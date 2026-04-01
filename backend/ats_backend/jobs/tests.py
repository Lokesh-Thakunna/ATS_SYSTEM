from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth.models import User
from authentication.models import UserProfile
from jobs.models import JobDescription, JobApplication


class JobApplicationAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='candidate1', password='pass123', email='candidate@example.com')
        UserProfile.objects.create(user=self.user, role='candidate')
        self.job = JobDescription.objects.create(title='Test Job', description='Test desc')

    def test_candidate_can_apply_for_job(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            f'/api/jobs/{self.job.id}/apply/',
            {
                'full_name': 'Candidate One',
                'phone': '1234567890',
                'summary': 'Experienced test candidate',
                'total_experience_years': '2.5',
                'cover_letter': 'I am a good fit',
                'expected_salary': 50000,
                'available_from': '2026-04-01'
            },
            format='multipart'
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(JobApplication.objects.filter(candidate__email='candidate@example.com', job=self.job).exists())

    def test_cannot_apply_twice(self):
        self.client.force_authenticate(user=self.user)
        self.client.post(f'/api/jobs/{self.job.id}/apply/', {'cover_letter': 'test'}, format='multipart')
        response = self.client.post(f'/api/jobs/{self.job.id}/apply/', {'cover_letter': 'test2'}, format='multipart')
        self.assertEqual(response.status_code, 400)

