from django.contrib import admin

from .models import AuditLog, Organization, OrganizationInvite, OrganizationSettings, RecruiterProfile, UserProfile


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "slug", "created_at")
    search_fields = ("name", "slug")


@admin.register(OrganizationSettings)
class OrganizationSettingsAdmin(admin.ModelAdmin):
    list_display = ("organization", "timezone", "candidate_visibility", "allow_public_job_board", "auto_publish_jobs")
    search_fields = ("organization__name", "organization__slug", "domain")


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "organization", "created_at")
    list_filter = ("role", "organization")
    search_fields = ("user__username", "user__email", "organization__name")


@admin.register(RecruiterProfile)
class RecruiterProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "company_name", "created_at")
    search_fields = ("user__email", "company_name")


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("user", "action", "timestamp")
    search_fields = ("user__email", "action")
    list_filter = ("timestamp",)


@admin.register(OrganizationInvite)
class OrganizationInviteAdmin(admin.ModelAdmin):
    list_display = ("email", "organization", "role", "status", "expires_at", "created_at")
    search_fields = ("email", "organization__name", "organization__slug")
    list_filter = ("status", "role", "organization")
