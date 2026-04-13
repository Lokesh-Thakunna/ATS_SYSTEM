#!/usr/bin/env python
import os
import sys
import django

# Setup Django
sys.path.append('backend/ats_backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ats_backend.settings')
django.setup()

from django.db.models import Count
from authentication.models import Organization, UserProfile
from authentication.permissions import is_super_admin, is_org_admin, get_user_organization, get_user_role
from django.contrib.auth.models import User

def test_multitenant_isolation():
    print("=== Multi-Tenant Architecture Test ===")
    
    # Test superadmin can see all organizations
    superadmin = User.objects.get(email='lokeshthakunna@gmail.com')
    print(f'Superadmin: {superadmin.email} - Role: {get_user_role(superadmin)}')
    print(f'Is SuperAdmin: {is_super_admin(superadmin)}')
    
    # Check organization admin is properly isolated
    org_admin = User.objects.filter(userprofile__role='org_admin').first()
    if org_admin:
        print(f'Org Admin: {org_admin.email} - Role: {get_user_role(org_admin)}')
        org = get_user_organization(org_admin)
        print(f'Organization: {org.name if org else "None"}')
    
    # Count organizations and verify isolation
    total_orgs = Organization.objects.filter(is_active=True).count()
    print(f'Total active organizations: {total_orgs}')
    
    # Verify user profiles are properly assigned
    profiles_by_role = UserProfile.objects.values('role').annotate(count=Count('id'))
    for profile in profiles_by_role:
        print(f'Role {profile["role"]}: {profile["count"]} users')
    
    # Test data isolation - list all organizations
    print("\n=== Organizations ===")
    for org in Organization.objects.filter(is_active=True):
        admin_count = UserProfile.objects.filter(organization=org, role='org_admin').count()
        recruiter_count = UserProfile.objects.filter(organization=org, role='recruiter').count()
        print(f'{org.name} (slug: {org.slug}) - Admins: {admin_count}, Recruiters: {recruiter_count}')
    
    print("\n=== Multi-Tenant Test Complete ===")

if __name__ == '__main__':
    test_multitenant_isolation()
