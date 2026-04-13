from django.contrib.auth.models import User
from django.utils.text import slugify
from django.core.cache import cache

from .models import Organization, OrganizationSettings, RecruiterProfile, UserProfile
from .permissions import is_super_admin
from core.cache_keys import CacheKeys


DEFAULT_ORGANIZATION_NAME = "Default Organization"
DEFAULT_ORGANIZATION_SLUG = "default"
ORG_CACHE_TIMEOUT = 300  # 5 minutes


def get_default_organization():
    """Get or create default organization. Cached for performance."""
    cache_key = CacheKeys.get_org_key(DEFAULT_ORGANIZATION_SLUG)
    organization = cache.get(cache_key)
    
    if organization is None:
        organization, _ = Organization.objects.get_or_create(
            slug=DEFAULT_ORGANIZATION_SLUG,
            defaults={
                "name": DEFAULT_ORGANIZATION_NAME,
                "admin_email": "default@ats.local",
                "registration_status": Organization.RegistrationStatus.COMPLETED,
            },
        )
        cache.set(cache_key, organization, ORG_CACHE_TIMEOUT)
    
    return organization


def get_or_create_organization_settings(organization):
    if not organization:
        organization = get_default_organization()
    settings_obj, _ = OrganizationSettings.objects.get_or_create(organization=organization)
    return settings_obj


def is_default_organization(organization):
    return bool(organization and organization.slug == DEFAULT_ORGANIZATION_SLUG)


def _build_organization_identity(name="", slug_value="", email=""):
    """
    Build safe organization name and slug from input, with email fallback.
    """
    cleaned_name = str(name or "").strip()
    cleaned_slug = slugify(slug_value or cleaned_name)

    if not cleaned_slug and email:
        domain = str(email).split("@")[-1].split(".")[0]
        cleaned_slug = slugify(domain)
        cleaned_name = cleaned_name or domain.replace("-", " ").title()

    if not cleaned_slug:
        default_org = get_default_organization()
        return default_org.name, default_org.slug

    return cleaned_name or cleaned_slug.replace("-", " ").title(), cleaned_slug


def get_or_create_named_organization(name="", slug_value="", email="", created_by=None):
    """
    Create or get organization with auto-generated admin email and registration tracking.
    
    Args:
        name: Organization name
        slug_value: URL slug
        email: Fallback email for slug generation
        created_by: User who created this organization (platform admin)
    
    Returns:
        Organization instance with pending registration status
    """
    organization_name, organization_slug = _build_organization_identity(
        name=name,
        slug_value=slug_value,
        email=email,
    )
    
    # Generate admin email if not provided
    admin_email = email or f"admin@{organization_slug}.ats.local"
    
    organization, created = Organization.objects.get_or_create(
        slug=organization_slug,
        defaults={
            "name": organization_name,
            "admin_email": admin_email,
            "registration_status": Organization.RegistrationStatus.PENDING,
            "created_by": created_by,
        },
    )
    
    # Clear cache
    cache_key = CacheKeys.get_org_key(organization_slug)
    cache.delete(cache_key)
    
    return organization


def get_public_organization_by_slug(organization_slug):
    if not organization_slug:
        return None

    # Check cache first
    cache_key = CacheKeys.get_org_key(organization_slug)
    organization = cache.get(cache_key)
    
    if organization is not None:
        if organization.is_active and hasattr(organization, '_settings_cached'):
            return organization if organization._settings_cached.allow_public_job_board else None
        
    organization = Organization.objects.filter(slug=slugify(organization_slug)).first()
    if not organization:
        return None

    settings_obj = get_or_create_organization_settings(organization)
    if not settings_obj.allow_public_job_board:
        return None

    # Cache result
    cache.set(cache_key, organization, ORG_CACHE_TIMEOUT)
    return organization


def get_organization_by_slug(organization_slug):
    """Get organization by slug. Cache for performance."""
    if not organization_slug:
        return None
    
    cache_key = CacheKeys.get_org_key(organization_slug)
    organization = cache.get(cache_key)
    
    if organization is None:
        organization = Organization.objects.filter(slug=slugify(organization_slug)).first()
        if organization:
            cache.set(cache_key, organization, ORG_CACHE_TIMEOUT)
    
    return organization


def _infer_user_role(user):
    if user.is_superuser or user.is_staff:
        return UserProfile.Role.SUPER_ADMIN

    if RecruiterProfile.objects.filter(user=user).exists():
        return UserProfile.Role.RECRUITER

    from jobs.models import JobDescription
    if JobDescription.objects.filter(posted_by=user).exists():
        return UserProfile.Role.RECRUITER

    from candidates.models import Candidate
    if Candidate.objects.filter(user=user).exists() or Candidate.objects.filter(email=user.email).exists():
        return UserProfile.Role.CANDIDATE

    return UserProfile.Role.CANDIDATE


def ensure_user_profile(user, role=None, organization=None):
    if not user:
        return None

    defaults = {
        "role": role or _infer_user_role(user),
        "organization": organization or get_default_organization(),
    }
    profile, created = UserProfile.objects.get_or_create(user=user, defaults=defaults)

    updated_fields = []
    if created:
        return profile

    if role and profile.role != role:
        profile.role = role
        updated_fields.append("role")

    if organization and profile.organization_id != organization.id:
        profile.organization = organization
        updated_fields.append("organization")

    if not profile.organization_id:
        profile.organization = defaults["organization"]
        updated_fields.append("organization")

    if updated_fields:
        profile.save(update_fields=updated_fields + ["updated_at"])

    return profile


def assign_user_organization(user, organization, role=None):
    profile = ensure_user_profile(user, role=role, organization=organization)
    if not profile:
        return None
    if profile.organization_id != organization.id:
        profile.organization = organization
        profile.save(update_fields=["organization", "updated_at"])
    return profile.organization


def get_user_organization(user):
    if not user or not getattr(user, "is_authenticated", False):
        return None

    profile = ensure_user_profile(user)
    return profile.organization if profile else get_default_organization()


def resolve_recruiter_organization(data):
    return get_or_create_named_organization(
        name=data.get("organization_name"),
        slug_value=data.get("organization_slug"),
        email=data.get("email"),
    )


def resolve_candidate_organization(user=None, recruiter=None, job=None, organization_slug=None):
    if job is not None and getattr(job, "organization_id", None):
        return job.organization

    if recruiter is not None:
        organization = get_user_organization(recruiter)
        if organization:
            return organization

    if organization_slug:
        organization = Organization.objects.filter(slug=slugify(organization_slug)).first()
        if organization:
            return organization

    if user is not None and getattr(user, "is_authenticated", False):
        organization = get_user_organization(user)
        if organization:
            return organization

    return get_default_organization()


def can_assign_organization(current_organization, target_organization):
    if current_organization is None or target_organization is None:
        return True
    if current_organization.id == target_organization.id:
        return True
    return is_default_organization(current_organization)


def get_request_organization(request):
    user = getattr(request, "user", None)
    if user and getattr(user, "is_authenticated", False) and not is_super_admin(user):
        user_organization = get_user_organization(user)
        if user_organization:
            return user_organization

    request_organization = getattr(request, "organization", None)
    if request_organization:
        return request_organization

    slug_value = (
        request.query_params.get("organization_slug")
        or request.query_params.get("organization")
        or request.data.get("organization_slug")
    )
    if slug_value:
        return Organization.objects.filter(slug=slugify(slug_value)).first() or get_default_organization()

    user_organization = get_user_organization(user)
    if user_organization:
        return user_organization

    return get_default_organization()


def resolve_admin_target_organization(request, user, required=False):
    requested_slug = (
        request.query_params.get("organization_slug")
        or request.query_params.get("organization")
        or request.data.get("organization_slug")
    )

    if is_super_admin(user):
        organization = get_organization_by_slug(requested_slug) if requested_slug else None
        if required and not organization:
            return None
        return organization

    organization = get_user_organization(user)
    if required and not organization:
        return None
    return organization


def ensure_candidate_organization(candidate, organization):
    if candidate.organization_id != organization.id:
        candidate.organization = organization
    return candidate.organization


def ensure_resume_organization(resume, organization):
    if resume.organization_id != organization.id:
        resume.organization = organization
    return resume.organization


def resolve_recruiter_by_id(recruiter_id):
    if not recruiter_id:
        return None

    try:
        return User.objects.filter(id=int(recruiter_id)).first()
    except (TypeError, ValueError):
        return None
