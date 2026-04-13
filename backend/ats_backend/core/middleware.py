"""
Enhanced security middleware for RBAC, tenant isolation, and comprehensive logging
"""

import logging
import time
from django.http import HttpResponseForbidden, JsonResponse
from django.urls import Resolver404, resolve
from django.utils.deprecation import MiddlewareMixin
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed
from django.conf import settings

from authentication.organization import (
    get_default_organization,
    get_organization_by_slug,
    get_user_organization,
)
from authentication.permissions import get_user_role, is_super_admin


logger = logging.getLogger(__name__)


class SecurityMiddleware:
    """
    Middleware for security enhancements and request logging
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Log incoming requests (excluding health checks for noise reduction)
        if not request.path.startswith('/health/'):
            self._log_request(request)

        # Check for suspicious patterns
        if self._is_suspicious_request(request):
            logger.warning(f"Suspicious request blocked: {request.META.get('REMOTE_ADDR')} - {request.path}")
            return HttpResponseForbidden("Request blocked")

        # Start timing
        start_time = time.time()

        response = self.get_response(request)

        # Add security headers
        response = self._add_security_headers(response)

        # Log response time for slow requests
        duration = time.time() - start_time
        if duration > 1.0:  # Log requests taking more than 1 second
            logger.warning(
                "Slow request detected: %s %s completed in %.2fs",
                request.method,
                request.path,
                duration,
            )

        return response

    def _log_request(self, request):
        """Log incoming request details"""
        user = getattr(request, 'user', None)
        user_id = user.id if user and user.is_authenticated else 'anonymous'

        logger.info(
            f"Request: {request.method} {request.path} - "
            f"User: {user_id} - "
            f"IP: {self._get_client_ip(request)} - "
            f"User-Agent: {request.META.get('HTTP_USER_AGENT', 'Unknown')[:100]}"
        )

    def _get_client_ip(self, request):
        """Get the real client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def _is_suspicious_request(self, request):
        """Check for potentially malicious request patterns"""
        # Check user agent for common attack patterns
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()

        suspicious_patterns = [
            'sqlmap',
            'nmap',
            'masscan',
            'dirbuster',
            'gobuster',
            'nikto',
            'acunetix',
            'openvas'
        ]

        for pattern in suspicious_patterns:
            if pattern in user_agent:
                return True

        # Check for SQL injection patterns in query parameters
        for key, value in request.GET.items():
            if isinstance(value, str):
                sql_patterns = ['union select', '1=1', 'or 1=1', 'script', 'javascript:']
                for pattern in sql_patterns:
                    if pattern in value.lower():
                        return True

        return False

    def _add_security_headers(self, response):
        """Add security headers to response"""
        # Prevent clickjacking
        response['X-Frame-Options'] = 'DENY'

        # Prevent MIME type sniffing
        response['X-Content-Type-Options'] = 'nosniff'

        # XSS protection
        response['X-XSS-Protection'] = '1; mode=block'

        # Referrer policy
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        # Content Security Policy (basic)
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'"
        )
        response['Content-Security-Policy'] = csp

        return response


class TenantRoutingMiddleware:
    """
    Resolve the effective organization and request context early so views can
    make consistent tenant-aware decisions from one place.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        tenant_context = self._build_tenant_context(request)
        request.tenant_context = tenant_context
        request.organization = tenant_context["organization"]
        request.organization_slug = tenant_context["organization_slug"]
        request.requested_organization_slug = tenant_context["requested_organization_slug"]
        request.request_job_id = tenant_context["job_id"]
        request.request_application_id = tenant_context["application_id"]
        return self.get_response(request)

    def _build_tenant_context(self, request):
        resolved_kwargs = {}
        try:
            resolved_kwargs = resolve(request.path_info).kwargs
        except Resolver404:
            resolved_kwargs = {}

        organization_slug = (
            request.GET.get("organization_slug")
            or request.GET.get("organization")
            or request.headers.get("X-Organization-Slug")
        )
        job_id = resolved_kwargs.get("job_id") or resolved_kwargs.get("id")
        application_id = resolved_kwargs.get("application_id")

        organization = None
        source = "default"

        if organization_slug:
            organization = get_organization_by_slug(organization_slug)
            source = "query"

        if organization is None and application_id:
            from jobs.models import JobApplication

            application = (
                JobApplication.objects
                .select_related("job__organization")
                .filter(id=application_id)
                .first()
            )
            if application:
                organization = application.job.organization
                job_id = job_id or application.job_id
                source = "application"

        if organization is None and job_id:
            from jobs.models import JobDescription

            job = JobDescription.objects.select_related("organization").filter(id=job_id).first()
            if job:
                organization = job.organization
                source = "job"

        if organization is None:
            user_organization = get_user_organization(getattr(request, "user", None))
            if user_organization is not None:
                organization = user_organization
                source = "user"

        if organization is None:
            organization = get_default_organization()

        return {
            "organization": organization,
            "organization_slug": getattr(organization, "slug", ""),
            "requested_organization_slug": organization_slug or "",
            "job_id": job_id,
            "application_id": application_id,
            "source": source,
        }


class RoleBasedAccessMiddleware(MiddlewareMixin):
    """
    Middleware to enforce role-based access control for API endpoints.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.jwt_auth = JWTAuthentication()
        
    def __call__(self, request):
        # Skip RBAC for public endpoints
        if self._is_public_endpoint(request.path):
            return self.get_response(request)
            
        # Only apply to API endpoints
        if not request.path.startswith('/api/v1/'):
            return self.get_response(request)
            
        try:
            user = self._authenticate_user(request)
            if not user:
                return self._unauthorized_response("Authentication required")
                
            role = get_user_role(user)
            if not role:
                return self._forbidden_response("Invalid user role")
                
            # Check role-based endpoint access
            if not self._has_endpoint_access(role, request.path, request.method):
                return self._forbidden_response("Insufficient permissions")
                
            # Set role and user in request for downstream use
            request.user = user
            request.user_role = role
            
        except Exception as e:
            logger.error(f"RBAC middleware error: {str(e)}")
            return self._server_error_response("Access control error")
            
        return self.get_response(request)
    
    def _is_public_endpoint(self, path):
        """Check if endpoint is public"""
        public_paths = [
            '/api/v1/auth/login/',
            '/api/v1/auth/register/',
            '/api/v1/auth/refresh/',
            '/api/v1/public/jobs/',
            '/health/',
        ]
        return any(path.startswith(public_path) for public_path in public_paths)
    
    def _authenticate_user(self, request):
        """Authenticate user from JWT token"""
        try:
            auth_result = self.jwt_auth.authenticate(request)
            if auth_result:
                user, token = auth_result
                return user
        except (InvalidToken, AuthenticationFailed):
            pass
        return None
    
    def _has_endpoint_access(self, role, path, method):
        """Check if role has access to specific endpoint"""
        
        # Define role-based access rules
        access_rules = {
            'SUPER_ADMIN': [
                '/api/v1/admin/',
                '/api/v1/organizations/',
                '/api/v1/users/',
                '/api/v1/system/',
            ],
            'ORG_ADMIN': [
                '/api/v1/org/',
                '/api/v1/team/',
                '/api/v1/settings/',
                '/api/v1/analytics/',
            ],
            'RECRUITER': [
                '/api/v1/recruiter/',
                '/api/v1/jobs/',
                '/api/v1/applications/',
                '/api/v1/candidates/',
                '/api/v1/matching/',
                '/api/v1/interviews/',
            ],
            'CANDIDATE': [
                '/api/v1/candidate/',
                '/api/v1/applications/',
                '/api/v1/profile/',
                '/api/v1/jobs/search/',
            ]
        }
        
        # Check if path matches any allowed pattern for role
        allowed_patterns = access_rules.get(role, [])
        
        for pattern in allowed_patterns:
            if path.startswith(pattern):
                # Additional method-based restrictions
                return self._check_method_access(role, pattern, method)
                
        return False
    
    def _check_method_access(self, role, pattern, method):
        """Check if role can use specific HTTP method on endpoint"""
        
        # Define method restrictions per role/endpoint type
        method_restrictions = {
            'CANDIDATE': {
                '/api/v1/candidate/': ['GET', 'POST', 'PUT', 'PATCH'],
                '/api/v1/applications/': ['GET', 'POST'],
                '/api/v1/profile/': ['GET', 'PUT', 'PATCH'],
                '/api/v1/jobs/search/': ['GET'],
            },
            'RECRUITER': {
                '/api/v1/jobs/': ['GET', 'POST', 'PUT', 'PATCH', 'DELETE'],
                '/api/v1/applications/': ['GET', 'PUT', 'PATCH'],
                '/api/v1/candidates/': ['GET'],
                '/api/v1/matching/': ['GET'],
                '/api/v1/interviews/': ['GET', 'POST', 'PUT', 'PATCH'],
            }
        }
        
        restrictions = method_restrictions.get(role, {})
        for endpoint_pattern, allowed_methods in restrictions.items():
            if pattern.startswith(endpoint_pattern):
                return method in allowed_methods
                
        # Default: allow all methods if not specifically restricted
        return True
    
    def _unauthorized_response(self, message):
        """Return 401 Unauthorized response"""
        return JsonResponse({
            'error': 'unauthorized',
            'message': message,
            'code': 'AUTH_001'
        }, status=401)
    
    def _forbidden_response(self, message):
        """Return 403 Forbidden response"""
        return JsonResponse({
            'error': 'forbidden',
            'message': message,
            'code': 'AUTH_002'
        }, status=403)
    
    def _server_error_response(self, message):
        """Return 500 Server Error response"""
        return JsonResponse({
            'error': 'server_error',
            'message': message,
            'code': 'AUTH_003'
        }, status=500)


class TenantIsolationMiddleware(MiddlewareMixin):
    """
    Middleware to enforce tenant data isolation by setting organization context
    for all database queries based on user's organization.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.jwt_auth = JWTAuthentication()
        
    def __call__(self, request):
        # Skip tenant isolation for public endpoints
        if self._is_public_endpoint(request.path):
            return self.get_response(request)
            
        try:
            # Authenticate user and set organization context
            user = self._authenticate_user(request)
            if user and not self._is_super_admin(user):
                organization = get_user_organization(user)
                if organization:
                    # Set organization context for database queries
                    request.organization_id = str(organization.id)
                    request.organization = organization
                    
                    # Set PostgreSQL session variable for Row Level Security
                    self._set_database_context(organization.id)
                    
        except Exception as e:
            logger.error(f"Tenant isolation middleware error: {str(e)}")
            
        response = self.get_response(request)
        
        # Clean up database context
        self._clear_database_context()
        
        return response
    
    def _is_public_endpoint(self, path):
        """Check if endpoint is public (no authentication required)"""
        public_paths = [
            '/api/auth/login/',
            '/api/auth/register/',
            '/api/auth/refresh/',
            '/api/public/',
            '/health/',
            '/admin/login/',
            '/static/',
            '/media/',
        ]
        # Also skip tenant isolation for SuperAdmin endpoints
        superadmin_paths = [
            '/api/auth/admin/',
        ]
        return any(path.startswith(public_path) for public_path in public_paths) or \
               any(path.startswith(superadmin_path) for superadmin_path in superadmin_paths)
    
    def _authenticate_user(self, request):
        """Authenticate user from JWT token"""
        try:
            auth_result = self.jwt_auth.authenticate(request)
            if auth_result:
                user, token = auth_result
                request.user = user
                return user
        except (InvalidToken, AuthenticationFailed):
            pass
        return None
    
    def _is_super_admin(self, user):
        """Check if user is super admin"""
        return is_super_admin(user)
    
    def _set_database_context(self, organization_id):
        """Set PostgreSQL session variable for Row Level Security"""
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute(f"SET app.current_organization_id = '{organization_id}'")
    
    def _clear_database_context(self):
        """Clear PostgreSQL session variable"""
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("RESET app.current_organization_id")
