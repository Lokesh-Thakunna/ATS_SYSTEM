from django.core.management.base import BaseCommand
from jobs.models import JobDescription, JobApplication
from authentication.models import Organization


class Command(BaseCommand):
    help = 'Check database state for jobs'

    def handle(self, *args, **options):
        job_count = JobDescription.objects.count()
        org_count = Organization.objects.count()
        app_count = JobApplication.objects.count()

        self.stdout.write(f"Total Jobs: {job_count}")
        self.stdout.write(f"Total Organizations: {org_count}")
        self.stdout.write(f"Total Applications: {app_count}")

        orgs = Organization.objects.all()
        for org in orgs:
            jobs_in_org = JobDescription.objects.filter(organization=org).count()
            self.stdout.write(f"  - {org.name}: {jobs_in_org} jobs")

        if job_count > 0:
            jobs = JobDescription.objects.all()[:5]
            self.stdout.write("\nSample Jobs:")
            for job in jobs:
                self.stdout.write(f"  - {job.title} (ID: {job.id}, Org: {job.organization.name})")
        else:
            self.stdout.write("\nNo jobs found in database")
