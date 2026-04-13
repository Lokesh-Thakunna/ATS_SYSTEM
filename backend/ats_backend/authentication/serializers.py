from rest_framework import serializers

from jobs.models import JobDescription

from .models import Organization, OrganizationInvite, OrganizationSettings


class CandidateRegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class OrganizationSettingsSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source="organization.name")
    organization_slug = serializers.CharField(source="organization.slug", read_only=True)
    organization_email = serializers.CharField(source="organization.admin_email", required=False, allow_blank=True)
    organization_password = serializers.CharField(source="organization.admin_password", required=False, allow_blank=True, write_only=True)

    class Meta:
        model = OrganizationSettings
        fields = [
            "organization_name",
            "organization_slug",
            "organization_email",
            "organization_password",
            "company_logo_url",
            "domain",
            "timezone",
            "brand_color",
            "careers_page_title",
            "candidate_visibility",
            "allow_public_job_board",
            "auto_publish_jobs",
            "updated_at",
        ]

    def update(self, instance, validated_data):
        organization_data = validated_data.pop("organization", {})
        organization_name = organization_data.get("name")
        admin_email = organization_data.get("admin_email")
        admin_password = organization_data.get("admin_password")
        
        if organization_name:
            instance.organization.name = organization_name
            update_fields = ["name"]
            
            if admin_email is not None:
                instance.organization.admin_email = admin_email
                update_fields.append("admin_email")
                
            if admin_password is not None and admin_password != "":
                # Hash the password before saving
                from django.contrib.auth.hashers import make_password
                instance.organization.admin_password = make_password(admin_password)
                update_fields.append("admin_password")
                
            instance.organization.save(update_fields=update_fields)

        return super().update(instance, validated_data)


class OrganizationInviteSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source="organization.name", read_only=True)
    organization_slug = serializers.CharField(source="organization.slug", read_only=True)
    invited_by_name = serializers.SerializerMethodField()
    invite_link = serializers.SerializerMethodField()
    is_expired = serializers.SerializerMethodField()

    class Meta:
        model = OrganizationInvite
        fields = [
            "id",
            "email",
            "role",
            "status",
            "token",
            "organization_name",
            "organization_slug",
            "invited_by_name",
            "invite_link",
            "expires_at",
            "accepted_at",
            "created_at",
            "updated_at",
            "is_expired",
        ]

    def get_invited_by_name(self, obj):
        user = obj.invited_by
        if not user:
            return ""
        return user.get_full_name().strip() or user.email

    def get_invite_link(self, obj):
        return f"/invites/accept/{obj.token}"

    def get_is_expired(self, obj):
        from django.utils import timezone

        return obj.expires_at <= timezone.now()


class PublicOrganizationInviteSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source="organization.name", read_only=True)
    organization_slug = serializers.CharField(source="organization.slug", read_only=True)
    is_expired = serializers.SerializerMethodField()

    class Meta:
        model = OrganizationInvite
        fields = [
            "email",
            "role",
            "status",
            "organization_name",
            "organization_slug",
            "expires_at",
            "is_expired",
        ]

    def get_is_expired(self, obj):
        from django.utils import timezone

        return obj.expires_at <= timezone.now()


class PublicOrganizationProfileSerializer(serializers.ModelSerializer):
    company_logo_url = serializers.CharField(source="settings.company_logo_url", read_only=True)
    domain = serializers.CharField(source="settings.domain", read_only=True)
    timezone = serializers.CharField(source="settings.timezone", read_only=True)
    brand_color = serializers.CharField(source="settings.brand_color", read_only=True)
    careers_page_title = serializers.SerializerMethodField()
    open_jobs_count = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        fields = [
            "id",
            "name",
            "slug",
            "company_logo_url",
            "domain",
            "timezone",
            "brand_color",
            "careers_page_title",
            "open_jobs_count",
        ]

    def get_careers_page_title(self, obj):
        title = getattr(obj.settings, "careers_page_title", "")
        return title or f"Careers at {obj.name}"

    def get_open_jobs_count(self, obj):
        return JobDescription.objects.filter(organization=obj, is_active=True).count()
