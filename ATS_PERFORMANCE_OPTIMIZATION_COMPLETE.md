# ATS System - Complete Performance Optimization Strategy

**Date**: April 11, 2026  
**Status**: Ready for Implementation

---

## Executive Summary

This document provides a complete optimization roadmap for the ATS system addressing:
1. Slow database queries (43-66 seconds → target: <2 seconds)
2. N+1 query problems
3. Heavy serializers and unnecessary data
4. Async processing for blocking operations
5. Caching strategy (Redis)
6. Frontend optimization
7. Authentication performance

---

## Part 1: Database & Query Optimization

### 1.1 Current Issues & Solutions

#### Problem: N+1 Queries in Job Listings
**Impact**: `GET /api/jobs/` takes 44-66 seconds

**Root Causes**:
- JobDescriptionSerializer calls `JobSkill.objects.filter(job=obj)` for each job
- `.count()` called per job for applicant count
- Missing `.select_related()` and `.prefetch_related()`

**Solution**:
```python
# GOOD - Use prefetch_related with Prefetch for annotations
from django.db.models import Prefetch, Count, Q

jobs = JobDescription.objects.filter(
    is_active=True,
    organization=organization
).annotate(
    applicant_count=Count('applications', filter=Q(applications__status='applied'))
).prefetch_related(
    Prefetch('jobskill_set', queryset=JobSkill.objects.only('id', 'skill'))
).select_related('organization', 'posted_by').only(
    'id', 'title', 'description', 'location', 'salary_min', 
    'salary_max', 'min_experience', 'created_at'
)[:50]  # Add pagination
```

#### Problem: Organization Resolution Too Many Queries
**Root Cause**: `get_user_organization()` called repeatedly in views

**Solution**:
```python
# Cache in request context
request._user_organization = None
request._user_organization_set = False

def get_cached_user_organization(request):
    if not hasattr(request, '_user_organization_set'):
        request._user_organization = None
        request._user_organization_set = True
    
    if not request._user_organization_set:
        user = getattr(request, 'user', None)
        if user and getattr(user, 'is_authenticated', False):
            try:
                request._user_organization = user.userprofile.organization
            except:
                request._user_organization = None
        request._user_organization_set = True
    
    return request._user_organization
```

### 1.2 Database Indexes

**Add these indexes** (in models.py or migration):
```python
class Meta:
    indexes = [
        # Organization indexes
        models.Index(fields=['slug'], name='org_slug_idx'),
        models.Index(fields=['is_active', 'created_at'], name='org_active_created_idx'),
        
        # Job indexes
        models.Index(fields=['organization', 'is_active'], name='job_org_active_idx'),
        models.Index(fields=['posted_by', 'is_active'], name='job_posted_active_idx'),
        models.Index(fields=['created_at'], name='job_created_idx'),
        
        # JobSkill indexes
        models.Index(fields=['job'], name='jobskill_job_idx'),
        models.Index(fields=['skill'], name='jobskill_skill_idx'),
        
        # JobApplication indexes
        models.Index(fields=['job', 'status'], name='jobapp_job_status_idx'),
        models.Index(fields=['candidate', 'status'], name='jobapp_cand_status_idx'),
        models.Index(fields=['created_at'], name='jobapp_created_idx'),
        
        # UserProfile indexes
        models.Index(fields=['user', 'organization'], name='userprof_user_org_idx'),
        models.Index(fields=['organization', 'role'], name='userprof_org_role_idx'),
    ]
```

---

## Part 2: Caching Strategy (Redis)

### 2.1 Redis Setup in settings.py

```python
# settings.py

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            },
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
        },
        'KEY_PREFIX': 'ats',
        'TIMEOUT': 300,  # 5 minutes default
    }
}

# Cache settings
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# Cache control headers
CACHE_MIDDLEWARE_SECONDS = 600
```

### 2.2 Cache Keys Strategy

```python
# core/cache_keys.py

class CacheKeys:
    # Organization
    ORG_BY_SLUG = 'org:slug:{slug}'
    ORG_SETTINGS = 'org:settings:{org_id}'
    ORG_DETAILS = 'org:details:{org_id}'
    
    # User
    USER_PROFILE = 'user:profile:{user_id}'
    USER_ORG = 'user:org:{user_id}'
    
    # Jobs
    JOB_DETAIL = 'job:detail:{job_id}'
    JOB_LIST_ORG = 'job:list:org:{org_id}'
    JOB_SKILLS = 'job:skills:{job_id}'
    
    # Candidates
    CANDIDATE_DETAIL = 'candidate:detail:{candidate_id}'
    
    # Session
    SESSION_USER = 'session:user:{session_id}'
    
    @staticmethod
    def get_org_key(slug):
        return CacheKeys.ORG_BY_SLUG.format(slug=slug)
    
    @staticmethod
    def get_user_org_key(user_id):
        return CacheKeys.USER_ORG.format(user_id=user_id)
```

### 2.3 Cache Decorators

```python
# core/decorators.py

from django.core.cache import cache
from functools import wraps
import hashlib
import json

def cached_result(timeout=300, key_builder=None):
    """Decorator to cache function results"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Build cache key
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                # Default: hash function args
                key_data = f"{func.__module__}.{func.__name__}:{str(args)}:{str(kwargs)}"
                cache_key = hashlib.md5(key_data.encode()).hexdigest()
            
            # Check cache
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # Compute and cache
            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout)
            return result
        
        return wrapper
    return decorator

def invalidate_cache(*keys):
    """Invalidate specific cache keys"""
    for key in keys:
        cache.delete(key)
```

---

## Part 3: Celery - Async Task Processing

### 3.1 Celery Configuration (ats_backend/celery.py)

```python
import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ats_backend.settings')

app = Celery('ats_backend')

# Load config from Django settings, namespace='CELERY'
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from all apps
app.autodiscover_tasks()

# Celery Beat Schedule
app.conf.beat_schedule = {
    'clean-expired-invites': {
        'task': 'authentication.tasks.clean_expired_invites',
        'schedule': crontab(hour=2, minute=0),  # 2 AM daily
    },
    'send-pending-emails': {
        'task': 'core.tasks.send_pending_emails',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes
    },
}

# Celery Configuration
app.conf.update(
    CELERY_BROKER_URL=os.getenv('CELERY_BROKER_URL', 'redis://127.0.0.1:6379/0'),
    CELERY_RESULT_BACKEND=os.getenv('CELERY_RESULT_BACKEND', 'redis://127.0.0.1:6379/0'),
    CELERY_ACCEPT_CONTENT=['json'],
    CELERY_TASK_SERIALIZER='json',
    CELERY_RESULT_SERIALIZER='json',
    CELERY_TIMEZONE='UTC',
    CELERY_TASK_TRACK_STARTED=True,
    CELERY_TASK_TIME_LIMIT=30 * 60,  # 30 minutes
    CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP=True,
)

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
```

### 3.2 Email Task (authentication/tasks.py)

```python
from celery import shared_task
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.urls import reverse
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def send_organization_creation_email(self, admin_email, admin_password, org_name, org_slug):
    """Send organization creation credentials via email"""
    try:
        # Create login URL
        login_url = f"{os.getenv('FRONTEND_URL')}/login"
        
        context = {
            'admin_email': admin_email,
            'admin_password': admin_password,
            'organization_name': org_name,
            'login_url': login_url,
            'change_password_url': f"{os.getenv('FRONTEND_URL')}/settings/security",
        }
        
        # Render templates
        html_message = render_to_string('emails/org_creation.html', context)
        plain_message = render_to_string('emails/org_creation.txt', context)
        
        # Send email
        email = EmailMultiAlternatives(
            subject=f'Welcome to ATS - {org_name} Organization Created',
            body=plain_message,
            from_email=os.getenv('DEFAULT_FROM_EMAIL', 'noreply@ats.com'),
            to=[admin_email],
        )
        email.attach_alternative(html_message, "text/html")
        email.send(fail_silently=False)
        
        logger.info(f"Organization creation email sent to {admin_email}")
        
    except Exception as exc:
        logger.error(f"Failed to send org creation email: {str(exc)}")
        # Retry with exponential backoff
        self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))

@shared_task(bind=True, max_retries=3)
def send_recruiter_invite_email(self, invite_token, recruiter_email, org_name, invited_by_name):
    """Send recruiter invitation email"""
    try:
        invite_url = f"{os.getenv('FRONTEND_URL')}/invites/accept?token={invite_token}"
        
        context = {
            'recruiter_email': recruiter_email,
            'organization_name': org_name,
            'invited_by': invited_by_name,
            'invite_url': invite_url,
            'expiry_days': 7,
        }
        
        html_message = render_to_string('emails/recruiter_invite.html', context)
        plain_message = render_to_string('emails/recruiter_invite.txt', context)
        
        email = EmailMultiAlternatives(
            subject=f'Join {org_name} on ATS',
            body=plain_message,
            from_email=os.getenv('DEFAULT_FROM_EMAIL', 'noreply@ats.com'),
            to=[recruiter_email],
        )
        email.attach_alternative(html_message, "text/html")
        email.send(fail_silently=False)
        
        logger.info(f"Recruiter invite email sent to {recruiter_email}")
        
    except Exception as exc:
        logger.error(f"Failed to send recruiter invite email: {str(exc)}")
        self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))

@shared_task
def clean_expired_invites():
    """Clean up expired organization invites"""
    from authentication.models import OrganizationInvite
    from django.utils import timezone
    
    expiredCount = OrganizationInvite.objects.filter(
        status=OrganizationInvite.Status.PENDING,
        expires_at__lt=timezone.now()
    ).update(status=OrganizationInvite.Status.EXPIRED)
    
    logger.info(f"Cleaned up {expiredCount} expired invites")
```

---

## Part 4: Frontend Optimization (React)

### 4.1 API Call Batching & Request Deduplication

```javascript
// services/api.js

class APIClient {
  constructor() {
    this.requestCache = new Map();
    this.pendingRequests = new Map();
  }

  // Deduplicate identical requests within 5 seconds
  async request(method, url, config = {}) {
    const cacheKey = `${method}:${url}:${JSON.stringify(config.params || {})}`;
    
    // Return pending request if already in flight
    if (this.pendingRequests.has(cacheKey)) {
      return this.pendingRequests.get(cacheKey);
    }
    
    // Check cache for GET requests
    if (method === 'GET' && this.requestCache.has(cacheKey)) {
      const cached = this.requestCache.get(cacheKey);
      if (Date.now() - cached.timestamp < 60000) { // 1 minute
        return cached.data;
      }
    }
    
    // Make request
    const promise = axiosInstance({
      method,
      url,
      ...config,
    })
      .then(res => {
        if (method === 'GET') {
          this.requestCache.set(cacheKey, {
            data: res.data,
            timestamp: Date.now(),
          });
        }
        this.pendingRequests.delete(cacheKey);
        return res.data;
      })
      .catch(err => {
        this.pendingRequests.delete(cacheKey);
        throw err;
      });
    
    this.pendingRequests.set(cacheKey, promise);
    return promise;
  }

  clearCache() {
    this.requestCache.clear();
  }
}
```

### 4.2 Pagination with Lazy Loading

```javascript
// hooks/usePaginatedJobs.js

export function usePaginatedJobs(organizationSlug) {
  const [jobs, setJobs] = useState([]);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [loading, setLoading] = useState(false);

  const loadMore = useCallback(async () => {
    if (loading || !hasMore) return;
    
    setLoading(true);
    try {
      const response = await api.get('/jobs/', {
        params: {
          page,
          page_size: 20,
          organization_slug: organizationSlug,
          ordering: '-created_at',
        },
      });
      
      setJobs(prev => [...prev, ...response.results]);
      setHasMore(response.next !== null);
      setPage(page + 1);
    } finally {
      setLoading(false);
    }
  }, [page, loading, hasMore, organizationSlug]);

  useEffect(() => {
    loadMore();
  }, []);

  return { jobs, loading, hasMore, loadMore };
}
```

### 4.3 Reduce Unnecessary Re-renders

```javascript
// components/JobCard.jsx

const JobCard = React.memo(({ job, onSelect }) => {
  return (
    <div onClick={() => onSelect(job.id)} className="job-card">
      <h3>{job.title}</h3>
      <p>{job.location}</p>
    </div>
  );
}, (prevProps, nextProps) => {
  // Custom comparison - only re-render if job ID changes
  return prevProps.job.id === nextProps.job.id;
});

export default JobCard;
```

---

## Part 5: Authentication Performance

### 5.1 JWT Token Optimization

```python
# authentication/views.py

from rest_framework_simplejwt.tokens import RefreshToken

# Reduce token expiry to reduce validation overhead
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': settings.SECRET_KEY,
}

def login_user(request):
    """Optimized login with minimal query"""
    user = authenticate_user(request.data)
    
    # Prefetch related data
    user = User.objects.select_related('userprofile__organization').get(id=user.id)
    
    refresh = RefreshToken.for_user(user)
    
    # Add custom claims
    refresh['organization_id'] = user.userprofile.organization_id
    refresh['role'] = user.userprofile.role
    
    return Response({
        'access': str(refresh.access_token),
        'refresh': str(refresh),
        'user': {
            'id': user.id,
            'email': user.email,
            'role': user.userprofile.role,
            'organization_id': user.userprofile.organization_id,
        }
    })
```

### 5.2 Token Validation Caching

```python
# authentication/middleware.py

from django.core.cache import cache
from rest_framework_simplejwt.authentication import JWTAuthentication

class CachedJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        token = self.get_raw_token(self.get_header(request))
        
        if token is None:
            return None
        
        # Check cache first
        cache_key = f'jwt_validated:{token}'
        cached_user = cache.get(cache_key)
        
        if cached_user:
            return (cached_user, token)
        
        # Validate token
        validated_token = self.get_validated_token(token)
        user = self.get_user(validated_token)
        
        # Cache for 1 hour
        cache.set(cache_key, user, 3600)
        
        return (user, validated_token)
```

---

## Part 6: Pagination & Filtering

### 6.1 Standard Pagination

```python
# settings.py

REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
}

# core/pagination.py

class SmallPagination(pagination.PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class LargePagination(pagination.PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 200
```

### 6.2 Cursor Pagination for Large Datasets

```python
# core/pagination.py

class CreatedAtCursorPagination(pagination.CursorPagination):
    page_size = 50
    ordering = '-created_at'
    cursor_query_param = 'cursor'
```

---

## Part 7: Implementation Checklist

### Phase 1: Critical (Week 1)
- [ ] ✅ Enhance Organization model with registration fields
- [ ] Create database migrations
- [ ] Add database indexes
- [ ] Optimize JobDescription queries with prefetch_related
- [ ] Fix N+1 queries in organization functions

### Phase 2: Important (Week 2)
- [ ] Setup Redis caching
- [ ] Implement cache decorators
- [ ] Add pagination to all list endpoints
- [ ] Optimize serializers (only return needed fields)

### Phase 3: Enhancement (Week 3)
- [ ] Setup Celery for async email
- [ ] Implement JWT token caching
- [ ] Add request deduplication on frontend
- [ ] Implement lazy loading for jobs

### Phase 4: Monitoring (Week 4)
- [ ] Add performance monitoring with Django Silk
- [ ] Setup alerts for slow queries
- [ ] Monitor Redis cache hit rates
- [ ] Monitor Celery task failures

---

## Part 8: Expected Performance Improvements

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| GET /api/jobs/ | 44-66s | ~1.5s | **97% ⬇️** |
| GET /api/auth/recruiters/ | 43-45s | ~1s | **97% ⬇️** |
| Login response | ~800ms | ~300ms | **63% ⬇️** |
| Email sending | Blocking | Async | **Immediate** |
| Token validation | ~200ms | ~10ms (cached) | **95% ⬇️** |

---

## Part 9: Monitoring & Tools

### Django Debug Toolbar
```python
# settings.py

if DEBUG:
    INSTALLED_APPS.append('debug_toolbar')
    MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')
```

### Silk for API Profiling
```python
# settings.py
INSTALLED_APPS.append('silk')
MIDDLEWARE.insert(0, 'silk.middleware.SilkyMiddleware')

# urls.py
urlpatterns += [path('silk/', include('silk.urls', namespace='silk'))]
```

### New Relic or Sentry for Error Tracking
```python
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn=os.getenv('SENTRY_DSN'),
    integrations=[DjangoIntegration()],
    traces_sample_rate=0.1,
)
```

---

## Deployment Configuration

### Docker Compose with Redis & Celery

```yaml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

  celery:
    build: .
    command: celery -A ats_backend worker -l info --concurrency=4
    environment:
      CELERY_BROKER_URL: redis://redis:6379/0
      CELERY_RESULT_BACKEND: redis://redis:6379/0
    depends_on:
      - redis

  celery-beat:
    build: .
    command: celery -A ats_backend beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
    environment:
      CELERY_BROKER_URL: redis://redis:6379/0
      CELERY_RESULT_BACKEND: redis://redis:6379/0
    depends_on:
      - redis

  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: ats_db
      POSTGRES_USER: ats_user
      POSTGRES_PASSWORD: secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  web:
    build: .
    command: gunicorn ats_backend.wsgi:application --bind 0.0.0.0:8000 --workers 4
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis

volumes:
  postgres_data:
  redis_data:
```

---

## Conclusion

These optimizations address all major performance bottlenecks. Expected system response time should drop from 40-60 seconds to under 2 seconds for most operations.

**Next Step**: Start with Part 1 - Organize Model Enhancement
