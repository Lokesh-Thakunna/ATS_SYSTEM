"""
Enhanced core models for audit trail, email logging, and system monitoring
"""

import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.conf import settings

User = get_user_model()


class EmailLog(models.Model):
    """Email sending log for audit trail"""
    
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        SENT = 'sent', 'Sent'
        FAILED = 'failed', 'Failed'
        BOUNCED = 'bounced', 'Bounced'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    to_email = models.EmailField(db_index=True)
    subject = models.CharField(max_length=255)
    template_name = models.CharField(max_length=100, blank=True)
    from_email = models.EmailField(blank=True)
    from_name = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    message_id = models.CharField(max_length=255, blank=True, db_index=True)
    error_message = models.TextField(blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Organization context
    organization_id = models.UUIDField(null=True, blank=True, db_index=True)
    
    # Email content (for debugging)
    content_preview = models.TextField(blank=True)
    attachments_count = models.PositiveSmallIntegerField(default=0)
    
    class Meta:
        db_table = 'email_logs'
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['to_email', 'status']),
            models.Index(fields=['organization_id', 'status']),
        ]
    
    def __str__(self):
        return f"Email to {self.to_email}: {self.status}"


class EmailQueue(models.Model):
    """Email queue for bulk sending"""
    
    class Priority(models.TextChoices):
        LOW = 'low', 'Low'
        NORMAL = 'normal', 'Normal'
        HIGH = 'high', 'High'
        URGENT = 'urgent', 'Urgent'
    
    class Status(models.TextChoices):
        QUEUED = 'queued', 'Queued'
        PROCESSING = 'processing', 'Processing'
        SENT = 'sent', 'Sent'
        FAILED = 'failed', 'Failed'
        RETRY = 'retry', 'Retry'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    to_email = models.EmailField(db_index=True)
    subject = models.CharField(max_length=255)
    template_name = models.CharField(max_length=100, blank=True)
    context = models.JSONField(default=dict)
    html_content = models.TextField(blank=True)
    text_content = models.TextField(blank=True)
    from_email = models.EmailField(blank=True)
    from_name = models.CharField(max_length=255, blank=True)
    priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.NORMAL)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.QUEUED)
    
    # Retry logic
    retry_count = models.PositiveSmallIntegerField(default=0)
    max_retries = models.PositiveSmallIntegerField(default=3)
    next_retry_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    
    # Organization context
    organization_id = models.UUIDField(null=True, blank=True, db_index=True)
    
    # Attachments
    attachments = models.JSONField(default=list)
    attachments_count = models.PositiveSmallIntegerField(default=0)
    
    # Error handling
    error_message = models.TextField(blank=True)
    
    class Meta:
        db_table = 'email_queue'
        indexes = [
            models.Index(fields=['status', 'priority', 'created_at']),
            models.Index(fields=['to_email', 'status']),
            models.Index(fields=['next_retry_at']),
            models.Index(fields=['organization_id', 'status']),
        ]
    
    def __str__(self):
        return f"Queued Email to {self.to_email}: {self.status}"


class SystemMetrics(models.Model):
    """System performance and usage metrics"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    metric_name = models.CharField(max_length=100, db_index=True)
    metric_value = models.JSONField(default=dict)
    metric_type = models.CharField(max_length=50)  # counter, gauge, histogram
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    # Organization context (optional)
    organization_id = models.UUIDField(null=True, blank=True, db_index=True)
    
    # Metadata
    tags = models.JSONField(default=list)
    source = models.CharField(max_length=100, blank=True)
    
    class Meta:
        db_table = 'system_metrics'
        indexes = [
            models.Index(fields=['metric_name', 'timestamp']),
            models.Index(fields=['metric_type', 'timestamp']),
            models.Index(fields=['organization_id', 'metric_name', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.metric_name}: {self.metric_type}"


class AuditLog(models.Model):
    """Comprehensive audit log for all system actions"""
    
    class Action(models.TextChoices):
        CREATE = 'create', 'Create'
        UPDATE = 'update', 'Update'
        DELETE = 'delete', 'Delete'
        LOGIN = 'login', 'Login'
        LOGOUT = 'logout', 'Logout'
        VIEW = 'view', 'View'
        EXPORT = 'export', 'Export'
        IMPORT = 'import', 'Import'
        SEND_EMAIL = 'send_email', 'Send Email'
        FILE_UPLOAD = 'file_upload', 'File Upload'
        FILE_DOWNLOAD = 'file_download', 'File Download'
    
    class Resource(models.TextChoices):
        USER = 'user', 'User'
        ORGANIZATION = 'organization', 'Organization'
        JOB = 'job', 'Job'
        APPLICATION = 'application', 'Application'
        RESUME = 'resume', 'Resume'
        INTERVIEW = 'interview', 'Interview'
        OFFER = 'offer', 'Offer'
        CANDIDATE = 'candidate', 'Candidate'
        TEAM = 'team', 'Team'
        SYSTEM = 'system', 'System'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs')
    action = models.CharField(max_length=20, choices=Action.choices, db_index=True)
    resource_type = models.CharField(max_length=20, choices=Resource.choices, db_index=True)
    resource_id = models.UUIDField(null=True, blank=True, db_index=True)
    resource_name = models.CharField(max_length=255, blank=True)
    
    # Change tracking
    old_values = models.JSONField(default=dict, blank=True)
    new_values = models.JSONField(default=dict, blank=True)
    changed_fields = models.JSONField(default=list, blank=True)
    
    # Request context
    ip_address = models.GenericIPAddressField(null=True, blank=True, db_index=True)
    user_agent = models.TextField(blank=True)
    request_method = models.CharField(max_length=10, blank=True)
    request_path = models.CharField(max_length=500, blank=True)
    
    # Organization context
    organization_id = models.UUIDField(null=True, blank=True, db_index=True)
    
    # Metadata
    session_id = models.CharField(max_length=255, blank=True, db_index=True)
    correlation_id = models.UUIDField(null=True, blank=True, db_index=True)
    
    # Timestamps
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'audit_logs'
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
            models.Index(fields=['resource_type', 'resource_id', 'timestamp']),
            models.Index(fields=['organization_id', 'timestamp']),
            models.Index(fields=['ip_address', 'timestamp']),
            models.Index(fields=['session_id', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.user} {self.action} {self.resource_type}"


class ErrorLog(models.Model):
    """System error logging for monitoring"""
    
    class Level(models.TextChoices):
        DEBUG = 'debug', 'Debug'
        INFO = 'info', 'Info'
        WARNING = 'warning', 'Warning'
        ERROR = 'error', 'Error'
        CRITICAL = 'critical', 'Critical'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    level = models.CharField(max_length=20, choices=Level.choices, db_index=True)
    message = models.TextField()
    exception_type = models.CharField(max_length=255, blank=True, db_index=True)
    stack_trace = models.TextField(blank=True)
    
    # Request context
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='error_logs')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    request_path = models.CharField(max_length=500, blank=True)
    request_method = models.CharField(max_length=10, blank=True)
    
    # Organization context
    organization_id = models.UUIDField(null=True, blank=True, db_index=True)
    
    # System context
    module = models.CharField(max_length=100, blank=True, db_index=True)
    function_name = models.CharField(max_length=100, blank=True, db_index=True)
    line_number = models.PositiveIntegerField(null=True, blank=True)
    
    # Additional data
    extra_data = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'error_logs'
        indexes = [
            models.Index(fields=['level', 'timestamp']),
            models.Index(fields=['exception_type', 'timestamp']),
            models.Index(fields=['module', 'timestamp']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['organization_id', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.level}: {self.message[:50]}"


class SystemSettings(models.Model):
    """Dynamic system settings"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    key = models.CharField(max_length=255, unique=True, db_index=True)
    value = models.TextField()
    description = models.TextField(blank=True)
    data_type = models.CharField(max_length=50, default='string')  # string, integer, boolean, json
    is_public = models.BooleanField(default=False)  # Whether setting can be exposed in API
    
    # Organization-specific settings
    organization_id = models.UUIDField(null=True, blank=True, db_index=True)
    
    # Validation
    validation_rules = models.JSONField(default=dict, blank=True)
    default_value = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        db_table = 'system_settings'
        unique_together = [['key', 'organization_id']]
        indexes = [
            models.Index(fields=['key', 'organization_id']),
            models.Index(fields=['is_public']),
        ]
    
    def __str__(self):
        return f"{self.key} = {self.value}"


class APICache(models.Model):
    """API response caching for performance"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cache_key = models.CharField(max_length=500, unique=True, db_index=True)
    cache_value = models.JSONField()
    response_data = models.JSONField(default=dict)
    content_type = models.CharField(max_length=100, default='application/json')
    
    # Cache metadata
    hits = models.PositiveIntegerField(default=0)
    size_bytes = models.PositiveIntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    last_accessed = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(db_index=True)
    
    # Request context
    endpoint = models.CharField(max_length=255, blank=True, db_index=True)
    http_method = models.CharField(max_length=10, blank=True)
    user_id = models.UUIDField(null=True, blank=True, db_index=True)
    organization_id = models.UUIDField(null=True, blank=True, db_index=True)
    
    class Meta:
        db_table = 'api_cache'
        indexes = [
            models.Index(fields=['cache_key']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['endpoint']),
            models.Index(fields=['user_id', 'endpoint']),
            models.Index(fields=['organization_id', 'endpoint']),
        ]
    
    def __str__(self):
        return f"Cache: {self.cache_key}"


class UserSession(models.Model):
    """User session tracking"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    session_key = models.CharField(max_length=255, unique=True, db_index=True)
    
    # Session data
    ip_address = models.GenericIPAddressField(db_index=True)
    user_agent = models.TextField(blank=True)
    
    # Organization context
    organization_id = models.UUIDField(null=True, blank=True, db_index=True)
    
    # Activity tracking
    last_activity = models.DateTimeField(auto_now=True)
    page_views = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(db_index=True)
    
    class Meta:
        db_table = 'user_sessions'
        indexes = [
            models.Index(fields=['session_key']),
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['ip_address']),
            models.Index(fields=['organization_id']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"Session for {self.user.email}"


class FileUpload(models.Model):
    """File upload tracking"""
    
    class FileType(models.TextChoices):
        RESUME = 'resume', 'Resume'
        AVATAR = 'avatar', 'Avatar'
        COMPANY_LOGO = 'company_logo', 'Company Logo'
        DOCUMENT = 'document', 'Document'
        EXPORT = 'export', 'Export'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploads')
    file_name = models.CharField(max_length=255)
    file_path = models.CharField(max_length=500)
    file_size = models.PositiveIntegerField()
    content_type = models.CharField(max_length=100)
    file_type = models.CharField(max_length=20, choices=FileType.choices, db_index=True)
    
    # Processing status
    is_processed = models.BooleanField(default=False)
    processing_status = models.CharField(max_length=50, default='pending')
    processing_error = models.TextField(blank=True)
    
    # Organization context
    organization_id = models.UUIDField(null=True, blank=True, db_index=True)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    checksum = models.CharField(max_length=64, blank=True, db_index=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'file_uploads'
        indexes = [
            models.Index(fields=['user', 'file_type']),
            models.Index(fields=['organization_id', 'file_type']),
            models.Index(fields=['checksum']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.file_type}: {self.file_name}"
