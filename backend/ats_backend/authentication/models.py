from datetime import timedelta

from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Organization(models.Model):
    """
    Organization model with enhanced registration tracking for multi-tenant ATS system.
    
    Tracks:
    - Basic organization info (name, slug)
    - Admin credentials (email, password)
    - Registration status and email tracking
    - Password reset tokens for secure re-setup
    - Organization metadata (website, phone, industry)
    - Timestamps for audit trail
    """
    
    class RegistrationStatus(models.TextChoices):
        PENDING = "pending", "Pending Admin Setup"
        EMAIL_SENT = "email_sent", "Setup Email Sent"
        EMAIL_FAILED = "email_failed", "Setup Email Failed"
        IN_PROGRESS = "in_progress", "In Progress"
        COMPLETED = "completed", "Registration Completed"
        PAUSED = "paused", "Registration Paused"

    # Basic Organization Info
    name = models.CharField(max_length=255, db_index=True)
    slug = models.SlugField(max_length=255, unique=True, db_index=True)
    description = models.TextField(blank=True, default="")
    
    # Admin Credentials & Registration
    admin_email = models.EmailField(db_index=True, null=True, blank=True)
    admin_password = models.CharField(max_length=255, null=True, blank=True)  # Hashed password
    
    # Registration Status Tracking
    registration_status = models.CharField(
        max_length=20,
        choices=RegistrationStatus.choices,
        default=RegistrationStatus.PENDING,
        db_index=True
    )
    registration_completed_at = models.DateTimeField(null=True, blank=True)
    
    # Email Delivery Tracking
    setup_email_sent_at = models.DateTimeField(null=True, blank=True)
    setup_email_sent_count = models.IntegerField(default=0)  # Track retry attempts
    setup_email_last_error = models.TextField(blank=True, default="")
    
    # Password Reset / Temporary Setup
    temp_password_token = models.CharField(max_length=255, blank=True, default="")
    temp_password_token_expires_at = models.DateTimeField(null=True, blank=True)
    password_reset_count = models.IntegerField(default=0)
    
    # Organization Metadata
    website = models.URLField(blank=True, default="")
    phone = models.CharField(max_length=20, blank=True, default="")
    industry = models.CharField(max_length=100, blank=True, default="")
    size = models.CharField(
        max_length=20,
        choices=[
            ('1-10', '1-10 employees'),
            ('11-50', '11-50 employees'),
            ('51-200', '51-200 employees'),
            ('201-500', '201-500 employees'),
            ('500+', '500+ employees'),
        ],
        blank=True,
        default=""
    )
    country = models.CharField(max_length=2, blank=True, default="")
    
    # System Status
    is_active = models.BooleanField(default=True, db_index=True)
    
    # Audit Trail
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_organizations",
        db_index=True
    )
    updated_at = models.DateTimeField(auto_now=True)
    last_login_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at", "name", "id"]
        indexes = [
            models.Index(fields=["slug"], name="org_slug_idx"),
            models.Index(fields=["admin_email"], name="org_admin_email_idx"),
            models.Index(fields=["is_active", "created_at"], name="org_active_created_idx"),
            models.Index(fields=["registration_status"], name="org_reg_status_idx"),
            models.Index(fields=["created_by"], name="org_created_by_idx"),
        ]

    def __str__(self):
        return f"{self.name} ({self.registration_status})"
    
    def is_registration_complete(self):
        """Check if organization registration is fully completed"""
        return self.registration_status == self.RegistrationStatus.COMPLETED
    
    def mark_email_sent(self):
        """Mark that setup email was sent"""
        self.setup_email_sent_at = timezone.now()
        self.setup_email_sent_count += 1
        self.registration_status = self.RegistrationStatus.EMAIL_SENT
        self.save(update_fields=['setup_email_sent_at', 'setup_email_sent_count', 'registration_status'])
    
    def mark_registration_completed(self):
        """Mark registration as completed after admin logs in"""
        self.registration_completed_at = timezone.now()
        self.registration_status = self.RegistrationStatus.COMPLETED
        self.save(update_fields=['registration_completed_at', 'registration_status'])
    
    def record_login(self):
        """Record last login timestamp"""
        self.last_login_at = timezone.now()
        self.save(update_fields=['last_login_at'])
    
    def generate_password_reset_token(self):
        """Generate a unique token for password reset"""
        import secrets
        from django.utils import timezone
        from datetime import timedelta
        
        self.temp_password_token = secrets.token_urlsafe(32)
        self.temp_password_token_expires_at = timezone.now() + timedelta(hours=24)
        self.password_reset_count += 1
        self.save(update_fields=['temp_password_token', 'temp_password_token_expires_at', 'password_reset_count'])
        
        return self.temp_password_token
    
    def is_password_reset_token_valid(self, token):
        """Check if password reset token is valid and not expired"""
        if not token or self.temp_password_token != token:
            return False
        
        if not self.temp_password_token_expires_at:
            return False
        
        return timezone.now() <= self.temp_password_token_expires_at
    
    def create_admin_user(self):
        """Create the organization admin user with auto-generated credentials"""
        from django.contrib.auth.hashers import make_password

        # Create Django User
        user = User.objects.create_user(
            username=self.admin_email,
            email=self.admin_email,
            password=self.admin_password,  # This will be hashed automatically
            first_name=f"{self.name} Admin",
            is_active=True
        )

        # Create UserProfile
        UserProfile.objects.create(
            user=user,
            role=UserProfile.Role.ORG_ADMIN,
            organization=self
        )

        return user


class OrganizationSettings(models.Model):
    class CandidateVisibility(models.TextChoices):
        PRIVATE = "private", "Private to organization"
        JOB_ONLY = "job_only", "Visible through job applications"

    organization = models.OneToOneField(
        Organization,
        on_delete=models.CASCADE,
        related_name="settings",
    )
    company_logo_url = models.URLField(blank=True, default="")
    domain = models.CharField(max_length=255, blank=True, default="")
    timezone = models.CharField(max_length=100, default=settings.TIME_ZONE)
    brand_color = models.CharField(max_length=20, default="#4f46e5")
    careers_page_title = models.CharField(max_length=255, blank=True, default="")
    candidate_visibility = models.CharField(
        max_length=20,
        choices=CandidateVisibility.choices,
        default=CandidateVisibility.JOB_ONLY,
    )
    allow_public_job_board = models.BooleanField(default=True)
    auto_publish_jobs = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["organization_id"]

    def __str__(self):
        return f"Settings for {self.organization.name}"


def default_invite_expiry():
    return timezone.now() + timedelta(days=7)


class UserProfile(models.Model):
    class Role(models.TextChoices):
        SUPER_ADMIN = "super_admin", "Super Admin"
        ORG_ADMIN = "org_admin", "Organization Admin"
        RECRUITER = "recruiter", "Recruiter"
        CANDIDATE = "candidate", "Candidate"

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=Role.choices, db_index=True)
    # Organization lives alongside role so we can add SaaS tenancy safely
    # without rewriting the project's existing auth.User model.
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="user_profiles",
        null=True,  # Super admin doesn't belong to any organization
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        ordering = ["user_id"]

    def __str__(self):
        return f"{self.user.email or self.user.username} ({self.role})"

    @property
    def is_super_admin(self):
        return self.role == self.Role.SUPER_ADMIN

    @property
    def is_org_admin(self):
        return self.role == self.Role.ORG_ADMIN

    @property
    def is_recruiter(self):
        return self.role == self.Role.RECRUITER

    @property
    def is_candidate(self):
        return self.role == self.Role.CANDIDATE



class RecruiterProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    company_name = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        ordering = ["company_name", "user_id"]

    def __str__(self):
        return self.company_name or self.user.email or self.user.username


class AuditLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="auth_audit_logs")
    action = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-timestamp", "-id"]

    def __str__(self):
        return f"{self.timestamp}: {self.action}"


class OrganizationInvite(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        REVOKED = "revoked", "Revoked"
        EXPIRED = "expired", "Expired"

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="invites",
    )
    email = models.EmailField(db_index=True)
    invited_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="sent_organization_invites",
    )
    role = models.CharField(
        max_length=20,
        choices=UserProfile.Role.choices,
        default=UserProfile.Role.RECRUITER,
    )
    token = models.CharField(max_length=255, unique=True, db_index=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    expires_at = models.DateTimeField(default=default_invite_expiry)
    accepted_at = models.DateTimeField(null=True, blank=True)
    accepted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="accepted_organization_invites",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["organization", "status"], name="org_invite_status_idx"),
        ]

    def __str__(self):
        return f"{self.email} -> {self.organization.slug} ({self.status})"
