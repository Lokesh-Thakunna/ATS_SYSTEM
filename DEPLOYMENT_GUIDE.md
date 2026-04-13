# 🚀 ATS Platform Deployment Guide

**Version**: 1.0  
**Date**: April 11, 2026  
**Status**: Production Ready

---

## 📋 Prerequisites

### System Requirements
- **Python**: 3.9+
- **Node.js**: 16+
- **PostgreSQL**: 13+ with pgvector extension
- **Redis**: 6+
- **Nginx**: 1.18+ (for production)
- **Docker**: 20+ (optional)

### Environment Setup
```bash
# Clone repository
git clone <repository-url>
cd ats_project

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Frontend setup
cd ../ats-frontend
npm install
```

---

## 🗄️ Database Setup

### PostgreSQL Configuration
```sql
-- Create database
CREATE DATABASE ats_platform;

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create user (optional)
CREATE USER ats_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE ats_platform TO ats_user;
```

### Run Database Migrations
```bash
cd backend
python manage.py makemigrations
python manage.py migrate
```

### Load Initial Data
```bash
# Create super admin
python manage.py createsuperuser

# Load skill aliases and initial data
python manage.py loaddata initial_data.json
```

---

## ⚙️ Environment Configuration

### Backend Environment (.env)
```bash
# Database Configuration
DB_NAME=ats_platform
DB_USER=ats_user
DB_PASSWORD=your_secure_password
DB_HOST=localhost
DB_PORT=5432

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password
REDIS_DB=0

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
DEFAULT_FROM_NAME=ATS Platform

# JWT Configuration
SECRET_KEY=your_very_long_secret_key_here
JWT_SECRET_KEY=your_jwt_secret_key
JWT_ACCESS_TOKEN_LIFETIME=60
JWT_REFRESH_TOKEN_LIFETIME=1440

# File Storage
MEDIA_ROOT=/path/to/media/files
MAX_UPLOAD_SIZE=10485760  # 10MB

# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### Frontend Environment (.env)
```bash
# API Configuration
REACT_APP_API_URL=http://localhost:8000/api/v1
REACT_APP_ENVIRONMENT=development

# Upload Configuration
REACT_APP_MAX_FILE_SIZE=10485760
REACT_APP_ALLOWED_FILE_TYPES=pdf,doc,docx

# Feature Flags
REACT_APP_ENABLE_AI_MATCHING=true
REACT_APP_ENABLE_RESUME_PARSING=true
```

---

## 🚀 Development Setup

### Start Backend Services
```bash
# Terminal 1: Django Development Server
cd backend
python manage.py runserver 0.0.0.0:8000

# Terminal 2: Celery Worker
cd backend
celery -A ats_backend worker --loglevel=info

# Terminal 3: Celery Beat (Scheduler)
cd backend
celery -A ats_backend beat --loglevel=info

# Terminal 4: Redis Server
redis-server
```

### Start Frontend
```bash
cd ats-frontend
npm start
```

### Access Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000/api/v1
- **Admin Panel**: http://localhost:8000/admin
- **API Documentation**: http://localhost:8000/api/docs

---

## 🐳 Docker Deployment (Recommended)

### Docker Compose Setup
```yaml
# docker-compose.yml
version: '3.8'

services:
  db:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: ats_platform
      POSTGRES_USER: ats_user
      POSTGRES_PASSWORD: your_secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  backend:
    build: ./backend
    environment:
      - DB_HOST=db
      - REDIS_HOST=redis
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis
    volumes:
      - ./backend:/app
      - media_files:/app/media

  frontend:
    build: ./ats-frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend
    volumes:
      - ./ats-frontend:/app

  celery:
    build: ./backend
    command: celery -A ats_backend worker --loglevel=info
    environment:
      - DB_HOST=db
      - REDIS_HOST=redis
    depends_on:
      - db
      - redis
    volumes:
      - ./backend:/app

volumes:
  postgres_data:
  redis_data:
  media_files:
```

### Docker Commands
```bash
# Build and start all services
docker-compose up --build

# Start in background
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down

# Clean up volumes
docker-compose down -v
```

---

## 🌐 Production Deployment

### Nginx Configuration
```nginx
# /etc/nginx/sites-available/ats-platform
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;
    
    # SSL Configuration
    ssl_certificate /path/to/your/certificate.crt;
    ssl_certificate_key /path/to/your/private.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;
    
    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # Frontend
    location / {
        root /var/www/ats-frontend/build;
        try_files $uri $uri/ /index.html;
    }
    
    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Media Files
    location /media/ {
        alias /var/www/ats-backend/media/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Static Files
    location /static/ {
        alias /var/www/ats-backend/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

### Production Commands
```bash
# Backend Setup
cd backend
python manage.py collectstatic --noinput
python manage.py migrate
python manage.py check --deploy

# Frontend Build
cd ../ats-frontend
npm run build

# Start Production Services
# Using Gunicorn for backend
gunicorn ats_backend.wsgi:application \
    --bind 127.0.0.1:8000 \
    --workers 4 \
    --worker-class gevent \
    --max-requests 1000 \
    --max-requests-jitter 50 \
    --timeout 30 \
    --keep-alive 2 \
    --log-level info

# Start Celery workers
celery -A ats_backend worker \
    --loglevel=info \
    --concurrency=4 \
    --max-tasks-per-child=1000

# Start Celery beat
celery -A ats_backend beat \
    --loglevel=info \
    --schedule=/tmp/celerybeat-schedule
```

---

## 🔒 Security Configuration

### SSL Certificate Setup
```bash
# Using Let's Encrypt (Recommended)
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### Firewall Configuration
```bash
# UFW Setup
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw enable

# IPTables (Alternative)
sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT
sudo iptables -A INPUT -j DROP
```

---

## 📊 Monitoring & Logging

### Application Monitoring
```bash
# Setup monitoring
pip install django-debug-toolbar
pip install sentry-sdk

# Add to settings.py
INSTALLED_APPS += ['debug_toolbar']
MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']

# Sentry for error tracking
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn="your-sentry-dsn",
    integrations=[DjangoIntegration()],
    traces_sample_rate=1.0,
)
```

### Log Configuration
```python
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/var/log/ats/app.log',
            'formatter': 'verbose',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': '/var/log/ats/error.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'error_file'],
            'level': 'INFO',
            'propagate': True,
        },
        'ats_backend': {
            'handlers': ['file', 'error_file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

---

## 🔄 Backup Strategy

### Database Backup
```bash
# Automated backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/ats"
DB_NAME="ats_platform"

# Create backup
pg_dump -h localhost -U ats_user -d $DB_NAME > $BACKUP_DIR/backup_$DATE.sql

# Compress
gzip $BACKUP_DIR/backup_$DATE.sql

# Keep last 7 days
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +7 -delete
```

### Media Files Backup
```bash
# Sync media files to backup location
rsync -av /var/www/ats-backend/media/ /backup/ats/media/

# Or use cloud storage
aws s3 sync /var/www/ats-backend/media/ s3://your-backup-bucket/media/
```

---

## 🧪 Testing

### Run Tests
```bash
# Backend tests
cd backend
python manage.py test

# Coverage report
coverage run --source='.' manage.py test
coverage report
coverage html

# Frontend tests
cd ../ats-frontend
npm test
npm run test:coverage
```

### Load Testing
```bash
# Install Locust
pip install locust

# Create load test
# locustfile.py
from locust import HttpUser, task, between

class ATSUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def view_jobs(self):
        self.client.get("/api/v1/public/jobs/")
    
    @task
    def login(self):
        self.client.post("/api/v1/auth/login/", json={
            "email": "test@example.com",
            "password": "testpassword"
        })

# Run load test
locust -f locustfile.py --host=http://localhost:8000 -u 100 -r 10 -t 60s
```

---

## 📈 Performance Optimization

### Database Optimization
```sql
-- Create indexes for better performance
CREATE INDEX CONCURRENTLY idx_jobs_org_status ON jobs(organization_id, status);
CREATE INDEX CONCURRENTLY idx_applications_job_status ON applications(job_id, status);
CREATE INDEX CONCURRENTLY idx_match_scores_job_score ON match_scores(job_id, total_score DESC);

-- Analyze tables for query planner
ANALYZE jobs;
ANALYZE applications;
ANALYZE match_scores;
```

### Redis Configuration
```bash
# Redis optimization
echo "maxmemory 2gb" >> /etc/redis/redis.conf
echo "maxmemory-policy allkeys-lru" >> /etc/redis/redis.conf
echo "save 900 1" >> /etc/redis/redis.conf
echo "save 300 10" >> /etc/redis/redis.conf
echo "save 60 10000" >> /etc/redis/redis.conf
```

---

## 🚨 Troubleshooting

### Common Issues

#### Database Connection
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Check connection
psql -h localhost -U ats_user -d ats_platform

# Reset password
ALTER USER ats_user WITH PASSWORD 'new_password';
```

#### Redis Connection
```bash
# Check Redis status
redis-cli ping

# Check memory usage
redis-cli info memory
```

#### Celery Issues
```bash
# Check worker status
celery -A ats_backend inspect active

# Clear queue
celery -A ats_backend purge

# Restart workers
pkill -f celery
celery -A ats_backend worker --loglevel=info
```

### Health Checks
```bash
# Application health
curl http://localhost:8000/health/

# Database health
python manage.py dbshell --command="SELECT 1;"

# Redis health
redis-cli ping
```

---

## 📞 Support & Maintenance

### Regular Maintenance Tasks
```bash
# Weekly tasks
0 2 * * 1 /usr/bin/python manage.py cleanup_old_sessions
0 3 * * 1 /usr/bin/python manage.py cleanup_cache
0 4 * * 1 /usr/bin/python manage.py backup_database

# Monthly tasks
0 5 1 * * /usr/bin/python manage.py update_skill_aliases
0 6 1 * * /usr/bin/python manage.py generate_analytics_report
```

### Monitoring Dashboard
- **System Metrics**: http://yourdomain.com/admin/system/metrics/
- **Error Logs**: http://yourdomain.com/admin/system/logs/
- **Performance**: http://yourdomain.com/api/v1/system/performance/

---

## 🎯 Production Checklist

### Pre-Deployment Checklist
- [ ] Environment variables configured
- [ ] Database migrations applied
- [ ] SSL certificates installed
- [ ] Firewall configured
- [ ] Backup strategy implemented
- [ ] Monitoring tools installed
- [ ] Load testing completed
- [ ] Security audit performed
- [ ] Documentation updated

### Post-Deployment Checklist
- [ ] All services running
- [ ] Health checks passing
- [ ] Monitoring alerts configured
- [ ] Log rotation setup
- [ ] Performance benchmarks recorded
- [ ] User acceptance testing completed

---

## 🆘 Emergency Procedures

### Database Recovery
```bash
# Restore from backup
psql -h localhost -U ats_user -d ats_platform < backup_20240411.sql

# Point-in-time recovery (if using WAL)
pg_basebackup -h localhost -D /backup/base -U ats_user -v -P
```

### Service Restart
```bash
# Restart all services
sudo systemctl restart nginx
sudo systemctl restart postgresql
sudo systemctl restart redis
sudo systemctl restart gunicorn
sudo systemctl restart celery

# Check status
sudo systemctl status nginx postgresql redis gunicorn celery
```

---

**🎉 Your ATS Platform is now ready for production deployment!**

For support and updates, visit: https://github.com/your-repo/issues
