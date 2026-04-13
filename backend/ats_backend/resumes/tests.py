from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from authentication.models import Organization, UserProfile
from candidates.models import Candidate
from resumes.models import Resume


@override_settings(RESUME_PROCESSING_MODE="sync")
class ResumeUploadApiTestCase(TestCase):
    PDF_BYTES = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n<<>>\n%%EOF"

    def setUp(self):
        self.client = APIClient()
        self.organization, _ = Organization.objects.get_or_create(name="Default Organization", slug="default")
        self.user = User.objects.create_user(
            username="candidate@example.com",
            email="candidate@example.com",
            password="Candidate123",
        )
        UserProfile.objects.create(
            user=self.user,
            role=UserProfile.Role.CANDIDATE,
            organization=self.organization,
        )
        self.candidate = Candidate.objects.create(
            user=self.user,
            organization=self.organization,
            full_name="Candidate Example",
            email=self.user.email,
        )

    def test_resume_upload_returns_success_with_integrity_checksum(self):
        self.client.force_authenticate(user=self.user)
        resume_file = SimpleUploadedFile(
            "resume.pdf",
            self.PDF_BYTES,
            content_type="application/pdf",
        )

        response = self.client.post("/api/resumes/upload/", {"resume": resume_file}, format="multipart")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["processing_mode"], "sync")
        self.assertTrue(response.data["checksum_sha256"])
        resume = Resume.objects.get(id=response.data["resume_id"])
        self.assertEqual(resume.organization, self.organization)
        self.assertIn(
            resume.parsing_status,
            [Resume.ParsingStatus.COMPLETED, Resume.ParsingStatus.FAILED],
        )

    def test_duplicate_resume_upload_returns_existing_resume(self):
        self.client.force_authenticate(user=self.user)

        first_response = self.client.post(
            "/api/resumes/upload/",
            {"resume": SimpleUploadedFile("resume.pdf", self.PDF_BYTES, content_type="application/pdf")},
            format="multipart",
        )
        second_response = self.client.post(
            "/api/resumes/upload/",
            {"resume": SimpleUploadedFile("resume.pdf", self.PDF_BYTES, content_type="application/pdf")},
            format="multipart",
        )

        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(second_response.status_code, 200)
        self.assertEqual(second_response.data["message"], "Resume already uploaded")
        self.assertEqual(first_response.data["resume_id"], second_response.data["resume_id"])
