from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from authentication.models import UserProfile, Organization
from jobs.models import JobDescription, JobSkill
import uuid


class Command(BaseCommand):
    help = 'Seeds the database with sample recruiters and jobs'

    def handle(self, *args, **options):
        # Get or create the Default Organization
        org, org_created = Organization.objects.get_or_create(
            slug='default',
            defaults={
                'name': 'Default Organization',
                'registration_status': Organization.RegistrationStatus.COMPLETED,
                'is_active': True,
            }
        )

        if org_created:
            self.stdout.write(self.style.SUCCESS(f'✓ Created organization: {org.name}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'✓ Using existing organization: {org.name}'))

        # Create sample recruiters
        recruiters = []
        recruiter_emails = [
            ('recruiter1@example.com', 'Recruiter One'),
            ('recruiter2@example.com', 'Recruiter Two'),
        ]

        for email, full_name in recruiter_emails:
            user, user_created = User.objects.get_or_create(
                username=email,
                defaults={
                    'email': email,
                    'first_name': full_name.split()[0],
                    'last_name': ' '.join(full_name.split()[1:]),
                    'is_active': True,
                }
            )

            profile, profile_created = UserProfile.objects.get_or_create(
                user=user,
                defaults={
                    'organization': org,
                    'role': UserProfile.Role.RECRUITER,
                }
            )

            if user_created or profile_created:
                # Set password
                user.set_password('recruiterpass123')
                user.save()
                self.stdout.write(self.style.SUCCESS(f'✓ Created recruiter: {email}'))
            else:
                self.stdout.write(self.style.WARNING(f'✓ Recruiter already exists: {email}'))

            recruiters.append(user)

        # Sample jobs data
        jobs_data = [
            {
                'title': 'Senior Python Developer',
                'company': 'TechCorp Solutions',
                'description': 'We are looking for an experienced Python developer to join our backend team. You will work on scalable microservices and contribute to our platform.',
                'requirements': '5+ years of Python experience, Django/FastAPI knowledge, PostgreSQL expertise',
                'location': 'Remote',
                'type': 'FULL_TIME',
                'salary_min': 80000,
                'salary_max': 120000,
                'min_experience': 5,
                'skills': ['Python', 'Django', 'PostgreSQL', 'Docker', 'REST APIs'],
            },
            {
                'title': 'Full Stack React Developer',
                'company': 'WebDev Inc',
                'description': 'Join our dynamic team to build modern web applications. You will work with React, Node.js, and cloud technologies.',
                'requirements': '3+ years of React experience, Node.js knowledge, Git proficiency',
                'location': 'Remote',
                'type': 'FULL_TIME',
                'salary_min': 70000,
                'salary_max': 110000,
                'min_experience': 3,
                'skills': ['React', 'Node.js', 'JavaScript', 'MongoDB', 'AWS'],
            },
            {
                'title': 'Data Scientist',
                'company': 'AI Innovations',
                'description': 'Help us build AI-powered solutions. Work with Python, machine learning frameworks, and big data technologies.',
                'requirements': '3+ years of ML experience, Python proficiency, TensorFlow/PyTorch knowledge',
                'location': 'Hybrid',
                'type': 'FULL_TIME',
                'salary_min': 90000,
                'salary_max': 130000,
                'min_experience': 3,
                'skills': ['Python', 'Machine Learning', 'TensorFlow', 'SQL', 'Statistics'],
            },
            {
                'title': 'Frontend Developer - React',
                'company': 'Creative Studio',
                'description': 'Design and develop beautiful user interfaces using React. Collaborate with designers and backend developers.',
                'requirements': '2+ years of React experience, CSS/SCSS knowledge, responsive design experience',
                'location': 'Remote',
                'type': 'FULL_TIME',
                'salary_min': 60000,
                'salary_max': 90000,
                'min_experience': 2,
                'skills': ['React', 'JavaScript', 'CSS', 'Tailwind CSS', 'UI/UX'],
            },
            {
                'title': 'DevOps Engineer',
                'company': 'CloudOps Pro',
                'description': 'Manage infrastructure, deployment pipelines, and cloud resources. Work with Kubernetes, Docker, and CI/CD.',
                'requirements': '4+ years of DevOps experience, AWS/GCP knowledge, Kubernetes expertise',
                'location': 'Remote',
                'type': 'FULL_TIME',
                'salary_min': 85000,
                'salary_max': 125000,
                'min_experience': 4,
                'skills': ['Docker', 'Kubernetes', 'AWS', 'CI/CD', 'Linux'],
            },
            {
                'title': 'Product Manager',
                'company': 'StartUp Hub',
                'description': 'Lead product strategy and roadmap development. Work cross-functionally with engineering and design teams.',
                'requirements': '3+ years of product management experience, agile methodology knowledge',
                'location': 'Hybrid',
                'type': 'FULL_TIME',
                'salary_min': 100000,
                'salary_max': 140000,
                'min_experience': 3,
                'skills': ['Product Strategy', 'Agile', 'Analytics', 'User Research', 'Communication'],
            },
        ]

        # Create jobs
        created_count = 0
        for idx, job_data in enumerate(jobs_data):
            recruiter = recruiters[idx % len(recruiters)]
            skills = job_data.pop('skills', [])

            job, job_created = JobDescription.objects.get_or_create(
                title=job_data['title'],
                posted_by=recruiter,
                organization=org,
                defaults={
                    **job_data,
                    'embedding': None,  # Skip embedding generation for speed
                    'is_active': True,
                }
            )

            if job_created:
                # Add skills
                for skill_name in skills:
                    JobSkill.objects.get_or_create(
                        job=job,
                        skill=skill_name,
                    )
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'✓ Created job: {job.title}'))
            else:
                self.stdout.write(self.style.WARNING(f'✓ Job already exists: {job.title}'))

        self.stdout.write(self.style.SUCCESS(f'\n✓ Completed! Created {created_count} jobs'))
