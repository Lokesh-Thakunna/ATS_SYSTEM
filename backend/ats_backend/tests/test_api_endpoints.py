from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth.models import User
from authentication.models import UserProfile
from candidates.models import Candidate
from jobs.models import JobDescription, JobApplication
from resumes.models import Resume
from unittest.mock import patch


class APIEndpointsTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_register_and_login_candidate(self):
        # Register candidate
        response = self.client.post('/api/auth/register/', {
            'email': 'cand1@example.com',
            'password': 'password123',
            'full_name': 'Candidate One'
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['message'], 'Candidate registered')

        # Login candidate
        login_response = self.client.post('/api/auth/login/', {
            'email': 'cand1@example.com',
            'password': 'password123'
        }, format='json')
        self.assertEqual(login_response.status_code, 200)
        self.assertIn('access', login_response.data)
        self.assertEqual(login_response.data['role'], 'candidate')

        token = login_response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        # Get candidate profile
        profile_response = self.client.get('/api/candidates/profile/')
        self.assertEqual(profile_response.status_code, 200)
        self.assertEqual(profile_response.data['full_name'], 'Candidate One')

        # Update candidate profile
        response = self.client.put('/api/candidates/profile/update/', {
            'full_name': 'Candidate One Updated',
            'phone': '1234567890',
            'summary': 'Test summary',
            'total_experience_years': '2.5'
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['message'], 'Candidate profile updated')

    def test_admin_create_and_deactivate_recruiter(self):
        admin = User.objects.create_user(username='admin@example.com', email='admin@example.com', password='adminpass')
        UserProfile.objects.create(user=admin, role='admin')

        login_response = self.client.post('/api/auth/login/', {
            'email': 'admin@example.com',
            'password': 'adminpass'
        }, format='json')
        self.assertEqual(login_response.status_code, 200)
        admin_token = login_response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {admin_token}')

        response = self.client.post('/api/auth/recruiter/create/', {
            'email': 'recruit1@example.com',
            'password': 'recruitpass',
            'company_name': 'Example Co'
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['message'], 'Recruiter created')

        recruiter = User.objects.get(email='recruit1@example.com')
        self.assertTrue(recruiter.is_active)

        deactivate_response = self.client.patch(f'/api/auth/recruiter/deactivate/{recruiter.id}/')
        self.assertEqual(deactivate_response.status_code, 200)
        recruiter.refresh_from_db()
        self.assertFalse(recruiter.is_active)

    @patch('jobs.utils.embedding.generate_embedding', return_value=[0.1, 0.2, 0.3])
    def test_jobs_crud_and_apply(self, _):
        # create candidate user
        c_user = User.objects.create_user(username='cand2@example.com', email='cand2@example.com', password='password123')
        UserProfile.objects.create(user=c_user, role='candidate')
        Candidate.objects.create(full_name='Cand 2', email='cand2@example.com')

        # create recruiter user
        r_user = User.objects.create_user(username='recruit2@example.com', email='recruit2@example.com', password='recruitpass')
        UserProfile.objects.create(user=r_user, role='recruiter')

        # recruiter login
        login_resp = self.client.post('/api/auth/login/', {'email': 'recruit2@example.com', 'password': 'recruitpass'}, format='json')
        self.assertEqual(login_resp.status_code, 200)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login_resp.data['access']}")

        # create job
        create_job_resp = self.client.post('/api/jobs/create/', {
            'title': 'Data Engineer',
            'description': 'Fast API',
            'location': 'Remote',
            'salary_min': 50000,
            'salary_max': 80000,
            'min_experience': 1,
            'skills': ['Python', 'Django']
        }, format='json')
        self.assertEqual(create_job_resp.status_code, 201)
        job_id = create_job_resp.data['job_id']

        # get jobs
        job_list_resp = self.client.get('/api/jobs/')
        self.assertEqual(job_list_resp.status_code, 200)
        self.assertGreaterEqual(job_list_resp.data['count'], 1)

        # update job
        update_resp = self.client.put(f'/api/jobs/update/{job_id}/', {'title': 'Data Engineer Updated'}, format='json')
        self.assertEqual(update_resp.status_code, 200)
        self.assertEqual(update_resp.data['data']['title'], 'Data Engineer Updated')

        # candidate applies
        login_resp2 = self.client.post('/api/auth/login/', {'email': 'cand2@example.com', 'password': 'password123'}, format='json')
        self.assertEqual(login_resp2.status_code, 200)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login_resp2.data['access']}")

        apply_resp = self.client.post(f'/api/jobs/{job_id}/apply/', {
            'full_name': 'Cand 2',
            'phone': '999999999',
            'summary': 'Happy candidate',
            'total_experience_years': '3',
            'cover_letter': 'I can do it',
            'expected_salary': 60000,
            'available_from': '2026-05-01'
        }, format='multipart')
        self.assertEqual(apply_resp.status_code, 201)

        # check applications list
        apps_resp = self.client.get('/api/jobs/applications/')
        self.assertEqual(apps_resp.status_code, 200)
        self.assertEqual(apps_resp.data['count'], 1)

    def test_parse_resume_service(self):
        data = {
            'resume': ('sample.txt', b"Python developer\nExperience: 2 years", 'text/plain')
        }
        response = self.client.post('/api/services/parse/', data, format='multipart')
        self.assertEqual(response.status_code, 200)
        self.assertIn('data', response.data)

    def test_matching_endpoints(self):
        # setup candidate, job, resume with embeddings (skip I/O heavy parse)
        candidate = Candidate.objects.create(full_name='Match Cand', email='match@example.com')
        job = JobDescription.objects.create(title='ML Engineer', description='AI', embedding=[0.1, 0.2, 0.3])
        resume = Resume.objects.create(candidate=candidate, file_name='r.pdf', cloud_url='http://x', embedding=[0.1,0.2,0.3])

        match_resp = self.client.get(f'/api/matching/resume/{resume.id}/jobs/')
        self.assertEqual(match_resp.status_code, 200)
        self.assertIn('matches', match_resp.data)

        match_resp2 = self.client.get(f'/api/matching/candidate/{candidate.id}/jobs/')
        self.assertEqual(match_resp2.status_code, 200)
        self.assertIn('matches', match_resp2.data)
