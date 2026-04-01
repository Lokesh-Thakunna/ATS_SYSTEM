from django.core.management.base import BaseCommand
from django.db import transaction
from jobs.models import JobDescription
from resumes.models import Resume


class Command(BaseCommand):
    help = 'Clean up invalid embeddings (empty lists) in the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be cleaned without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write('DRY RUN MODE - No changes will be made\n')

        self.stdout.write('Starting embedding cleanup...\n')

        # Clean JobDescription embeddings
        self.stdout.write('Checking JobDescription embeddings...')
        jobs_to_fix = []
        for job in JobDescription.objects.exclude(embedding__isnull=True):
            try:
                # Handle different embedding formats
                if job.embedding is None:
                    continue
                elif hasattr(job.embedding, '__len__') and len(job.embedding) == 0:
                    jobs_to_fix.append(job.id)
                elif job.embedding == []:
                    jobs_to_fix.append(job.id)
            except (ValueError, TypeError):
                # If there's any comparison issue, assume it's invalid
                jobs_to_fix.append(job.id)
        
        if jobs_to_fix:
            self.stdout.write(f'Found {len(jobs_to_fix)} JobDescription records with empty embeddings')
            if not dry_run:
                JobDescription.objects.filter(id__in=jobs_to_fix).update(embedding=None)
                self.stdout.write(f'Fixed {len(jobs_to_fix)} JobDescription records')
        else:
            self.stdout.write('No invalid JobDescription embeddings found')

        # Clean Resume embeddings
        self.stdout.write('\nChecking Resume embeddings...')
        resumes_to_fix = []
        for resume in Resume.objects.exclude(embedding__isnull=True):
            try:
                # Handle different embedding formats
                if resume.embedding is None:
                    continue
                elif hasattr(resume.embedding, '__len__') and len(resume.embedding) == 0:
                    resumes_to_fix.append(resume.id)
                elif resume.embedding == []:
                    resumes_to_fix.append(resume.id)
            except (ValueError, TypeError):
                # If there's any comparison issue, assume it's invalid
                resumes_to_fix.append(resume.id)
        
        if resumes_to_fix:
            self.stdout.write(f'Found {len(resumes_to_fix)} Resume records with empty embeddings')
            if not dry_run:
                Resume.objects.filter(id__in=resumes_to_fix).update(embedding=None)
                self.stdout.write(f'Fixed {len(resumes_to_fix)} Resume records')
        else:
            self.stdout.write('No invalid Resume embeddings found')

        # Check for zero-length vectors
        self.stdout.write('\nChecking for zero-length vectors...')

        jobs_zero_length = []
        resumes_zero_length = []

        for job in JobDescription.objects.exclude(embedding__isnull=True):
            if job.embedding and len(job.embedding) == 0:
                jobs_zero_length.append(job.id)

        for resume in Resume.objects.exclude(embedding__isnull=True):
            if resume.embedding and len(resume.embedding) == 0:
                resumes_zero_length.append(resume.id)

        if jobs_zero_length:
            self.stdout.write(f'Found {len(jobs_zero_length)} JobDescription records with zero-length vectors')
            if not dry_run:
                JobDescription.objects.filter(id__in=jobs_zero_length).update(embedding=None)
                self.stdout.write(f'Fixed {len(jobs_zero_length)} JobDescription records')

        if resumes_zero_length:
            self.stdout.write(f'Found {len(resumes_zero_length)} Resume records with zero-length vectors')
            if not dry_run:
                Resume.objects.filter(id__in=resumes_zero_length).update(embedding=None)
                self.stdout.write(f'Fixed {len(resumes_zero_length)} Resume records')

        self.stdout.write('\nEmbedding cleanup completed!')

        if dry_run:
            self.stdout.write('\nThis was a dry run. Run without --dry-run to apply changes.')