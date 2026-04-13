#!/usr/bin/env python
"""
Script to check the current state of organizations and users in the database.
Run from: python manage.py shell < check_db_state.py
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ats_backend.settings')
sys.path.insert(0, '/c/Users/lt22c/OneDrive/Desktop/ats_project/backend/ats_backend')
django.setup()

from django.contrib.auth.models import User
from authentication.models import Organization, UserProfile, RecruiterProfile

print("=" * 80)
print("DATABASE STATE CHECK")
print("=" * 80)

# 1. Check Organizations
print("\n1. ORGANIZATIONS:")
print("-" * 80)
organizations = Organization.objects.all()
org_count = organizations.count()
print(f"Total Organizations: {org_count}")

if org_count > 0:
    for org in organizations:
        print(f"\n  Name: {org.name}")
        print(f"  Slug: {org.slug}")
        print(f"  Status: {org.registration_status}")
        print(f"  Active: {org.is_active}")
        print(f"  Admin Email: {org.admin_email}")
        print(f"  Created: {org.created_at}")
        print(f"  Registration Completed: {org.registration_completed_at}")
else:
    print("  No organizations found in the database.")

# 2. Check Recruiters/Users with Recruiter Role
print("\n2. RECRUITERS/USERS WITH RECRUITER ROLE:")
print("-" * 80)
recruiters = UserProfile.objects.filter(role=UserProfile.Role.RECRUITER)
recruiter_count = recruiters.count()
print(f"Total Recruiters: {recruiter_count}")

if recruiter_count > 0:
    for profile in recruiters:
        print(f"\n  User: {profile.user.username} ({profile.user.email})")
        print(f"  Role: {profile.role}")
        print(f"  Organization: {profile.organization.name if profile.organization else 'None'}")
        print(f"  Created: {profile.created_at}")
else:
    print("  No recruiters found in the database.")

# 3. Check all users and their roles
print("\n3. ALL USERS AND THEIR ROLES:")
print("-" * 80)
all_users = User.objects.all()
user_count = all_users.count()
print(f"Total Users: {user_count}")

if user_count > 0:
    for user in all_users:
        try:
            profile = UserProfile.objects.get(user=user)
            org_name = profile.organization.name if profile.organization else "None"
            print(f"\n  Username: {user.username}")
            print(f"  Email: {user.email}")
            print(f"  Role: {profile.role}")
            print(f"  Organization: {org_name}")
            print(f"  Active: {user.is_active}")
            print(f"  Created: {user.date_joined}")
        except UserProfile.DoesNotExist:
            print(f"\n  Username: {user.username} (No UserProfile - orphaned user)")
else:
    print("  No users found in the database.")

# 4. Check if there's a current user (if Django has a way to determine it)
print("\n4. ADMIN/SUPER_ADMIN USERS:")
print("-" * 80)
admins = UserProfile.objects.filter(role__in=[UserProfile.Role.ORG_ADMIN, UserProfile.Role.SUPER_ADMIN])
admin_count = admins.count()
print(f"Total Admins: {admin_count}")

if admin_count > 0:
    for profile in admins:
        print(f"\n  User: {profile.user.username} ({profile.user.email})")
        print(f"  Role: {profile.role}")
        print(f"  Organization: {profile.organization.name if profile.organization else 'None'}")
        print(f"  Created: {profile.created_at}")
else:
    print("  No admins found in the database.")

print("\n" + "=" * 80)
print("END OF DATABASE STATE CHECK")
print("=" * 80)
