#!/usr/bin/env python
import os
import sys
import django
import requests

# Setup Django
sys.path.append('backend/ats_backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ats_backend.settings')
django.setup()

from django.contrib.auth.models import User
from jobs.models import JobDescription
from authentication.models import UserProfile

def test_fixed_job_deletion():
    print("=== Testing Fixed Job Deletion ===")
    
    # Get recruiter user
    recruiter = User.objects.filter(userprofile__role='recruiter').first()
    if not recruiter:
        print("No recruiter found!")
        return
    
    print(f"Testing with recruiter: {recruiter.email}")
    
    # Get recruiter's job
    job = JobDescription.objects.filter(posted_by=recruiter).first()
    if not job:
        print("No jobs found for recruiter!")
        return
    
    print(f"Found job: {job.title} (ID: {job.id})")
    
    # Test API endpoint
    base_url = "http://localhost:8000/api"
    
    # First, login to get token
    login_data = {
        "email": recruiter.email,
        "password": "demo123"  # Default password for testing
    }
    
    try:
        print("Attempting login...")
        login_response = requests.post(f"{base_url}/auth/login/", json=login_data)
        if login_response.status_code == 200:
            token_data = login_response.json()
            token = token_data.get('access')
            print("✅ Login successful!")
            
            # Test job deletion with FIXED endpoint
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            print(f"Attempting to delete job {job.id} using CORRECT endpoint...")
            delete_response = requests.delete(f"{base_url}/jobs/delete/{job.id}/", headers=headers)
            
            print(f"Delete response status: {delete_response.status_code}")
            print(f"Delete response: {delete_response.text}")
            
            if delete_response.status_code == 204:
                print("✅ Job deletion successful with FIXED endpoint!")
            elif delete_response.status_code == 404:
                print("❌ Job not found or access denied")
            else:
                print("❌ Job deletion failed!")
        else:
            print(f"❌ Login failed: {login_response.text}")
            
    except Exception as e:
        print(f"❌ Error during testing: {e}")

if __name__ == '__main__':
    test_fixed_job_deletion()
