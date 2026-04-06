"""
Security middleware for additional protection and logging
"""

import logging
import time
from django.http import HttpResponseForbidden


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
