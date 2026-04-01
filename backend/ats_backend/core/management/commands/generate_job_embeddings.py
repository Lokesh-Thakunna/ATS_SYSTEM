from django.core.management.base import BaseCommand
from jobs.models import JobDescription
from jobs.utils.embedding import generate_embedding


class Command(BaseCommand):
    help = 'Generate embeddings for all jobs that don\'t have them'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be processed without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write('DRY RUN MODE - No changes will be made')

        jobs_without_embeddings = JobDescription.objects.filter(embedding__isnull=True)

        if not jobs_without_embeddings:
            self.stdout.write('All jobs already have embeddings')
            return

        self.stdout.write(f'Found {jobs_without_embeddings.count()} jobs without embeddings')

        for job in jobs_without_embeddings:
            self.stdout.write(f'Processing job: {job.title}')

            if dry_run:
                self.stdout.write(f'  Would generate embedding for job {job.id}')
                continue

            try:
                embedding = generate_embedding(job.description)
                if embedding and len(embedding) > 0:
                    job.embedding = embedding
                    job.save()
                    self.stdout.write(
                        self.style.SUCCESS(f'  ✅ Generated embedding for job {job.id} (length: {len(embedding)})')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'  ⚠️ Failed to generate embedding for job {job.id}')
                    )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'  ❌ Error processing job {job.id}: {str(e)}')
                )

        self.stdout.write('Job embedding generation completed!')