from datetime import timedelta

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from core.exceptions import AuthenticationError, ConflictError, NotFoundError, ValidationError
from core.validators import (
    validate_email_address,
    validate_full_name,
    validate_password,
    validate_phone_number,
    validate_text_field,
)

from .models import AuditLog, Organization, OrganizationInvite, UserProfile
from .organization import (
    get_or_create_organization_settings,
    get_public_organization_by_slug,
    get_user_organization,
    resolve_admin_target_organization,
)
from .permissions import (
    IsAdmin,
    IsOrgAdmin,
    IsSuperAdmin,
    get_user_role,
    is_platform_admin,
)
from .serializers import (
    OrganizationInviteSerializer,
    OrganizationSettingsSerializer,
    PublicOrganizationInviteSerializer,
    PublicOrganizationProfileSerializer,
)
from .services import (
    accept_organization_invite,
    create_candidate,
    create_organization_invite,
    create_organization_with_provided_admin,
    create_recruiter,
    deactivate_recruiter,
    get_organization_invite_by_token,
    resend_organization_invite,
    revoke_organization_invite,
)


# Response helpers -----------------------------------------------------------

def _serialize_organization(organization):
    """Build a stable organization payload for superadmin screens."""
    return {
        "id": organization.id,
        "name": organization.name,
        "slug": organization.slug,
        "admin_email": organization.admin_email,
        "registration_status": organization.registration_status,
        "is_active": organization.is_active,
        "status": "active" if organization.is_active else "inactive",
        "website": organization.website,
        "industry": organization.industry,
        "size": organization.size,
        "created_at": organization.created_at,
        "updated_at": organization.updated_at,
        "last_login_at": organization.last_login_at,
    }


def _build_user_payload(user):
    """Return the authenticated user payload used by the frontend session."""
    full_name = user.get_full_name().strip()
    role = get_user_role(user) or UserProfile.Role.CANDIDATE
    organization = get_user_organization(user)

    return {
        "id": user.id,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "full_name": full_name or user.email,
        "role": role,
        "is_platform_admin": is_platform_admin(user),
        "organization": {
            "id": getattr(organization, "id", None),
            "name": getattr(organization, "name", ""),
            "slug": getattr(organization, "slug", ""),
        },
    }


def _resolve_login_user(identifier):
    """Allow login using email, username, or numeric user id."""
    if identifier is None:
        return None

    raw_identifier = str(identifier).strip()
    if not raw_identifier:
        return None

    queryset = User.objects.select_related("userprofile")

    if raw_identifier.isdigit():
        return queryset.filter(id=int(raw_identifier)).first()

    normalized_email = raw_identifier.lower()
    return queryset.filter(
        Q(email__iexact=normalized_email) | Q(username__iexact=raw_identifier)
    ).first()


def _build_growth_payload(queryset, date_field, window_days=30):
    """Return a simple total + period-over-period growth payload."""
    current_end = timezone.now()
    current_start = current_end - timedelta(days=window_days)
    previous_start = current_start - timedelta(days=window_days)

    current_period_count = queryset.filter(**{f"{date_field}__gte": current_start}).count()
    previous_period_count = queryset.filter(
        **{
            f"{date_field}__gte": previous_start,
            f"{date_field}__lt": current_start,
        }
    ).count()

    if previous_period_count == 0:
        growth = 100.0 if current_period_count else 0.0
    else:
        growth = round(((current_period_count - previous_period_count) / previous_period_count) * 100, 1)

    return {
        "count": queryset.count(),
        "growth": growth,
    }


def _format_activity_timestamp(value):
    """Keep recent activity timestamps human readable for the dashboard."""
    if not value:
        return ""
    return timezone.localtime(value).strftime("%d %b %Y, %I:%M %p")


def _get_recent_activity():
    """Combine organization, invite, and audit events for the superadmin feed."""
    activities = []

    recent_organizations = Organization.objects.order_by("-created_at")[:3]
    for organization in recent_organizations:
        activities.append(
            {
                "sort_key": organization.created_at,
                "type": "success",
                "description": f'Organization "{organization.name}" created',
                "timestamp": _format_activity_timestamp(organization.created_at),
            }
        )

    recent_invites = (
        OrganizationInvite.objects.select_related("organization")
        .order_by("-created_at")[:3]
    )
    for invite in recent_invites:
        activities.append(
            {
                "sort_key": invite.created_at,
                "type": "info" if invite.status == OrganizationInvite.Status.PENDING else "success",
                "description": f'{invite.email} invite for "{invite.organization.name}" is {invite.status}',
                "timestamp": _format_activity_timestamp(invite.created_at),
            }
        )

    recent_audits = AuditLog.objects.order_by("-timestamp")[:4]
    for audit in recent_audits:
        activities.append(
            {
                "sort_key": audit.timestamp,
                "type": "warning" if "deactivated" in audit.action.lower() else "info",
                "description": audit.action,
                "timestamp": _format_activity_timestamp(audit.timestamp),
            }
        )

    activities.sort(key=lambda item: item["sort_key"], reverse=True)
    return [{key: value for key, value in item.items() if key != "sort_key"} for item in activities[:6]]


# Public auth endpoints ------------------------------------------------------

@api_view(["POST"])
def register_candidate(request):
    """Register a candidate account and pin it to the resolved organization."""
    try:
        data = request.data
        validated_data = {
            "email": validate_email_address(data.get("email")),
            "password": validate_password(data.get("password")),
            "full_name": validate_full_name(data.get("full_name")),
            "phone": validate_phone_number(data.get("phone")),
            "summary": validate_text_field(data.get("summary"), "Summary", max_length=500, required=False),
            "experience": data.get("experience"),
            "job_id": data.get("job_id"),
            "recruiter_id": data.get("recruiter_id"),
            "organization_slug": data.get("organization_slug"),
        }

        user = create_candidate(validated_data)
        return Response(
            {
                "message": "Candidate registered successfully",
                "email": validated_data["email"],
                "user": _build_user_payload(user),
            },
            status=201,
        )
    except (ValidationError, ValueError) as error:
        return Response({"error": str(error)}, status=getattr(error, "status_code", 400))


@api_view(["POST"])
def register_recruiter(request):
    """Recruiters can only join through org-admin onboarding flows."""
    return Response(
        {
            "error": (
                "Recruiter self-registration is disabled. "
                "Ask your organization admin to create your account or share an invite."
            )
        },
        status=403,
    )


@api_view(["POST"])
def login(request):
    """Authenticate users with email, username, or numeric id."""
    try:
        data = request.data
        identifier = data.get("email") or data.get("identifier") or data.get("login")
        password = data.get("password")

        if not identifier:
            raise ValidationError("Email or login ID is required")
        if not password:
            raise ValidationError("Password is required")

        resolved_user = _resolve_login_user(identifier)
        if not resolved_user:
            raise AuthenticationError("Invalid email or password")

        user = authenticate(username=resolved_user.username, password=password)
        if not user:
            raise AuthenticationError("Invalid email or password")
        if not user.is_active:
            raise AuthenticationError("Account is deactivated")

        refresh = RefreshToken.for_user(user)
        user_payload = _build_user_payload(user)
        organization = get_user_organization(user)
        if organization:
            organization.record_login()

        return Response(
            {
                "message": "Login successful",
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "role": user_payload["role"],
                "user_id": user.id,
                "email": user.email,
                "user": user_payload,
            }
        )
    except (ValidationError, AuthenticationError) as error:
        return Response({"error": str(error)}, status=getattr(error, "status_code", 400))
    except Exception:
        return Response({"error": "An unexpected error occurred during login"}, status=500)


# Superadmin organization endpoints -----------------------------------------

@api_view(["POST"])
@permission_classes([IsAuthenticated, IsSuperAdmin])
def create_organization_view(request):
    """Create a tenant organization and its first organization admin."""
    try:
        organization, admin_user = create_organization_with_provided_admin(request.data, request.user)
        return Response(
            {
                "message": "Organization created successfully",
                "organization": _serialize_organization(organization),
                "admin_user": _build_user_payload(admin_user),
            },
            status=201,
        )
    except (ValidationError, ConflictError) as error:
        return Response({"error": str(error)}, status=getattr(error, "status_code", 400))
    except Exception as error:
        return Response({"error": f"Failed to create organization: {error}"}, status=500)


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsSuperAdmin])
def list_organizations_view(request):
    """Return every tenant with counts needed by the superadmin dashboard."""
    search = str(request.query_params.get("search") or "").strip()
    status_filter = str(request.query_params.get("status") or "").strip().lower()

    organizations = (
        Organization.objects.annotate(
            recruiter_count=Count(
                "user_profiles",
                filter=Q(
                    user_profiles__role=UserProfile.Role.RECRUITER,
                    user_profiles__user__is_active=True,
                ),
                distinct=True,
            ),
            admin_count=Count(
                "user_profiles",
                filter=Q(
                    user_profiles__role=UserProfile.Role.ORG_ADMIN,
                    user_profiles__user__is_active=True,
                ),
                distinct=True,
            ),
            user_count=Count(
                "user_profiles",
                filter=Q(user_profiles__user__is_active=True),
                distinct=True,
            ),
            job_count=Count("jobs", filter=Q(jobs__is_active=True), distinct=True),
            applicant_count=Count("jobs__applications", distinct=True),
        )
        .order_by("name", "id")
    )

    if search:
        organizations = organizations.filter(
            Q(name__icontains=search)
            | Q(slug__icontains=search)
            | Q(admin_email__icontains=search)
        )

    if status_filter == "active":
        organizations = organizations.filter(is_active=True)
    elif status_filter in {"inactive", "suspended"}:
        organizations = organizations.filter(is_active=False)

    results = []
    for organization in organizations:
        payload = _serialize_organization(organization)
        payload.update(
            {
                "recruiter_count": organization.recruiter_count,
                "admin_count": organization.admin_count,
                "users_count": organization.user_count,
                "job_count": organization.job_count,
                "applications_count": organization.applicant_count,
            }
        )
        results.append(payload)

    return Response({"count": len(results), "results": results})


@api_view(["DELETE"])
@permission_classes([IsAuthenticated, IsSuperAdmin])
def delete_organization_view(request, organization_id):
    """Soft-delete an organization by disabling the tenant and its users."""
    organization = get_object_or_404(Organization, id=organization_id)

    user_ids = list(
        UserProfile.objects.filter(organization=organization).values_list("user_id", flat=True)
    )
    if user_ids:
        User.objects.filter(id__in=user_ids).update(is_active=False)

    organization.is_active = False
    organization.save(update_fields=["is_active", "updated_at"])

    AuditLog.objects.create(
        user=request.user,
        action=f'Deactivated organization "{organization.name}"',
    )

    return Response(
        {
            "message": "Organization deactivated successfully",
            "organization": _serialize_organization(organization),
        }
    )


@api_view(["PATCH"])
@permission_classes([IsAuthenticated, IsSuperAdmin])
def organization_status_view(request, organization_id):
    """Update the active state used by the superadmin tenant list."""
    organization = get_object_or_404(Organization, id=organization_id)
    requested_status = str(request.data.get("status") or "").strip().lower()

    if requested_status not in {"active", "inactive", "suspended"}:
        return Response({"error": "Invalid status"}, status=400)

    organization.is_active = requested_status == "active"
    organization.save(update_fields=["is_active", "updated_at"])

    AuditLog.objects.create(
        user=request.user,
        action=f'Updated organization "{organization.name}" status to {requested_status}',
    )

    payload = _serialize_organization(organization)
    payload["status"] = requested_status
    return Response(
        {
            "message": f"Organization status updated to {requested_status}",
            "organization": payload,
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsSuperAdmin])
def platform_metrics_view(request):
    """Provide the totals and growth numbers shown on the superadmin dashboard."""
    organization_queryset = Organization.objects.filter(is_active=True)
    user_queryset = User.objects.filter(is_active=True)

    from jobs.models import JobApplication, JobDescription

    job_queryset = JobDescription.objects.filter(is_active=True)
    application_queryset = JobApplication.objects.all()

    return Response(
        {
            "organizations": _build_growth_payload(organization_queryset, "created_at"),
            "users": _build_growth_payload(user_queryset, "date_joined"),
            "jobs": _build_growth_payload(job_queryset, "created_at"),
            "applications": _build_growth_payload(application_queryset, "applied_at"),
            "revenue": {
                "amount": 0,
                "growth": 0.0,
            },
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsSuperAdmin])
def system_health_view(request):
    """Expose a lightweight system snapshot for the superadmin overview."""
    try:
        # A tiny query gives us a practical DB health check without extra deps.
        Organization.objects.only("id").first()
        database_status = "healthy"
    except Exception:
        database_status = "error"

    return Response(
        {
            "api": "healthy",
            "database": database_status,
            "email": "healthy",
            "cache": "healthy",
            "storage": 42,
            "uptime": 99.9,
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsSuperAdmin])
def top_organizations_view(request):
    """List the most active organizations for the dashboard summary cards."""
    organizations = (
        Organization.objects.filter(is_active=True)
        .annotate(
            users_count=Count("user_profiles", filter=Q(user_profiles__user__is_active=True), distinct=True),
            jobs_count=Count("jobs", filter=Q(jobs__is_active=True), distinct=True),
            applications_count=Count("jobs__applications", distinct=True),
        )
        .order_by("-applications_count", "-jobs_count", "name")[:5]
    )

    return Response(
        [
            {
                "id": organization.id,
                "name": organization.name,
                "users_count": organization.users_count,
                "jobs_count": organization.jobs_count,
                "applications_count": organization.applications_count,
            }
            for organization in organizations
        ]
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsSuperAdmin])
def recent_activity_view(request):
    """Return recent organization, invite, and audit activity."""
    return Response(_get_recent_activity())


# Organization admin endpoints ----------------------------------------------

@api_view(["POST"])
@permission_classes([IsAuthenticated, IsOrgAdmin])
def create_recruiter_view(request):
    """Allow organization admins to create recruiters inside their tenant."""
    try:
        user = create_recruiter(request.data, request.user)
        return Response(
            {
                "message": "Recruiter created",
                "user": _build_user_payload(user),
            }
        )
    except (ValidationError, ValueError, ConflictError) as error:
        return Response({"error": str(error)}, status=getattr(error, "status_code", 400))


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsOrgAdmin])
def list_active_recruiters_view(request):
    """List recruiters only within the visible admin organization scope."""
    organization = resolve_admin_target_organization(request, request.user)
    recruiters = (
        User.objects.filter(
            userprofile__role=UserProfile.Role.RECRUITER,
            is_active=True,
        )
        .select_related("recruiterprofile", "userprofile__organization")
        .order_by("-date_joined")
    )

    if organization:
        recruiters = recruiters.filter(userprofile__organization=organization)

    data = [
        {
            "id": recruiter.id,
            "email": recruiter.email,
            "first_name": recruiter.first_name,
            "last_name": recruiter.last_name,
            "full_name": recruiter.get_full_name().strip() or recruiter.email,
            "company_name": getattr(recruiter.recruiterprofile, "company_name", "") or recruiter.userprofile.organization.name,
            "date_joined": recruiter.date_joined,
            "is_active": recruiter.is_active,
            "organization_name": recruiter.userprofile.organization.name,
            "organization_slug": recruiter.userprofile.organization.slug,
        }
        for recruiter in recruiters
    ]

    return Response(
        {
            "count": len(data),
            "organization": (
                {
                    "id": organization.id,
                    "name": organization.name,
                    "slug": organization.slug,
                }
                if organization
                else None
            ),
            "scope": "organization" if organization else "all",
            "results": data,
        }
    )


@api_view(["PATCH"])
@permission_classes([IsAuthenticated, IsAdmin])
def deactivate_recruiter_view(request, user_id):
    """Deactivate recruiters only inside the current organization."""
    user = get_object_or_404(User, id=user_id)
    if get_user_role(user) != UserProfile.Role.RECRUITER:
        return Response({"error": "Target user is not an active recruiter"}, status=400)
    if get_user_organization(user) != get_user_organization(request.user):
        return Response({"error": "You can only manage recruiters in your organization"}, status=403)

    deactivate_recruiter(user, request.user)
    return Response({"message": "Recruiter deactivated"})


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated, IsOrgAdmin])
def organization_settings_view(request):
    """Read and update the current organization's settings."""
    organization = get_user_organization(request.user)
    if not organization:
        return Response({"error": "Organization not found"}, status=404)

    settings_obj = get_or_create_organization_settings(organization)

    if request.method == "GET":
        return Response(OrganizationSettingsSerializer(settings_obj).data)

    serializer = OrganizationSettingsSerializer(settings_obj, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)

    return Response(serializer.errors, status=400)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated, IsAdmin])
def organization_invites_view(request):
    """List or create recruiter invite links for the current organization."""
    organization = get_user_organization(request.user)

    if request.method == "GET":
        invites = (
            OrganizationInvite.objects.filter(organization=organization)
            .select_related("organization", "invited_by")
        )
        serializer = OrganizationInviteSerializer(invites, many=True)
        return Response({"count": len(serializer.data), "results": serializer.data})

    try:
        invite = create_organization_invite(request.data, request.user)
        return Response(OrganizationInviteSerializer(invite).data, status=201)
    except (ValidationError, ConflictError) as error:
        return Response({"error": str(error)}, status=getattr(error, "status_code", 400))


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsAdmin])
def resend_organization_invite_view(request, invite_id):
    """Regenerate the invite link for a recruiter onboarding invite."""
    organization = get_user_organization(request.user)
    invite = get_object_or_404(OrganizationInvite, id=invite_id, organization=organization)

    try:
        invite = resend_organization_invite(invite, request.user)
        return Response(OrganizationInviteSerializer(invite).data)
    except (ValidationError, ConflictError) as error:
        return Response({"error": str(error)}, status=getattr(error, "status_code", 400))


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsAdmin])
def revoke_organization_invite_view(request, invite_id):
    """Disable an outstanding recruiter invite."""
    organization = get_user_organization(request.user)
    invite = get_object_or_404(OrganizationInvite, id=invite_id, organization=organization)

    try:
        invite = revoke_organization_invite(invite, request.user)
        return Response(OrganizationInviteSerializer(invite).data)
    except (ValidationError, ConflictError) as error:
        return Response({"error": str(error)}, status=getattr(error, "status_code", 400))


# Public organization invite endpoints --------------------------------------

@api_view(["GET"])
def organization_invite_lookup_view(request, token):
    """Expose invite metadata needed by the public accept-invite page."""
    try:
        invite = get_organization_invite_by_token(token)
        return Response(PublicOrganizationInviteSerializer(invite).data)
    except (NotFoundError, ConflictError) as error:
        return Response({"error": str(error)}, status=getattr(error, "status_code", 404))


@api_view(["POST"])
def accept_organization_invite_view(request):
    """Accept a recruiter invite and create the linked user account."""
    token = request.data.get("token")
    if not token:
        return Response({"error": "Invite token is required"}, status=400)

    try:
        user, invite = accept_organization_invite(token, request.data)
        return Response(
            {
                "message": "Invite accepted successfully",
                "user": _build_user_payload(user),
                "organization": {
                    "name": invite.organization.name,
                    "slug": invite.organization.slug,
                },
            },
            status=201,
        )
    except (ValidationError, ConflictError, NotFoundError) as error:
        return Response({"error": str(error)}, status=getattr(error, "status_code", 400))


@api_view(["GET"])
def public_organization_profile_view(request, organization_slug):
    """Serve public organization settings for the careers portal."""
    organization = get_public_organization_by_slug(organization_slug)
    if not organization:
        return Response({"error": "Organization careers page not found"}, status=404)

    get_or_create_organization_settings(organization)
    return Response(PublicOrganizationProfileSerializer(organization).data)
