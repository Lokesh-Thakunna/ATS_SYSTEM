from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth.models import User
from authentication.models import Organization, OrganizationSettings, UserProfile
from jobs.models import JobDescription, JobApplication, JobSkill


class JobApplicationAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.organization, _ = Organization.objects.get_or_create(name='Default Organization', slug='default')
        self.user = User.objects.create_user(username='candidate1', password='pass123', email='candidate@example.com')
        UserProfile.objects.create(user=self.user, role='candidate', organization=self.organization)
        self.job = JobDescription.objects.create(
            title='Test Job',
            description='Test desc',
            organization=self.organization,
        )

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
        self.assertEqual(JobApplication.objects.get(job=self.job).candidate.organization, self.organization)

    def test_cannot_apply_twice(self):
        self.client.force_authenticate(user=self.user)
        self.client.post(f'/api/jobs/{self.job.id}/apply/', {'cover_letter': 'test'}, format='multipart')
        response = self.client.post(f'/api/jobs/{self.job.id}/apply/', {'cover_letter': 'test2'}, format='multipart')
        self.assertEqual(response.status_code, 400)


class PublicJobBoardAccessTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.public_org = Organization.objects.create(name='Acme Hiring', slug='acme-hiring')
        self.private_org = Organization.objects.create(name='Stealth Org', slug='stealth-org')

        OrganizationSettings.objects.create(
            organization=self.public_org,
            allow_public_job_board=True,
            careers_page_title='Acme Careers',
        )
        OrganizationSettings.objects.create(
            organization=self.private_org,
            allow_public_job_board=False,
        )

        self.public_job = JobDescription.objects.create(
            title='Public Role',
            description='Visible role',
            organization=self.public_org,
            is_active=True,
        )
        self.private_job = JobDescription.objects.create(
            title='Private Role',
            description='Hidden role',
            organization=self.private_org,
            is_active=True,
        )

    def test_public_jobs_can_be_listed_by_organization_slug(self):
        response = self.client.get('/api/jobs/', {'organization_slug': 'acme-hiring'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], self.public_job.id)
        self.assertNotIn('embedding', response.data['results'][0])

    def test_public_jobs_can_be_filtered_by_skill_keyword(self):
        JobSkill.objects.create(job=self.public_job, skill='Django')

        response = self.client.get(
            '/api/jobs/',
            {
                'organization_slug': 'acme-hiring',
                'keyword': 'django',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], self.public_job.id)

    def test_private_jobs_are_hidden_from_public_job_board_requests(self):
        response = self.client.get('/api/jobs/', {'organization_slug': 'stealth-org'})

        self.assertEqual(response.status_code, 404)

    def test_private_job_detail_is_hidden_from_public_job_board_requests(self):
        response = self.client.get(
            f'/api/jobs/{self.private_job.id}/',
            {'organization_slug': 'stealth-org'},
        )

        self.assertEqual(response.status_code, 404)


class AuthenticatedCandidateJobBoardAccessTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.default_org, _ = Organization.objects.get_or_create(name='Default Organization', slug='default')
        self.public_org = Organization.objects.create(name='Public Org', slug='public-org')
        self.private_org = Organization.objects.create(name='Private Org', slug='private-org')

        OrganizationSettings.objects.create(
            organization=self.public_org,
            allow_public_job_board=True,
        )
        OrganizationSettings.objects.create(
            organization=self.private_org,
            allow_public_job_board=False,
        )

        self.candidate = User.objects.create_user(
            username='candidate@example.com',
            email='candidate@example.com',
            password='Candidate123',
        )
        UserProfile.objects.create(
            user=self.candidate,
            role=UserProfile.Role.CANDIDATE,
            organization=self.default_org,
        )

        self.own_org_job = JobDescription.objects.create(
            title='Default Org Role',
            description='Visible inside own tenant',
            organization=self.default_org,
            is_active=True,
        )
        self.public_job = JobDescription.objects.create(
            title='Public Backend Role',
            description='Visible outside the tenant',
            organization=self.public_org,
            is_active=True,
        )
        self.private_job = JobDescription.objects.create(
            title='Private Internal Role',
            description='Hidden outside the tenant',
            organization=self.private_org,
            is_active=True,
        )

    def test_authenticated_candidate_browses_jobs_from_all_organizations(self):
        self.client.force_authenticate(user=self.candidate)

        response = self.client.get('/api/jobs/')

        self.assertEqual(response.status_code, 200)
        returned_ids = {item['id'] for item in response.data['results']}
        self.assertIn(self.own_org_job.id, returned_ids)
        self.assertIn(self.public_job.id, returned_ids)
        self.assertIn(self.private_job.id, returned_ids)

    def test_authenticated_candidate_can_open_own_org_job_detail(self):
        self.client.force_authenticate(user=self.candidate)

        response = self.client.get(f'/api/jobs/{self.own_org_job.id}/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['id'], self.own_org_job.id)

    def test_authenticated_candidate_can_open_other_org_job_detail(self):
        self.client.force_authenticate(user=self.candidate)

        response = self.client.get(f'/api/jobs/{self.public_job.id}/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['id'], self.public_job.id)

    def test_authenticated_candidate_can_query_other_org_by_slug(self):
        self.client.force_authenticate(user=self.candidate)

        response = self.client.get('/api/jobs/', {'organization_slug': 'public-org'})

        self.assertEqual(response.status_code, 200)
        returned_ids = {item['id'] for item in response.data['results']}
        self.assertIn(self.public_job.id, returned_ids)
        self.assertNotIn(self.own_org_job.id, returned_ids)

    def test_authenticated_candidate_can_query_private_org_by_slug(self):
        self.client.force_authenticate(user=self.candidate)

        response = self.client.get('/api/jobs/', {'organization_slug': 'private-org'})

        self.assertEqual(response.status_code, 200)
        returned_ids = {item['id'] for item in response.data['results']}
        self.assertIn(self.private_job.id, returned_ids)
        self.assertNotIn(self.own_org_job.id, returned_ids)

    def test_authenticated_candidate_can_apply_to_other_org_job(self):
        self.client.force_authenticate(user=self.candidate)

        response = self.client.post(
            f'/api/jobs/{self.public_job.id}/apply/',
            {
                'full_name': 'Candidate One',
                'phone': '1234567890',
                'cover_letter': 'Interested in this role',
            },
            format='multipart',
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(
            JobApplication.objects.filter(
                job=self.public_job,
                candidate__user=self.candidate,
            ).exists()
        )

