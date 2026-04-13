# Multi-Tenant ATS System Architecture

## Overview

This document outlines the complete multi-tenant architecture for the SaaS-level Applicant Tracking System (ATS) with strict data isolation and role-based access control.

## System Architecture

### Multi-Tenant Hierarchy

```
SuperAdmin (Platform Level)
├── Creates and manages organizations
├── Assigns organization admins
├── Platform-wide analytics
└── System health monitoring

Organization (Tenant Level)
├── Organization Admin
│   ├── Manages team members (recruiters)
│   ├── Configures organization settings
│   ├── Branding and customization
│   └── Organization analytics
├── Recruiters
│   ├── Create and manage job postings
│   ├── Review applications
│   ├── Schedule interviews
│   └── Send offers
└── Data (Isolated by organization_id)
    ├── Jobs
    ├── Applications
    ├── Candidates
    └── Analytics

Public (Cross-Tenant)
├── Job Board (Aggregated from all organizations)
├── Candidate Registration
└── Job Applications
```

## Data Isolation Strategy

### 1. Database Schema with organization_id

All tenant-specific tables include `organization_id` for data scoping:

**Core Tables:**
- `organizations` - Tenant information
- `users` - User accounts with role and organization_id
- `jobs` - Job postings (scoped to organization)
- `applications` - Job applications (scoped to organization)
- `candidates` - Candidate profiles (scoped to organization)
- `interviews` - Interview schedules (scoped to organization)
- `offers` - Job offers (scoped to organization)

### 2. Role-Based Access Control (RBAC)

**User Roles:**
- `SUPER_ADMIN` - Platform-level access
- `ORG_ADMIN` - Organization-level access
- `RECRUITER` - Job and application management
- `CANDIDATE` - Job seeking and applications

**Permission Matrix:**
```
Resource/Action         | SUPER_ADMIN | ORG_ADMIN | RECRUITER | CANDIDATE
------------------------|-------------|-----------|-----------|----------
Create Organization      | ✓           | ✗         | ✗         | ✗
Manage Organizations     | ✓           | ✗         | ✗         | ✗
View Platform Analytics  | ✓           | ✗         | ✗         | ✗
Manage Org Users         | ✗           | ✓         | ✗         | ✗
Manage Org Settings      | ✗           | ✓         | ✗         | ✗
Create Jobs              | ✗           | ✗         | ✓         | ✗
Manage Applications      | ✗           | ✗         | ✓         | ✗
View Jobs (All Orgs)     | ✗           | ✗         | ✗         | ✓
Apply to Jobs            | ✗           | ✗         | ✗         | ✓
```

## Security Architecture

### 1. Authentication Flow

```
1. User Login → JWT Token Generation
2. Token includes: user_id, role, organization_id
3. Middleware validates token on each request
4. Data access filtered by organization_id (except SUPER_ADMIN)
```

### 2. Data Access Patterns

**Middleware Implementation:**
```python
# Django middleware example
class TenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        if request.user and request.user.role != 'SUPER_ADMIN':
            # Filter queries by organization_id
            request.organization_id = request.user.organization_id
        return self.get_response(request)
```

**Query Filtering:**
```python
# Base queryset filtering
class TenantAwareManager(models.Manager):
    def get_queryset(self):
        qs = super().get_queryset()
        if hasattr(self.instance, 'organization_id'):
            return qs.filter(organization_id=self.instance.organization_id)
        return qs
```

## API Architecture

### 1. Endpoint Structure

```
/api/v1/
├── auth/
│   ├── login/
│   ├── logout/
│   ├── register/
│   └── refresh/
├── admin/ (SUPER_ADMIN only)
│   ├── organizations/
│   ├── platform-analytics/
│   └── system-health/
├── org/ (ORG_ADMIN only)
│   ├── settings/
│   ├── team/
│   └── analytics/
├── recruiter/ (RECRUITER only)
│   ├── jobs/
│   ├── applications/
│   ├── candidates/
│   └── interviews/
├── candidate/ (CANDIDATE only)
│   ├── profile/
│   ├── applications/
│   └── saved-jobs/
└── public/
    ├── jobs/
    ├── organizations/
    └── register/
```

### 2. Response Format

```json
{
  "success": true,
  "data": {},
  "message": "Operation successful",
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 100
  },
  "timestamp": "2026-04-11T11:26:00Z"
}
```

## Frontend Architecture

### 1. Component Structure

```
src/
├── components/
│   ├── common/
│   │   ├── Layout/
│   │   ├── Navigation/
│   │   ├── Cards/
│   │   └── Forms/
│   ├── auth/
│   ├── admin/
│   ├── organization/
│   ├── recruiter/
│   └── candidate/
├── pages/
│   ├── AdminDashboard/
│   ├── OrganizationDashboard/
│   ├── RecruiterDashboard/
│   ├── CandidateDashboard/
│   └── PublicJobBoard/
├── hooks/
│   ├── useAuth.js
│   ├── useTenant.js
│   └── usePermissions.js
├── services/
│   ├── api.js
│   ├── auth.js
│   └── tenant.js
└── utils/
    ├── permissions.js
    ├── constants.js
    └── helpers.js
```

### 2. Route Protection

```javascript
// Route guard implementation
const ProtectedRoute = ({ role, children }) => {
  const { user, loading } = useAuth();
  
  if (loading) return <LoadingSpinner />;
  
  if (!user || user.role !== role) {
    return <Navigate to="/unauthorized" />;
  }
  
  return children;
};
```

## Database Schema

### Core Tables

```sql
-- Organizations (Tenants)
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    website VARCHAR(500),
    industry VARCHAR(100),
    company_size VARCHAR(50),
    description TEXT,
    logo_url VARCHAR(500),
    primary_color VARCHAR(7) DEFAULT '#4f46e5',
    settings JSONB DEFAULT '{}',
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Users with Roles
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    role VARCHAR(20) NOT NULL CHECK (role IN ('SUPER_ADMIN', 'ORG_ADMIN', 'RECRUITER', 'CANDIDATE')),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    is_active BOOLEAN DEFAULT true,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Jobs (Tenant-scoped)
CREATE TABLE jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    job_type VARCHAR(50) NOT NULL,
    location VARCHAR(255),
    salary_min DECIMAL(10,2),
    salary_max DECIMAL(10,2),
    required_skills TEXT[],
    experience_required INTEGER,
    status VARCHAR(20) DEFAULT 'active',
    posted_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Applications (Tenant-scoped)
CREATE TABLE applications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
    candidate_id UUID REFERENCES users(id) ON DELETE CASCADE,
    resume_url VARCHAR(500),
    cover_letter TEXT,
    status VARCHAR(20) DEFAULT 'applied',
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    notes TEXT,
    applied_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

## Deployment Architecture

### 1. Infrastructure Components

```
Load Balancer
├── Frontend (React/Vite) - CDN
├── Backend API (Django/DRF)
│   ├── Application Servers
│   ├── Redis Cache
│   └── Celery Workers
├── Database (PostgreSQL + pgvector)
├── File Storage (Supabase/S3)
└── Email Service (SendGrid/SES)
```

### 2. Environment Configuration

**Development:**
- Local PostgreSQL with pgvector
- Redis for caching
- Local file storage
- SMTP for emails

**Production:**
- Managed PostgreSQL (RDS/CloudSQL)
- Redis Cluster
- S3/Supabase for file storage
- SendGrid/SES for emails
- CDN for static assets

## Monitoring & Analytics

### 1. System Health Monitoring

- API response times
- Database performance
- Email delivery rates
- File storage usage
- User activity metrics

### 2. Business Analytics

- Organization growth metrics
- Job posting statistics
- Application conversion rates
- Time-to-hire metrics
- Revenue tracking

## Security Considerations

### 1. Data Privacy

- GDPR compliance
- Data encryption at rest and in transit
- Regular security audits
- Data retention policies

### 2. Access Control

- Multi-factor authentication
- Session management
- API rate limiting
- Input validation and sanitization

## Scalability Planning

### 1. Horizontal Scaling

- Stateless application servers
- Database read replicas
- CDN for static content
- Load balancing

### 2. Performance Optimization

- Database indexing
- Caching strategies
- Lazy loading
- Pagination

This architecture ensures complete data isolation between tenants while providing a scalable, secure, and maintainable SaaS platform.
