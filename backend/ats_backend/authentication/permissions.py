from rest_framework.permissions import BasePermission


def get_user_role(user):
    if not user or not user.is_authenticated:
        return None

    if user.is_superuser or user.is_staff:
        return 'admin'

    try:
        return user.userprofile.role
    except Exception:
        return None


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return get_user_role(request.user) == 'admin'


class IsRecruiter(BasePermission):
    def has_permission(self, request, view):
        return get_user_role(request.user) == 'recruiter'


class IsCandidate(BasePermission):
    def has_permission(self, request, view):
        return get_user_role(request.user) == 'candidate'
