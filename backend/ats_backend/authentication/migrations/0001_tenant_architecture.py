# Generated manually for tenant architecture

from datetime import timedelta

from django.conf import settings
from django.db import migrations, models
from django.utils import timezone


def default_invite_expiry():
    return timezone.now() + timedelta(days=7)


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Organization',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('slug', models.SlugField(max_length=255, unique=True)),
                ('admin_email', models.EmailField(blank=True, null=True)),
                ('admin_password', models.CharField(blank=True, max_length=128, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, related_name='created_organizations', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['name', 'id'],
            },
        ),
        migrations.CreateModel(
            name='OrganizationSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('company_logo_url', models.URLField(blank=True, default='')),
                ('domain', models.CharField(blank=True, default='', max_length=255)),
                ('timezone', models.CharField(default=settings.TIME_ZONE, max_length=100)),
                ('brand_color', models.CharField(default='#4f46e5', max_length=20)),
                ('candidate_visibility', models.CharField(choices=[('private', 'Private to organization'), ('job_only', 'Visible through job applications')], default='job_only', max_length=20)),
                ('allow_public_job_board', models.BooleanField(default=True)),
                ('auto_publish_jobs', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('organization', models.OneToOneField(on_delete=models.CASCADE, related_name='settings', to='authentication.organization')),
            ],
            options={
                'ordering': ['organization_id'],
            },
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('super_admin', 'Super Admin'), ('org_admin', 'Organization Admin'), ('recruiter', 'Recruiter'), ('candidate', 'Candidate')], db_index=True, max_length=20)),
                ('created_at', models.DateTimeField(blank=True, null=True, auto_now_add=True)),
                ('updated_at', models.DateTimeField(blank=True, null=True, auto_now=True)),
                ('organization', models.ForeignKey(blank=True, null=True, on_delete=models.PROTECT, related_name='user_profiles', to='authentication.organization')),
                ('user', models.OneToOneField(on_delete=models.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['user_id'],
            },
        ),
        migrations.CreateModel(
            name='RecruiterProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('company_name', models.CharField(blank=True, default='', max_length=255)),
                ('created_at', models.DateTimeField(blank=True, null=True, auto_now_add=True)),
                ('updated_at', models.DateTimeField(blank=True, null=True, auto_now=True)),
                ('user', models.OneToOneField(on_delete=models.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['company_name', 'user_id'],
            },
        ),
        migrations.CreateModel(
            name='AuditLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(max_length=255)),
                ('timestamp', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, related_name='audit_logs', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-timestamp', '-id'],
            },
        ),
        migrations.CreateModel(
            name='OrganizationInvite',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(db_index=True, max_length=254)),
                ('role', models.CharField(choices=[('super_admin', 'Super Admin'), ('org_admin', 'Organization Admin'), ('recruiter', 'Recruiter'), ('candidate', 'Candidate')], default='recruiter', max_length=20)),
                ('token', models.CharField(db_index=True, max_length=255, unique=True)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('accepted', 'Accepted'), ('revoked', 'Revoked'), ('expired', 'Expired')], db_index=True, default='pending', max_length=20)),
                ('expires_at', models.DateTimeField(default=default_invite_expiry)),
                ('accepted_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('accepted_by', models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, related_name='accepted_organization_invites', to=settings.AUTH_USER_MODEL)),
                ('invited_by', models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, related_name='sent_organization_invites', to=settings.AUTH_USER_MODEL)),
                ('organization', models.ForeignKey(on_delete=models.CASCADE, related_name='invites', to='authentication.organization')),
            ],
            options={
                'ordering': ['-created_at', '-id'],
                'indexes': [models.Index(fields=['organization', 'status'], name='org_invite_status_idx')],
            },
        ),
    ]