from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from authentication.models import UserProfile
from candidates.models import Candidate
from jobs.models import JobApplication, JobDescription
from resumes.models import Resume
from resumes.utils import build_resume_file_response


class ResumeAccessTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.candidate_user = User.objects.create_user(
            username='candidate@example.com',
            email='candidate@example.com',
            password='password123',
        )
        UserProfile.objects.create(user=self.candidate_user, role='candidate')

        self.recruiter_user = User.objects.create_user(
            username='recruiter@example.com',
            email='recruiter@example.com',
            password='password123',
        )
        UserProfile.objects.create(user=self.recruiter_user, role='recruiter')

        self.other_user = User.objects.create_user(
            username='other@example.com',
            email='other@example.com',
            password='password123',
        )
        UserProfile.objects.create(user=self.other_user, role='candidate')

        self.candidate = Candidate.objects.create(
            user=self.candidate_user,
            email=self.candidate_user.email,
            full_name='Candidate User',
        )
        self.resume = Resume.objects.create(
            candidate=self.candidate,
            file_name='resume.pdf',
            storage_backend=Resume.StorageBackend.SUPABASE,
            storage_path='resume.pdf',
            cloud_url='https://example.supabase.co/storage/v1/object/public/Candidate_resume/resume.pdf',
            mime_type='application/pdf',
            is_primary=True,
        )

    @patch('resumes.utils.supabase.storage.from_')
    def test_build_resume_file_response_streams_supabase_content(self, storage_from):
        storage_from.return_value.download.return_value = b'pdf-bytes'

        response = build_resume_file_response(self.resume)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(b''.join(response.streaming_content), b'pdf-bytes')
        storage_from.assert_called_once_with('Candidate_resume')
        storage_from.return_value.download.assert_called_once_with('resume.pdf')

    def test_build_resume_file_response_reads_local_file(self):
        with TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / 'resume.pdf'
            file_path.write_bytes(b'local-resume')

            self.resume.storage_backend = Resume.StorageBackend.LOCAL
            self.resume.storage_path = str(file_path)
            self.resume.save(update_fields=['storage_backend', 'storage_path'])

            response = build_resume_file_response(self.resume)

            self.assertEqual(response.status_code, 200)
            self.assertEqual(b''.join(response.streaming_content), b'local-resume')
            response.close()

    @patch('resumes.utils.supabase.storage.from_')
    def test_candidate_can_access_own_resume_file(self, storage_from):
        storage_from.return_value.download.return_value = b'candidate-resume'
        self.client.force_authenticate(user=self.candidate_user)

        response = self.client.get(f'/api/resumes/{self.resume.id}/file/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(b''.join(response.streaming_content), b'candidate-resume')

    @patch('resumes.utils.supabase.storage.from_')
    def test_recruiter_can_access_resume_for_own_job_applicant(self, storage_from):
        storage_from.return_value.download.return_value = b'recruiter-resume'
        job = JobDescription.objects.create(
            title='Backend Engineer',
            description='Build APIs',
            posted_by=self.recruiter_user,
        )
        JobApplication.objects.create(
            candidate=self.candidate,
            job=job,
            cover_letter='Interested',
        )
        self.client.force_authenticate(user=self.recruiter_user)

        response = self.client.get(f'/api/resumes/{self.resume.id}/file/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(b''.join(response.streaming_content), b'recruiter-resume')

    def test_unrelated_user_cannot_access_resume_file(self):
        self.client.force_authenticate(user=self.other_user)

        response = self.client.get(f'/api/resumes/{self.resume.id}/file/')

        self.assertEqual(response.status_code, 403)
