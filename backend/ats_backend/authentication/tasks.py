# authentication/tasks.py
"""
Celery async tasks for authentication operations.
Handles email sending, invite management, and cleanup tasks.
"""

from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import logging
import os
from datetime import timedelta
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, name='authentication.tasks.send_organization_registration_email')
def send_organization_registration_email(self, org_id, admin_email, org_name, temp_password, created_by_email=None):
    """
    Send organization setup email with admin credentials.
    Called asynchronously after organization is created.
    
    Args:
        org_id: Organization ID
        admin_email: Admin email address
        org_name: Organization name
        temp_password: Temporary password (plaintext - only in this email)
        created_by_email: Email of platform admin who created this org
    """
    try:
        from authentication.models import Organization
        
        organization = Organization.objects.get(id=org_id)
        
        # Build URLs
        frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')
        login_url = f"{frontend_url}/login"
        change_password_url = f"{frontend_url}/settings/security"
        
        context = {
            'admin_email': admin_email,
            'temp_password': temp_password,
            'organization_name': org_name,
            'login_url': login_url,
            'change_password_url': change_password_url,
            'support_email': os.getenv('SUPPORT_EMAIL', 'support@ats.com'),
            'created_by_email': created_by_email or 'Platform Administrator',
        }
        
        # Render email templates
        html_message = render_to_string('emails/organization_registration.html', context)
        plain_message = render_to_string('emails/organization_registration.txt', context)
        
        # Send email
        email = EmailMultiAlternatives(
            subject=f'Welcome to ATS - {org_name} Organization Registration',
            body=plain_message,
            from_email=os.getenv('DEFAULT_FROM_EMAIL', 'noreply@ats.com'),
            to=[admin_email],
        )
        email.attach_alternative(html_message, "text/html")
        result = email.send(fail_silently=False)
        
        # Mark email as sent
        organization.mark_email_sent()
        
        logger.info(f"✓ Organization registration email sent to {admin_email} (Org: {org_name})")
        
        return {
            'status': 'success',
            'message': f'Email sent to {admin_email}',
            'organization_id': org_id,
        }
        
    except Organization.DoesNotExist:
        logger.error(f"Organization {org_id} not found")
        return {'status': 'error', 'message': 'Organization not found'}
        
    except Exception as exc:
        logger.error(f"✗ Failed to send organization registration email: {str(exc)}", exc_info=True)
        
        # Update organization with error
        try:
            organization = Organization.objects.get(id=org_id)
            organization.setup_email_last_error = str(exc)[:500]
            organization.registration_status = Organization.RegistrationStatus.EMAIL_FAILED
            organization.save(update_fields=['setup_email_last_error', 'registration_status'])
        except:
            pass
        
        # Retry with exponential backoff
        countdown = 300 * (2 ** self.request.retries)  # 5 min, 10 min, 20 min
        self.retry(exc=exc, countdown=countdown)


@shared_task(bind=True, max_retries=3, name='authentication.tasks.send_recruiter_invite_email')
def send_recruiter_invite_email(self, invite_id, recruiter_email, org_name, invited_by_name, invite_token):
    """
    Send recruiter invitation email with acceptance link.
    
    Args:
        invite_id: OrganizationInvite ID
        recruiter_email: Recruiter's email
        org_name: Organization name
        invited_by_name: Name of admin who sent invite
        invite_token: Unique invite token
    """
    try:
        from authentication.models import OrganizationInvite
        
        invite = OrganizationInvite.objects.get(id=invite_id)
        
        # Build invitation link
        frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')
        invite_url = f"{frontend_url}/invites/accept?token={invite_token}"
        
        context = {
            'recruiter_email': recruiter_email,
            'organization_name': org_name,
            'invited_by': invited_by_name,
            'invite_url': invite_url,
            'expiry_days': 7,
            'support_email': os.getenv('SUPPORT_EMAIL', 'support@ats.com'),
        }
        
        # Render templates
        html_message = render_to_string('emails/recruiter_invite.html', context)
        plain_message = render_to_string('emails/recruiter_invite.txt', context)
        
        # Send email
        email = EmailMultiAlternatives(
            subject=f'Join {org_name} on ATS - Recruiter Invitation',
            body=plain_message,
            from_email=os.getenv('DEFAULT_FROM_EMAIL', 'noreply@ats.com'),
            to=[recruiter_email],
        )
        email.attach_alternative(html_message, "text/html")
        email.send(fail_silently=False)
        
        logger.info(f"✓ Recruiter invite sent to {recruiter_email} (Org: {org_name})")
        
        return {
            'status': 'success',
            'message': f'Invite sent to {recruiter_email}',
            'invite_id': invite_id,
        }
        
    except OrganizationInvite.DoesNotExist:
        logger.error(f"Invite {invite_id} not found")
        return {'status': 'error', 'message': 'Invite not found'}
        
    except Exception as exc:
        logger.error(f"✗ Failed to send recruiter invite email: {str(exc)}", exc_info=True)
        
        # Retry with exponential backoff
        countdown = 300 * (2 ** self.request.retries)
        self.retry(exc=exc, countdown=countdown)


@shared_task(bind=True, max_retries=3, name='authentication.tasks.send_password_reset_email')
def send_password_reset_email(self, org_id, admin_email, reset_token, org_name):
    """
    Send password reset email with secure reset link.
    
    Args:
        org_id: Organization ID
        admin_email: Admin email
        reset_token: Password reset token (valid for 24 hours)
        org_name: Organization name
    """
    try:
        from authentication.models import Organization
        
        organization = Organization.objects.get(id=org_id)
        
        # Build reset link
        frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')
        reset_url = f"{frontend_url}/auth/reset-password?token={reset_token}"
        
        context = {
            'admin_email': admin_email,
            'organization_name': org_name,
            'reset_url': reset_url,
            'expiry_hours': 24,
            'support_email': os.getenv('SUPPORT_EMAIL', 'support@ats.com'),
        }
        
        # Render templates
        html_message = render_to_string('emails/password_reset.html', context)
        plain_message = render_to_string('emails/password_reset.txt', context)
        
        # Send email
        email = EmailMultiAlternatives(
            subject=f'Reset Your ATS Password - {org_name}',
            body=plain_message,
            from_email=os.getenv('DEFAULT_FROM_EMAIL', 'noreply@ats.com'),
            to=[admin_email],
        )
        email.attach_alternative(html_message, "text/html")
        email.send(fail_silently=False)
        
        logger.info(f"✓ Password reset email sent to {admin_email}")
        
        return {'status': 'success', 'message': f'Reset email sent to {admin_email}'}
        
    except Organization.DoesNotExist:
        logger.error(f"Organization {org_id} not found")
        return {'status': 'error', 'message': 'Organization not found'}
        
    except Exception as exc:
        logger.error(f"✗ Failed to send password reset email: {str(exc)}", exc_info=True)
        countdown = 300 * (2 ** self.request.retries)
        self.retry(exc=exc, countdown=countdown)


@shared_task(name='authentication.tasks.clean_expired_invites')
def clean_expired_invites():
    """
    Periodic task to mark expired organization invites.
    Runs daily at 2 AM UTC.
    """
    try:
        from authentication.models import OrganizationInvite
        
        now = timezone.now()
        
        # Update expired pending invites
        expired_count = OrganizationInvite.objects.filter(
            status=OrganizationInvite.Status.PENDING,
            expires_at__lt=now
        ).update(status=OrganizationInvite.Status.EXPIRED)
        
        logger.info(f"✓ Cleaned up {expired_count} expired organization invites")
        
        return {
            'status': 'success',
            'expired_count': expired_count,
            'timestamp': now.isoformat(),
        }
        
    except Exception as exc:
        logger.error(f"✗ Error cleaning expired invites: {str(exc)}", exc_info=True)
        return {'status': 'error', 'message': str(exc)}


@shared_task(name='authentication.tasks.send_pending_emails')
def send_pending_emails():
    """
    Periodic task to retry failed email sends.
    Runs every 5 minutes.
    """
    try:
        from authentication.models import Organization
        
        # Get organizations with failed email sends (max 10 retries)
        failed_orgs = Organization.objects.filter(
            registration_status=Organization.RegistrationStatus.EMAIL_FAILED,
            setup_email_sent_count__lt=10,
        ).order_by('setup_email_sent_at')[:5]  # Process max 5 at a time
        
        retry_count = 0
        for org in failed_orgs:
            # Re-queue email send
            if org.admin_password and org.created_by:
                send_organization_registration_email.delay(
                    org.id,
                    org.admin_email,
                    org.name,
                    org.admin_password,
                    org.created_by.email
                )
                retry_count += 1
        
        logger.info(f"✓ Requeued {retry_count} failed email sends")
        
        return {
            'status': 'success',
            'retry_count': retry_count,
        }
        
    except Exception as exc:
        logger.error(f"✗ Error in send_pending_emails: {str(exc)}", exc_info=True)
        return {'status': 'error', 'message': str(exc)}


@shared_task(name='authentication.tasks.sync_organization_admin_user')
def sync_organization_admin_user(org_id):
    """
    Sync organization admin user details with User model.
    Called when admin details change.
    """
    try:
        from authentication.models import Organization
        from django.contrib.auth.models import User
        
        org = Organization.objects.get(id=org_id)
        
        # Get or create admin user
        admin_user = User.objects.filter(email=org.admin_email).first()
        
        if admin_user:
            # Update email if needed
            if admin_user.email != org.admin_email:
                admin_user.email = org.admin_email
                admin_user.username = org.admin_email
                admin_user.save()
            
            logger.info(f"✓ Synced admin user for organization {org.name}")
            return {'status': 'success', 'user_id': admin_user.id}
        else:
            logger.warning(f"Admin user not found for organization {org.name}")
            return {'status': 'warning', 'message': 'Admin user not found'}
        
    except Organization.DoesNotExist:
        logger.error(f"Organization {org_id} not found")
        return {'status': 'error', 'message': 'Organization not found'}
        
    except Exception as exc:
        logger.error(f"Error syncing organization admin user: {str(exc)}", exc_info=True)
        return {'status': 'error', 'message': str(exc)}
