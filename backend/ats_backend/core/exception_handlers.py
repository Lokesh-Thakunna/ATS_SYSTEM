"""
Global exception handlers for Django REST Framework
"""

import logging
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

from .exceptions import ATSException

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom exception handler that provides detailed error responses
    and proper logging for different types of exceptions
    """

    # Get the standard DRF error response first
    response = exception_handler(exc, context)

    if response is not None:
        # DRF handled the exception, but we can enhance it
        if isinstance(exc, DjangoValidationError):
            response.data = {
                'error': 'Validation Error',
                'details': response.data
            }
        return response

    # Handle our custom exceptions
    if isinstance(exc, ATSException):
        logger.warning(f"ATS Exception: {exc.detail}", extra={
            'exception_type': type(exc).__name__,
            'status_code': exc.status_code,
            'user': getattr(context.get('request'), 'user', None),
            'view': context.get('view', {}).get('__class__', {}).get('__name__'),
        })

        return Response({
            'error': exc.default_detail,
            'code': exc.default_code,
            'details': exc.detail if hasattr(exc, 'detail') else None
        }, status=exc.status_code)

    # Handle Django database errors
    elif isinstance(exc, IntegrityError):
        logger.error(f"Database integrity error: {str(exc)}", extra={
            'exception_type': 'IntegrityError',
            'user': getattr(context.get('request'), 'user', None),
        })
        return Response({
            'error': 'Database constraint violation',
            'code': 'database_error'
        }, status=status.HTTP_400_BAD_REQUEST)

    # Handle unexpected errors
    else:
        view = context.get('view')
        if view:
            if hasattr(view, '__class__'):
                view_name = view.__class__.__name__
            else:
                view_name = getattr(view, '__name__', 'Unknown')
        else:
            view_name = 'Unknown'
        
        logger.error(f"Unexpected error: {str(exc)}", exc_info=True, extra={
            'exception_type': type(exc).__name__,
            'user': getattr(context.get('request'), 'user', None),
            'view': view_name,
        })
        return Response({
            'error': 'An unexpected error occurred',
            'code': 'internal_server_error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
