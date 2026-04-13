"""
Production-ready email service with SMTP configuration and template system
"""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.utils import formataddr
from typing import Dict, List, Optional, Union
from datetime import datetime, timedelta
from django.conf import settings
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives, get_connection
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


class EmailService:
    """Production-ready email service with SMTP support"""
    
    def __init__(self):
        self.smtp_config = self._load_smtp_config()
        self.default_from = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@atsplatform.com')
        self.default_from_name = getattr(settings, 'DEFAULT_FROM_NAME', 'ATS Platform')
        
    def _load_smtp_config(self) -> Dict:
        """Load SMTP configuration from settings"""
        return {
            'host': getattr(settings, 'EMAIL_HOST', 'localhost'),
            'port': getattr(settings, 'EMAIL_PORT', 587),
            'username': getattr(settings, 'EMAIL_HOST_USER', ''),
            'password': getattr(settings, 'EMAIL_HOST_PASSWORD', ''),
            'use_tls': getattr(settings, 'EMAIL_USE_TLS', True),
            'use_ssl': getattr(settings, 'EMAIL_USE_SSL', False),
            'timeout': getattr(settings, 'EMAIL_TIMEOUT', 30),
            'connection_pool_size': getattr(settings, 'EMAIL_CONNECTION_POOL_SIZE', 5)
        }
    
    def send_email(self, to_emails: Union[str, List[str]], subject: str, 
                  template_name: Optional[str] = None, context: Optional[Dict] = None,
                  html_content: Optional[str] = None, text_content: Optional[str] = None,
                  from_email: Optional[str] = None, from_name: Optional[str] = None,
                  attachments: Optional[List[Dict]] = None, 
                  organization_id: Optional[str] = None) -> Dict:
        """
        Send email with template support and attachments
        
        Args:
            to_emails: Single email or list of emails
            subject: Email subject
            template_name: Django template name (without .html)
            context: Template context variables
            html_content: Direct HTML content (overrides template)
            text_content: Direct text content (auto-generated from HTML if not provided)
            from_email: Override default from email
            from_name: Override default from name
            attachments: List of {'filename': str, 'content': bytes, 'content_type': str}
            organization_id: For organization-specific email configuration
            
        Returns:
            Dict with success status and details
        """
        try:
            # Prepare email content
            if template_name and context:
                html_content = render_to_string(f'emails/{template_name}.html', context)
                if not text_content:
                    text_content = strip_tags(html_content)
            
            if not html_content and not text_content:
                raise ValueError("Either template_name or content must be provided")
            
            # Create message
            msg = MIMEMultipart('alternative')
            
            # Add text part
            if text_content:
                text_part = MIMEText(text_content, 'plain', 'utf-8')
                msg.attach(text_part)
            
            # Add HTML part
            if html_content:
                html_part = MIMEText(html_content, 'html', 'utf-8')
                msg.attach(html_part)
            
            # Add attachments
            if attachments:
                for attachment in attachments:
                    self._add_attachment(msg, attachment)
            
            # Set headers
            from_addr = formataddr(
                (from_name or self.default_from_name,
                from_email or self.default_from
            )
            
            msg['From'] = from_addr
            msg['To'] = ', '.join(to_emails) if isinstance(to_emails, list) else to_emails
            msg['Subject'] = subject
            
            # Add organization-specific headers
            if organization_id:
                msg['X-Organization-ID'] = organization_id
                msg['X-Email-Type'] = 'transactional'
            
            # Send email
            result = self._send_via_smtp(msg, to_emails)
            
            # Log email sent
            self._log_email_sent(to_emails, subject, result)
            
            return {
                'success': True,
                'message': 'Email sent successfully',
                'recipients': to_emails,
                'subject': subject,
                'message_id': result.get('message_id'),
                'sent_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            error_msg = f"Email sending failed: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'recipients': to_emails,
                'subject': subject
            }
    
    def _add_attachment(self, msg: MIMEMultipart, attachment: Dict):
        """Add attachment to email message"""
        try:
            attachment_part = MIMEBase('application', 'octet-stream')
            attachment_part.set_payload(attachment['content'])
            encoders.encode_base64(attachment_part)
            
            filename = attachment['filename']
            content_type = attachment.get('content_type', 'application/octet-stream')
            
            attachment_part.add_header(
                'Content-Disposition',
                f'attachment; filename="{filename}"'
            )
            attachment_part.add_header('Content-Type', content_type)
            
            msg.attach(attachment_part)
            
        except Exception as e:
            logger.error(f"Failed to add attachment {attachment.get('filename', 'unknown')}: {str(e)}")
    
    def _send_via_smtp(self, msg: MIMEMultipart, to_emails: Union[str, List[str]]) -> Dict:
        """Send email via SMTP"""
        try:
            # Get organization-specific SMTP config if available
            smtp_config = self.smtp_config
            
            # Create SMTP connection
            with smtplib.SMTP(
                smtp_config['host'], 
                smtp_config['port'],
                timeout=smtp_config['timeout']
            ) as server:
                
                # Enable TLS if configured
                if smtp_config['use_tls']:
                    server.starttls()
                
                # Login if credentials provided
                if smtp_config['username'] and smtp_config['password']:
                    server.login(smtp_config['username'], smtp_config['password'])
                
                # Send email
                recipients = to_emails if isinstance(to_emails, list) else [to_emails]
                server.sendmail(msg['From'], recipients, msg.as_string())
                
                return {
                    'message_id': f"msg_{datetime.now().timestamp()}",
                    'recipients': recipients
                }
                
        except Exception as e:
            logger.error(f"SMTP sending failed: {str(e)}")
            raise
    
    def send_welcome_email(self, user_email: str, user_name: str, 
                         temporary_password: str, organization_name: str,
                         login_url: str, organization_id: Optional[str] = None) -> Dict:
        """Send welcome email to new organization admin"""
        context = {
            'user_name': user_name,
            'user_email': user_email,
            'temporary_password': temporary_password,
            'organization_name': organization_name,
            'login_url': login_url,
            'support_email': getattr(settings, 'SUPPORT_EMAIL', 'support@atsplatform.com')
        }
        
        return self.send_email(
            to_emails=user_email,
            subject=f"Welcome to {organization_name} - Your ATS Account is Ready",
            template_name='organization_welcome',
            context=context,
            organization_id=organization_id
        )
    
    def send_team_invitation(self, to_email: str, inviter_name: str, 
                           organization_name: str, role: str, invite_url: str,
                           organization_id: Optional[str] = None) -> Dict:
        """Send team invitation email"""
        context = {
            'inviter_name': inviter_name,
            'organization_name': organization_name,
            'role': role,
            'invite_url': invite_url,
            'support_email': getattr(settings, 'SUPPORT_EMAIL', 'support@atsplatform.com')
        }
        
        return self.send_email(
            to_emails=to_email,
            subject=f"You're invited to join {organization_name}",
            template_name='team_invitation',
            context=context,
            organization_id=organization_id
        )
    
    def send_application_confirmation(self, to_email: str, candidate_name: str,
                                job_title: str, company_name: str,
                                application_id: str, organization_id: Optional[str] = None) -> Dict:
        """Send application confirmation to candidate"""
        context = {
            'candidate_name': candidate_name,
            'job_title': job_title,
            'company_name': company_name,
            'application_id': application_id,
            'support_email': getattr(settings, 'SUPPORT_EMAIL', 'support@atsplatform.com')
        }
        
        return self.send_email(
            to_emails=to_email,
            subject=f"Application Received: {job_title} at {company_name}",
            template_name='application_confirmation',
            context=context,
            organization_id=organization_id
        )
    
    def send_interview_invitation(self, to_email: str, candidate_name: str,
                               job_title: str, company_name: str,
                               interview_datetime: str, interview_location: str,
                               organization_id: Optional[str] = None) -> Dict:
        """Send interview invitation email"""
        context = {
            'candidate_name': candidate_name,
            'job_title': job_title,
            'company_name': company_name,
            'interview_datetime': interview_datetime,
            'interview_location': interview_location,
            'support_email': getattr(settings, 'SUPPORT_EMAIL', 'support@atsplatform.com')
        }
        
        return self.send_email(
            to_emails=to_email,
            subject=f"Interview Invitation: {job_title} at {company_name}",
            template_name='interview_invitation',
            context=context,
            organization_id=organization_id
        )
    
    def send_offer_email(self, to_email: str, candidate_name: str,
                       job_title: str, company_name: str, offer_details: Dict,
                       organization_id: Optional[str] = None) -> Dict:
        """Send job offer email"""
        context = {
            'candidate_name': candidate_name,
            'job_title': job_title,
            'company_name': company_name,
            'offer_details': offer_details,
            'support_email': getattr(settings, 'SUPPORT_EMAIL', 'support@atsplatform.com')
        }
        
        return self.send_email(
            to_emails=to_email,
            subject=f"Job Offer: {job_title} at {company_name}",
            template_name='job_offer',
            context=context,
            organization_id=organization_id
        )
    
    def send_rejection_email(self, to_email: str, candidate_name: str,
                           job_title: str, company_name: str, reason: Optional[str] = None,
                           organization_id: Optional[str] = None) -> Dict:
        """Send rejection email"""
        context = {
            'candidate_name': candidate_name,
            'job_title': job_title,
            'company_name': company_name,
            'reason': reason,
            'support_email': getattr(settings, 'SUPPORT_EMAIL', 'support@atsplatform.com')
        }
        
        return self.send_email(
            to_emails=to_email,
            subject=f"Regarding your application for {job_title} at {company_name}",
            template_name='application_rejection',
            context=context,
            organization_id=organization_id
        )
    
    def send_password_reset(self, to_email: str, user_name: str, 
                          reset_url: str, organization_id: Optional[str] = None) -> Dict:
        """Send password reset email"""
        context = {
            'user_name': user_name,
            'reset_url': reset_url,
            'support_email': getattr(settings, 'SUPPORT_EMAIL', 'support@atsplatform.com')
        }
        
        return self.send_email(
            to_emails=to_email,
            subject="Password Reset Request",
            template_name='password_reset',
            context=context,
            organization_id=organization_id
        )
    
    def send_system_notification(self, to_emails: Union[str, List[str]], 
                              subject: str, message: str, 
                              notification_type: str = 'info',
                              organization_id: Optional[str] = None) -> Dict:
        """Send system notification email"""
        context = {
            'message': message,
            'notification_type': notification_type,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'support_email': getattr(settings, 'SUPPORT_EMAIL', 'support@atsplatform.com')
        }
        
        return self.send_email(
            to_emails=to_emails,
            subject=subject,
            template_name='system_notification',
            context=context,
            organization_id=organization_id
        )
    
    def _log_email_sent(self, to_emails: Union[str, List[str]], subject: str, result: Dict):
        """Log email sending activity"""
        try:
            from core.models import EmailLog
            
            EmailLog.objects.create(
                to_email=', '.join(to_emails) if isinstance(to_emails, list) else to_emails,
                subject=subject,
                status='sent' if result.get('success') else 'failed',
                message_id=result.get('message_id'),
                error_message=result.get('error'),
                sent_at=datetime.now()
            )
        except Exception as e:
            logger.error(f"Failed to log email: {str(e)}")
    
    def test_email_configuration(self, test_email: str) -> Dict:
        """Test email configuration"""
        try:
            context = {
                'test_email': test_email,
                'test_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'support_email': getattr(settings, 'SUPPORT_EMAIL', 'support@atsplatform.com')
            }
            
            result = self.send_email(
                to_emails=test_email,
                subject="ATS Platform - Email Configuration Test",
                template_name='email_test',
                context=context
            )
            
            return {
                'success': result.get('success', False),
                'message': 'Email configuration test ' + ('successful' if result.get('success') else 'failed'),
                'details': result
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f"Email configuration test failed: {str(e)}",
                'error': str(e)
            }


class EmailQueueService:
    """Email queue service for bulk email sending"""
    
    def __init__(self):
        self.email_service = EmailService()
        
    def queue_bulk_email(self, email_list: List[Dict]) -> Dict:
        """Queue multiple emails for sending"""
        try:
            from core.models import EmailQueue
            
            queued_emails = []
            for email_data in email_list:
                queued_email = EmailQueue.objects.create(
                    to_email=email_data['to_email'],
                    subject=email_data['subject'],
                    template_name=email_data.get('template_name'),
                    context=email_data.get('context', {}),
                    html_content=email_data.get('html_content'),
                    text_content=email_data.get('text_content'),
                    from_email=email_data.get('from_email'),
                    from_name=email_data.get('from_name'),
                    attachments=email_data.get('attachments', []),
                    priority=email_data.get('priority', 'normal'),
                    organization_id=email_data.get('organization_id'),
                    status='queued',
                    created_at=datetime.now()
                )
                queued_emails.append(str(queued_email.id))
            
            return {
                'success': True,
                'message': f'{len(queued_emails)} emails queued successfully',
                'queued_ids': queued_emails
            }
            
        except Exception as e:
            logger.error(f"Email queueing failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def process_queue(self, batch_size: int = 10) -> Dict:
        """Process queued emails"""
        try:
            from core.models import EmailQueue
            
            # Get pending emails
            pending_emails = EmailQueue.objects.filter(
                status='queued'
            ).order_by('priority', 'created_at')[:batch_size]
            
            processed_count = 0
            failed_count = 0
            
            for email in pending_emails:
                try:
                    # Send email
                    result = self.email_service.send_email(
                        to_emails=email.to_email,
                        subject=email.subject,
                        template_name=email.template_name,
                        context=email.context,
                        html_content=email.html_content,
                        text_content=email.text_content,
                        from_email=email.from_email,
                        from_name=email.from_name,
                        attachments=email.attachments,
                        organization_id=email.organization_id
                    )
                    
                    # Update queue status
                    if result.get('success'):
                        email.status = 'sent'
                        email.sent_at = datetime.now()
                        processed_count += 1
                    else:
                        email.status = 'failed'
                        email.error_message = result.get('error')
                        failed_count += 1
                    
                    email.save()
                    
                except Exception as e:
                    email.status = 'failed'
                    email.error_message = str(e)
                    email.save()
                    failed_count += 1
            
            return {
                'success': True,
                'message': f'Processed {processed_count + failed_count} emails',
                'processed': processed_count,
                'failed': failed_count
            }
            
        except Exception as e:
            logger.error(f"Email queue processing failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }


# Global email service instances
email_service = EmailService()
email_queue_service = EmailQueueService()
