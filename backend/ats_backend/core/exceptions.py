"""
Custom exception classes for ATS backend
"""

from rest_framework.exceptions import APIException


class ATSException(APIException):
    """Base exception class for ATS application"""
    default_detail = "An error occurred"
    default_code = "ats_error"


class ValidationError(ATSException):
    """Validation error for input data"""
    default_detail = "Invalid input data"
    default_code = "validation_error"
    status_code = 400


class AuthenticationError(ATSException):
    """Authentication related errors"""
    default_detail = "Authentication failed"
    default_code = "authentication_error"
    status_code = 401


class AuthorizationError(ATSException):
    """Authorization related errors"""
    default_detail = "Permission denied"
    default_code = "authorization_error"
    status_code = 403


class NotFoundError(ATSException):
    """Resource not found errors"""
    default_detail = "Resource not found"
    default_code = "not_found"
    status_code = 404


class ConflictError(ATSException):
    """Resource conflict errors (e.g., duplicate entries)"""
    default_detail = "Resource conflict"
    default_code = "conflict"
    status_code = 409


class ServiceUnavailableError(ATSException):
    """External service unavailable"""
    default_detail = "Service temporarily unavailable"
    default_code = "service_unavailable"
    status_code = 503


class FileUploadError(ATSException):
    """File upload related errors"""
    default_detail = "File upload failed"
    default_code = "file_upload_error"
    status_code = 400


class EmbeddingGenerationError(ATSException):
    """AI embedding generation errors"""
    default_detail = "Failed to generate embeddings"
    default_code = "embedding_error"
    status_code = 500