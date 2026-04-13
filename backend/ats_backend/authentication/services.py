from datetime import timedelta
import secrets

from django.contrib.auth.models import User
from django.utils import timezone
from candidates.models import Candidate
from authentication.models import RecruiterProfile, UserProfile, AuditLog, OrganizationInvite
from authentication.organization import (
    assign_user_organization,
    get_or_create_named_organization,
    get_or_create_organization_settings,
    get_organization_by_slug,
    get_user_organization,
    resolve_candidate_organization,
    resolve_recruiter_by_id,
    resolve_recruiter_organization,
)
from authentication.permissions import is_platform_admin
from core.exceptions import ValidationError, ConflictError, NotFoundError
from core.validators import validate_email_address, validate_experience_years, validate_full_name, validate_password


def _split_full_name(full_name):
    validated_name = validate_full_name(full_name)
    parts = validated_name.split()
    first_name = parts[0]
    last_name = ' '.join(parts[1:]) if len(parts) > 1 else ''
    return validated_name, first_name, last_name


def _resolve_recruiter_creation_organization(data, admin_user=None):
    if admin_user:
        requested_slug = str(data.get("organization_slug") or "").strip()
        requested_name = str(data.get("organization_name") or "").strip()

        if is_platform_admin(admin_user):
            organization = None
            if requested_slug:
                organization = get_organization_by_slug(requested_slug)
            elif requested_name:
                organization = get_or_create_named_organization(name=requested_name)

            if not organization:
                raise ValidationError("Platform admin must choose an organization for recruiter creation")
            return organization

        organization = get_user_organization(admin_user)
        if not organization:
            raise ValidationError("Organization must exist before creating recruiters")

        if requested_slug and requested_slug != organization.slug:
            raise ValidationError("Recruiters can only be created inside the admin organization")
        if requested_name and requested_name.lower() != organization.name.lower():
            raise ValidationError("Recruiters can only be created inside the admin organization")
        return organization

    organization_name = str(data.get("organization_name") or "").strip()
    organization_slug = str(data.get("organization_slug") or "").strip()
    if not organization_name and not organization_slug:
        raise ValidationError("Organization name or organization slug is required for recruiter registration")

    return resolve_recruiter_organization(data)


def create_candidate(data):
    """
    Create a new candidate user and profile with validation
    """
    try:
        # Validate email (should already be validated in view, but double-check)
        email = validate_email_address(data['email'])

        # Check if user already exists
        if User.objects.filter(email=email).exists():
            raise ConflictError("Email already exists")

        full_name, first_name, last_name = _split_full_name(data['full_name'])

        user = User.objects.create_user(
            username=email,
            email=email,
            password=data['password'],
            first_name=first_name,
            last_name=last_name,
        )

        recruiter = resolve_recruiter_by_id(data.get("recruiter_id"))
        job = None
        job_id = data.get("job_id")
        if job_id:
            from jobs.models import JobDescription
            job = JobDescription.objects.filter(id=job_id).select_related("organization").first()

        organization = resolve_candidate_organization(
            user=user,
            recruiter=recruiter,
            job=job,
            organization_slug=data.get("organization_slug"),
        )
        assign_user_organization(user, organization, role=UserProfile.Role.CANDIDATE)

        experience_years = validate_experience_years(data.get('experience'))

        Candidate.objects.create(
            user=user,
            organization=organization,
            full_name=full_name,
            email=email,
            phone=data.get('phone', ''),
            summary=data.get('summary', ''),
            total_experience_years=experience_years
        )

        AuditLog.objects.create(
            user=user,
            action="Candidate account created"
        )

        return user

    except KeyError as e:
        raise ValidationError(f"Missing required field: {e}")
    except Exception as e:
        if isinstance(e, (ValidationError, ConflictError)):
            raise
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error creating candidate: {str(e)}", exc_info=True)
        raise ValidationError("Failed to create candidate account")


def create_recruiter(data, admin_user=None):
    email = validate_email_address(data.get('email'))
    full_name_input = data.get('full_name')
    if not full_name_input:
        first_name_input = (data.get('first_name') or '').strip()
        last_name_input = (data.get('last_name') or '').strip()
        full_name_input = ' '.join(part for part in [first_name_input, last_name_input] if part)
    full_name, first_name, last_name = _split_full_name(full_name_input)

    if User.objects.filter(email=email).exists():
        raise ConflictError("Email already exists")

    organization = _resolve_recruiter_creation_organization(data, admin_user=admin_user)

    user = User.objects.create_user(
        username=email,
        email=email,
        password=data['password'],
        first_name=first_name,
        last_name=last_name,
    )

    assign_user_organization(user, organization, role=UserProfile.Role.RECRUITER)

    RecruiterProfile.objects.create(
        user=user,
        company_name=organization.name,
    )

    # Only create audit log if admin_user is provided
    if admin_user:
        AuditLog.objects.create(
            user=admin_user,
            action=f"Created recruiter {full_name} ({user.email})"
        )

    return user


def create_organization_with_provided_admin(data, platform_admin):
    """
    Create a new organization with admin credentials provided by SuperAdmin.
    
    Args:
        data: Dict with 'name', 'admin_email', 'admin_password', 'admin_first_name', 'admin_last_name'
        platform_admin: User (SuperAdmin) creating this organization
    
    Returns:
        Tuple: (organization, admin_user)
    
    Process:
        1. Validate admin credentials
        2. Generate unique slug from name
        3. Create Organization
        4. Create Organization Settings
        5. Create Admin User with provided credentials
        6. Assign user to organization
        7. Log audit trail
    """
    from authentication.models import Organization

    organization_name = str(data.get("name") or "").strip()
    admin_email = str(data.get("admin_email") or "").strip()
    admin_password = str(data.get("admin_password") or "").strip()
    admin_first_name = str(data.get("admin_first_name") or "").strip()
    admin_last_name = str(data.get("admin_last_name") or "").strip()

    # Validate required fields
    if not organization_name:
        raise ValidationError("Organization name is required")
    if not admin_email:
        raise ValidationError("Admin email is required")
    if not admin_password:
        raise ValidationError("Admin password is required")

    # Validate email format
    validate_email_address(admin_email)

    # Validate password strength
    validate_password(admin_password)

    # Generate unique slug
    base_slug = organization_name.lower().replace(' ', '-').replace('_', '-')
    slug = base_slug
    counter = 1
    while Organization.objects.filter(slug=slug).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1

    # Check if email already exists
    if User.objects.filter(email=admin_email).exists():
        raise ConflictError(f"A user with email {admin_email} already exists")

    # Create organization
    organization = Organization.objects.create(
        name=organization_name,
        slug=slug,
        admin_email=admin_email,
        website=data.get("website", ""),
        industry=data.get("industry", ""),
        size=data.get("size", ""),
        is_active=True,
        created_by=platform_admin,
    )

    # Create organization settings
    get_or_create_organization_settings(organization)

    # Create admin user with provided credentials
    admin_user = User.objects.create_user(
        username=admin_email,
        email=admin_email,
        password=admin_password,
        first_name=admin_first_name,
        last_name=admin_last_name,
        is_active=True,
    )

    # Create user profile
    UserProfile.objects.create(
        user=admin_user,
        organization=organization,
        role=UserProfile.Role.ORG_ADMIN,
    )

    # Log audit trail
    AuditLog.objects.create(
        user=platform_admin,
        action=f'ORGANIZATION_CREATED: "{organization_name}" with admin {admin_email}',
    )

    return organization, admin_user


def create_organization_with_admin(data, platform_admin):
    """
    Create a new organization with auto-generated admin credentials and async email notification.
    
    Args:
        data: Dict with 'name' and optional 'website', 'industry', 'size'
        platform_admin: User (platform admin) creating this organization
    
    Returns:
        Tuple: (organization, admin_user, admin_password)
    
    Process:
        1. Generate unique slug from name
        2. Generate secure admin email and password
        3. Create Organization with PENDING registration status
        4. Create Organization Settings
        5. Create Admin User
        6. Queue async email with registration credentials
        7. Log audit trail
    """
    from django.utils.crypto import get_random_string
    from authentication.models import Organization
    from authentication.tasks import send_organization_registration_email

    organization_name = str(data.get("name") or "").strip()
    if not organization_name:
        raise ValidationError("Organization name is required")

    # Generate unique slug
    base_slug = organization_name.lower().replace(' ', '-').replace('_', '-')
    slug = base_slug
    counter = 1
    while Organization.objects.filter(slug=slug).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1

    # Generate secure admin credentials
    admin_email = data.get("admin_email") or f"admin@{slug}.ats.local"
    admin_password = get_random_string(length=16)  # Secure 16-char password

    # Check if email already exists
    if User.objects.filter(email=admin_email).exists():
        raise ConflictError(f"A user with email {admin_email} already exists")

    # Create organization with new registration tracking fields
    organization = Organization.objects.create(
        name=organization_name,
        slug=slug,
        admin_email=admin_email,
        admin_password=admin_password,
        registration_status=Organization.RegistrationStatus.PENDING,
        website=data.get("website", ""),
        industry=data.get("industry", ""),
        size=data.get("size", ""),
        country=data.get("country", ""),
        created_by=platform_admin,
        description=data.get("description", ""),
    )

    # Create organization settings
    get_or_create_organization_settings(organization)

    # Create admin user
    admin_user = organization.create_admin_user()

    # Log the action
    AuditLog.objects.create(
        user=platform_admin,
        action=f"Created organization '{organization_name}' (slug: {slug}) with admin email: {admin_email}"
    )

    # Queue async email with registration credentials
    try:
        send_organization_registration_email.delay(
            organization.id,
            admin_email,
            organization_name,
            admin_password,
            platform_admin.email
        )
    except Exception as e:
        # Log error but don't fail - org is created, email can be retried manually
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to queue registration email for org {organization.id}: {str(e)}")
        organization.registration_status = Organization.RegistrationStatus.EMAIL_FAILED
        organization.setup_email_last_error = str(e)[:500]
        organization.save(update_fields=['registration_status', 'setup_email_last_error'])

    return organization, admin_user, admin_password  # Return password for immediate display


def deactivate_recruiter(user, admin_user):
    user.is_active = False
    user.save()

    AuditLog.objects.create(
        user=admin_user,
        action=f"Deactivated recruiter {user.email}"
    )


def _generate_invite_token():
    return secrets.token_urlsafe(24)


def _ensure_invite_not_expired(invite):
    if invite.status == OrganizationInvite.Status.PENDING and invite.expires_at <= timezone.now():
        invite.status = OrganizationInvite.Status.EXPIRED
        invite.save(update_fields=["status", "updated_at"])
    return invite


def create_organization_invite(data, admin_user):
    email = validate_email_address(data.get("email"))
    role = data.get("role") or UserProfile.Role.RECRUITER

    if role != UserProfile.Role.RECRUITER:
        raise ValidationError("Only recruiter invites are supported right now")

    organization = get_user_organization(admin_user)
    if not organization:
        raise ValidationError("Admin organization is required")

    if User.objects.filter(email=email).exists():
        raise ConflictError("A user with this email already exists")

    existing_invite = OrganizationInvite.objects.filter(
        organization=organization,
        email=email,
        status=OrganizationInvite.Status.PENDING,
    ).order_by("-created_at").first()
    if existing_invite:
        _ensure_invite_not_expired(existing_invite)
        if existing_invite.status == OrganizationInvite.Status.PENDING:
            raise ConflictError("An active invite already exists for this email")

    invite = OrganizationInvite.objects.create(
        organization=organization,
        email=email,
        invited_by=admin_user,
        role=role,
        token=_generate_invite_token(),
    )

    AuditLog.objects.create(
        user=admin_user,
        action=f"Sent recruiter invite to {email} for {organization.slug}",
    )

    return invite


def get_organization_invite_by_token(token):
    invite = OrganizationInvite.objects.filter(token=token).select_related("organization", "invited_by").first()
    if not invite:
        raise NotFoundError("Invite not found")
    return _ensure_invite_not_expired(invite)


def resend_organization_invite(invite, admin_user):
    invite = _ensure_invite_not_expired(invite)
    if invite.status == OrganizationInvite.Status.ACCEPTED:
        raise ConflictError("Accepted invites cannot be resent")
    if invite.status == OrganizationInvite.Status.REVOKED:
        raise ConflictError("Revoked invites cannot be resent")

    invite.token = _generate_invite_token()
    invite.status = OrganizationInvite.Status.PENDING
    invite.expires_at = timezone.now() + timedelta(days=7)
    invite.save(update_fields=["token", "status", "expires_at", "updated_at"])

    AuditLog.objects.create(
        user=admin_user,
        action=f"Resent recruiter invite to {invite.email} for {invite.organization.slug}",
    )
    return invite


def revoke_organization_invite(invite, admin_user):
    invite = _ensure_invite_not_expired(invite)
    if invite.status == OrganizationInvite.Status.ACCEPTED:
        raise ConflictError("Accepted invites cannot be revoked")
    if invite.status == OrganizationInvite.Status.REVOKED:
        return invite

    invite.status = OrganizationInvite.Status.REVOKED
    invite.save(update_fields=["status", "updated_at"])

    AuditLog.objects.create(
        user=admin_user,
        action=f"Revoked recruiter invite to {invite.email} for {invite.organization.slug}",
    )
    return invite


def accept_organization_invite(token, data):
    invite = get_organization_invite_by_token(token)
    if invite.status == OrganizationInvite.Status.ACCEPTED:
        raise ConflictError("Invite has already been accepted")
    if invite.status == OrganizationInvite.Status.REVOKED:
        raise ConflictError("Invite has been revoked")
    if invite.status == OrganizationInvite.Status.EXPIRED:
        raise ConflictError("Invite has expired")

    email = invite.email
    if User.objects.filter(email=email).exists():
        raise ConflictError("A user with this email already exists")

    validate_password(data.get("password"))
    full_name, first_name, last_name = _split_full_name(data.get("full_name"))

    user = User.objects.create_user(
        username=email,
        email=email,
        password=data["password"],
        first_name=first_name,
        last_name=last_name,
    )
    assign_user_organization(user, invite.organization, role=invite.role)

    if invite.role == UserProfile.Role.RECRUITER:
        RecruiterProfile.objects.create(
            user=user,
            company_name=invite.organization.name,
        )

    invite.status = OrganizationInvite.Status.ACCEPTED
    invite.accepted_at = timezone.now()
    invite.accepted_by = user
    invite.save(update_fields=["status", "accepted_at", "accepted_by", "updated_at"])

    AuditLog.objects.create(
        user=user,
        action=f"Accepted recruiter invite for {invite.organization.slug}",
    )

    return user, invite
