"""
Authentication utility functions
"""

import logging
from typing import Optional
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist

from .models import UserProfile, Organization

User = get_user_model()
logger = logging.getLogger(__name__)


def get_user_role(user) -> Optional[str]:
    """
    Get user role from UserProfile
    """
    try:
        if not user or not user.is_authenticated:
            return None
        
        user_profile = UserProfile.objects.get(user=user)
        return user_profile.role
    except UserProfile.DoesNotExist:
        logger.warning(f"UserProfile not found for user: {user.id if user else 'None'}")
        return None
    except Exception as e:
        logger.error(f"Error getting user role: {str(e)}")
        return None


def get_user_organization(user) -> Optional[Organization]:
    """
    Get user's organization
    """
    try:
        if not user or not user.is_authenticated:
            return None
        
        user_profile = UserProfile.objects.get(user=user)
        return user_profile.organization
    except UserProfile.DoesNotExist:
        logger.warning(f"UserProfile not found for user: {user.id if user else 'None'}")
        return None
    except Exception as e:
        logger.error(f"Error getting user organization: {str(e)}")
        return None


def is_super_admin(user) -> bool:
    """
    Check if user is super admin
    """
    return get_user_role(user) == 'SUPER_ADMIN'


def is_org_admin(user) -> bool:
    """
    Check if user is organization admin
    """
    return get_user_role(user) == 'ORG_ADMIN'


def is_recruiter(user) -> bool:
    """
    Check if user is recruiter
    """
    return get_user_role(user) == 'RECRUITER'


def is_candidate(user) -> bool:
    """
    Check if user is candidate
    """
    return get_user_role(user) == 'CANDIDATE'


def user_has_organization_access(user, organization_id) -> bool:
    """
    Check if user has access to specific organization
    """
    try:
        if is_super_admin(user):
            return True
        
        user_org = get_user_organization(user)
        if user_org and str(user_org.id) == str(organization_id):
            return True
        
        return False
    except Exception as e:
        logger.error(f"Error checking organization access: {str(e)}")
        return False


def get_user_permissions(user) -> list:
    """
    Get user permissions based on role
    """
    role = get_user_role(user)
    
    permissions = {
        'SUPER_ADMIN': [
            'create_organization', 'delete_organization', 'view_all_organizations',
            'manage_users', 'view_analytics', 'system_settings'
        ],
        'ORG_ADMIN': [
            'manage_team', 'view_organization', 'edit_organization',
            'manage_jobs', 'view_analytics', 'team_settings'
        ],
        'RECRUITER': [
            'create_jobs', 'edit_jobs', 'view_applications',
            'schedule_interviews', 'view_candidates', 'job_analytics'
        ],
        'CANDIDATE': [
            'view_jobs', 'apply_jobs', 'edit_profile',
            'view_applications', 'upload_resume'
        ]
    }
    
    return permissions.get(role, [])


def can_user_access_resource(user, resource_type, resource_id) -> bool:
    """
    Check if user can access specific resource
    """
    try:
        if is_super_admin(user):
            return True
        
        role = get_user_role(user)
        user_org = get_user_organization(user)
        
        # Check resource ownership based on type
        if resource_type == 'job':
            from jobs.models import JobDescription
            job = JobDescription.objects.get(id=resource_id)
            return str(job.organization.id) == str(user_org.id) if user_org else False
        
        elif resource_type == 'application':
            from jobs.models import JobApplication
            application = JobApplication.objects.get(id=resource_id)
            job = application.job
            return str(job.organization.id) == str(user_org.id) if user_org else False
        
        elif resource_type == 'candidate':
            from candidates.models import Candidate
            candidate = Candidate.objects.get(id=resource_id)
            return str(candidate.organization.id) == str(user_org.id) if user_org else False
        
        return False
    except Exception as e:
        logger.error(f"Error checking resource access: {str(e)}")
        return False


def create_user_profile(user, role, organization=None) -> UserProfile:
    """
    Create UserProfile for user
    """
    try:
        profile, created = UserProfile.objects.get_or_create(
            user=user,
            defaults={
                'role': role,
                'organization': organization
            }
        )
        
        if not created:
            profile.role = role
            profile.organization = organization
            profile.save()
        
        return profile
    except Exception as e:
        logger.error(f"Error creating user profile: {str(e)}")
        raise


def update_user_role(user, new_role) -> bool:
    """
    Update user role
    """
    try:
        profile = UserProfile.objects.get(user=user)
        profile.role = new_role
        profile.save()
        return True
    except UserProfile.DoesNotExist:
        logger.error(f"UserProfile not found for user: {user.id}")
        return False
    except Exception as e:
        logger.error(f"Error updating user role: {str(e)}")
        return False


def get_organization_users(organization_id) -> list:
    """
    Get all users in organization
    """
    try:
        profiles = UserProfile.objects.filter(organization_id=organization_id)
        return [profile.user for profile in profiles]
    except Exception as e:
        logger.error(f"Error getting organization users: {str(e)}")
        return []


def validate_user_session(user) -> bool:
    """
    Validate user session
    """
    try:
        if not user or not user.is_authenticated:
            return False
        
        # Check if user is active
        if not user.is_active:
            return False
        
        # Check if user profile exists
        UserProfile.objects.get(user=user)
        return True
    except UserProfile.DoesNotExist:
        return False
    except Exception as e:
        logger.error(f"Error validating user session: {str(e)}")
        return False


def get_user_context(user) -> dict:
    """
    Get user context for templates and API responses
    """
    try:
        role = get_user_role(user)
        organization = get_user_organization(user)
        permissions = get_user_permissions(user)
        
        return {
            'user_id': str(user.id),
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': role,
            'organization_id': str(organization.id) if organization else None,
            'organization_name': organization.name if organization else None,
            'permissions': permissions,
            'is_authenticated': user.is_authenticated,
            'is_active': user.is_active
        }
    except Exception as e:
        logger.error(f"Error getting user context: {str(e)}")
        return {}
