from django.core.management.base import BaseCommand
from resumes.models import Resume
from jobs.utils.embedding import generate_embedding


class Command(BaseCommand):
    help = 'Generate embeddings for all resumes that don\'t have them'

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

        resumes_without_embeddings = Resume.objects.filter(embedding__isnull=True)

        if not resumes_without_embeddings:
            self.stdout.write('All resumes already have embeddings')
            return

        self.stdout.write(f'Found {resumes_without_embeddings.count()} resumes without embeddings')

        for resume in resumes_without_embeddings:
            self.stdout.write(f'Processing resume: {resume.file_name}')

            if dry_run:
                self.stdout.write(f'  Would generate embedding for resume {resume.id}')
                continue

            try:
                embedding = generate_embedding(resume.raw_text)
                if embedding and len(embedding) > 0:
                    resume.embedding = embedding
                    resume.save()
                    self.stdout.write(
                        self.style.SUCCESS(f'  ✅ Generated embedding for resume {resume.id} (length: {len(embedding)})')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'  ⚠️ Failed to generate embedding for resume {resume.id}')
                    )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'  ❌ Error processing resume {resume.id}: {str(e)}')
                )

        self.stdout.write('Resume embedding generation completed!')