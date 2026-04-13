import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ats_backend.settings')
django.setup()

from django.contrib.auth.models import User
from authentication.models import UserProfile, Organization
from jobs.models import JobDescription, JobSkill

# Get or create organization
org, _ = Organization.objects.get_or_create(
    slug='default',
    defaults={'name': 'Default Organization', 'is_active': True}
)
print(f'✓ Organization: {org.name}')

# Create recruiters
recruiters = []
for i, (email, name) in enumerate([('recruiter1@example.com', 'Recruiter One'), ('recruiter2@example.com', 'Recruiter Two')]):
    user, user_created = User.objects.get_or_create(
        username=email,
        defaults={'email': email, 'first_name': name.split()[0], 'last_name': ' '.join(name.split()[1:]), 'is_active': True}
    )
    profile, _ = UserProfile.objects.get_or_create(
        user=user,
        defaults={'organization': org, 'role': UserProfile.Role.RECRUITER}
    )
    recruiters.append(user)
    print(f'✓ Recruiter: {email}')

# Create sample jobs
jobs_data = [
   {'title': 'Senior Python Developer', 'company': 'TechCorp', 'description': 'Build scalable microservices', 'location': 'Remote', 'job_type': 'FULL_TIME', 'salary_min': 80000, 'salary_max': 120000, 'min_experience': 5, 'requirements': '', 'skills': ['Python', 'Django', 'PostgreSQL']},
    {'title': 'Full Stack React Developer', 'company': 'WebDev Inc', 'description': 'Modern web applications', 'location': 'Remote', 'job_type': 'FULL_TIME', 'salary_min': 70000, 'salary_max': 110000, 'min_experience': 3, 'requirements': '', 'skills': ['React', 'Node.js', 'MongoDB']},
    {'title': 'Data Scientist', 'company': 'AI Innovations', 'description': 'AI-powered solutions', 'location': 'Hybrid', 'job_type': 'FULL_TIME', 'salary_min': 90000, 'salary_max': 130000, 'min_experience': 3, 'requirements': '', 'skills': ['Python', 'ML', 'TensorFlow']},
    {'title': 'DevOps Engineer', 'company': 'CloudOps Pro', 'description': 'Manage infrastructure and deployment', 'location': 'Remote', 'job_type': 'FULL_TIME', 'salary_min': 85000, 'salary_max': 125000, 'min_experience': 4, 'requirements': '', 'skills': ['Docker', 'Kubernetes', 'AWS', 'CI/CD']},
    {'title': 'Frontend Developer - React', 'company': 'Creative Studio', 'description': 'Design beautiful user interfaces', 'location': 'Remote', 'job_type': 'FULL_TIME', 'salary_min': 60000, 'salary_max': 90000, 'min_experience': 2, 'requirements': '', 'skills': ['React', 'JavaScript', 'CSS', 'Tailwind CSS']},
]

for idx, job_data in enumerate(jobs_data):
    recruiter = recruiters[idx % len(recruiters)]
    skills = job_data.pop('skills', [])
    job, created = JobDescription.objects.get_or_create(
        title=job_data['title'],
        posted_by=recruiter,
        organization=org,
        defaults={**job_data, 'is_active': True, 'embedding': None}
    )
    if created:
        for skill in skills:
            JobSkill.objects.get_or_create(job=job, skill=skill)
        print(f'✓ Job: {job.title}')

print('✓ Seed completed successfully!')
