import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ats_backend.settings')
django.setup()

from jobs.models import JobDescription, JobSkill, JobApplication
from authentication.models import Organization

# Check database state
job_count = JobDescription.objects.count()
org_count = Organization.objects.count()
app_count = JobApplication.objects.count()

print(f"Total Jobs: {job_count}")
print(f"Total Organizations: {org_count}")
print(f"Total Applications: {app_count}")

# List all organizations
orgs = Organization.objects.all()
for org in orgs:
    jobs_in_org = JobDescription.objects.filter(organization=org).count()
    print(f"  - {org.name}: {jobs_in_org} jobs")

# List all jobs
if job_count > 0:
    jobs = JobDescription.objects.all()[:5]
    print("\nSample Jobs:")
    for job in jobs:
        print(f"  - {job.title} (ID: {job.id}, Org: {job.organization.name})")
else:
    print("\nNo jobs found in database")
