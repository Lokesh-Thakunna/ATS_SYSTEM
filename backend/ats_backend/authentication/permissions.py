from rest_framework.permissions import BasePermission

from .models import UserProfile


# Canonical role names used across the backend and frontend.
ROLE_ALIASES = {
    "SUPER_ADMIN": UserProfile.Role.SUPER_ADMIN,
    "ORG_ADMIN": UserProfile.Role.ORG_ADMIN,
    "RECRUITER": UserProfile.Role.RECRUITER,
    "CANDIDATE": UserProfile.Role.CANDIDATE,
    "admin": UserProfile.Role.ORG_ADMIN,
}


def normalize_role(role):
    """Convert legacy role labels into the canonical database role values."""
    if role is None:
        return None
    return ROLE_ALIASES.get(str(role).strip(), str(role).strip().lower())


def _get_user_profile(user):
    """Safely resolve the attached profile for authenticated users."""
    if not user or not user.is_authenticated:
        return None
    try:
        return user.userprofile
    except UserProfile.DoesNotExist:
        return None


def is_super_admin(user):
    """Check whether the authenticated user owns the SaaS platform."""
    profile = _get_user_profile(user)
    return bool(profile and normalize_role(profile.role) == UserProfile.Role.SUPER_ADMIN)


def is_org_admin(user):
    """Check whether the authenticated user manages an organization workspace."""
    profile = _get_user_profile(user)
    return bool(profile and normalize_role(profile.role) == UserProfile.Role.ORG_ADMIN)


def is_recruiter(user):
    """Check whether the authenticated user is a recruiter."""
    profile = _get_user_profile(user)
    return bool(profile and normalize_role(profile.role) == UserProfile.Role.RECRUITER)


def is_candidate(user):
    """Check whether the authenticated user is a candidate."""
    profile = _get_user_profile(user)
    return bool(profile and normalize_role(profile.role) == UserProfile.Role.CANDIDATE)


def get_user_organization(user):
    """Return the organization linked to the current authenticated user."""
    profile = _get_user_profile(user)
    return getattr(profile, "organization", None)


def get_user_role(user):
    """Return the canonical role string for the current authenticated user."""
    profile = _get_user_profile(user)
    return normalize_role(getattr(profile, "role", None))


def can_manage_organization(user, organization):
    """Allow super admins or the matching org admin to manage an organization."""
    if is_super_admin(user):
        return True

    profile = _get_user_profile(user)
    return bool(
        profile
        and normalize_role(profile.role) == UserProfile.Role.ORG_ADMIN
        and profile.organization == organization
    )


class IsSuperAdmin(BasePermission):
    """Only super admins can access."""

    def has_permission(self, request, view):
        return is_super_admin(request.user)


class IsOrgAdmin(BasePermission):
    """Only organization admins can access."""

    def has_permission(self, request, view):
        return is_org_admin(request.user)


class IsRecruiter(BasePermission):
    """Only recruiters can access."""

    def has_permission(self, request, view):
        return is_recruiter(request.user)


class IsCandidate(BasePermission):
    """Only candidates can access."""

    def has_permission(self, request, view):
        return is_candidate(request.user)


class IsAuthenticatedUser(BasePermission):
    """Allow any authenticated user."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)


class CanManageOrganization(BasePermission):
    """Allow access to the matching organization owner or the platform owner."""

    def has_object_permission(self, request, view, obj):
        return can_manage_organization(request.user, obj)


class CanManageRecruiters(BasePermission):
    """Allow recruiter management inside the caller's organization scope."""

    def has_permission(self, request, view):
        return is_super_admin(request.user) or is_org_admin(request.user)

    def has_object_permission(self, request, view, obj):
        if is_super_admin(request.user):
            return True

        profile = _get_user_profile(request.user)
        return bool(profile and getattr(obj, "organization", None) == profile.organization)


# Backward-compatible aliases used elsewhere in the project.
is_platform_admin = is_super_admin
IsPlatformAdmin = IsSuperAdmin
IsAdmin = IsOrgAdmin
