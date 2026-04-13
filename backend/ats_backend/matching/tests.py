from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from authentication.models import Organization, UserProfile
from candidates.models import Candidate
from jobs.models import JobApplication, JobDescription, JobSkill
from matching.utils import cosine_similarity, update_match_scores_for_resume
from resumes.models import Resume, Skill


class MatchingUtilityTestCase(TestCase):
    def setUp(self):
        self.default_org, _ = Organization.objects.get_or_create(name="Default Organization", slug="default")
        self.other_org = Organization.objects.create(name="Other Org", slug="other-org")

    def test_cosine_similarity(self):
        self.assertAlmostEqual(cosine_similarity([1.0, 0.0], [1.0, 0.0]), 1.0)

    def test_update_match_scores_for_resume_prioritizes_better_fit(self):
        candidate = Candidate.objects.create(
            organization=self.default_org,
            full_name="Test Candidate",
            email="test@example.com",
            total_experience_years=4,
        )
        resume = Resume.objects.create(
            candidate=candidate,
            organization=self.default_org,
            file_name="resume.pdf",
            cloud_url="http://x",
            raw_text="Python Django REST API backend engineer",
            embedding=[1.0, 0.0, 0.0],
            is_primary=True,
        )
        Skill.objects.create(resume=resume, skill_name="Python")
        Skill.objects.create(resume=resume, skill_name="Django")

        strong_job = JobDescription.objects.create(
            organization=self.default_org,
            title="Python Backend Developer",
            description="Build Django APIs",
            requirements="Need Python and Django experience",
            min_experience=3,
            embedding=[1.0, 0.0, 0.0],
        )
        weak_job = JobDescription.objects.create(
            organization=self.default_org,
            title="Java Engineer",
            description="Build Java services",
            requirements="Java and Spring Boot",
            min_experience=5,
            embedding=[0.0, 1.0, 0.0],
        )
        JobDescription.objects.create(
            organization=self.other_org,
            title="Hidden Cross Org Role",
            description="Should not be scored",
            requirements="Python",
            min_experience=3,
            embedding=[1.0, 0.0, 0.0],
        )
        JobSkill.objects.create(job=strong_job, skill="Python")
        JobSkill.objects.create(job=strong_job, skill="Django")
        JobSkill.objects.create(job=weak_job, skill="Java")

        matches = update_match_scores_for_resume(resume.id)

        self.assertGreaterEqual(len(matches), 2)
        self.assertEqual(matches[0]["job_id"], strong_job.id)
        self.assertGreater(matches[0]["score"], matches[1]["score"])
        self.assertEqual(matches[0]["components"]["recommendation"], "shortlist")
        matched_titles = {JobDescription.objects.get(id=item["job_id"]).title for item in matches}
        self.assertNotIn("Hidden Cross Org Role", matched_titles)


class RecruiterApplicantMatchingApiTestCase(APITestCase):
    def setUp(self):
        self.organization, _ = Organization.objects.get_or_create(name="Default Organization", slug="default")
        self.other_organization = Organization.objects.create(name="Other Org", slug="other-org")
        self.recruiter = User.objects.create_user(
            username="recruiter@example.com",
            email="recruiter@example.com",
            password="Recruiter123",
        )
        UserProfile.objects.create(
            user=self.recruiter,
            role=UserProfile.Role.RECRUITER,
            organization=self.organization,
        )

        self.other_recruiter = User.objects.create_user(
            username="other@example.com",
            email="other@example.com",
            password="Recruiter123",
        )
        UserProfile.objects.create(
            user=self.other_recruiter,
            role=UserProfile.Role.RECRUITER,
            organization=self.other_organization,
        )

        self.job = JobDescription.objects.create(
            posted_by=self.recruiter,
            organization=self.organization,
            title="Python Backend Developer",
            description="Build APIs with Python and Django",
            requirements="Strong Python and Django, 3 years experience",
            min_experience=3,
            embedding=[1.0, 0.0, 0.0],
        )
        JobSkill.objects.create(job=self.job, skill="Python")
        JobSkill.objects.create(job=self.job, skill="Django")

        self.other_job = JobDescription.objects.create(
            posted_by=self.other_recruiter,
            organization=self.other_organization,
            title="Other Recruiter Job",
            description="Should not be visible",
            embedding=[1.0, 0.0, 0.0],
        )

        self.strong_candidate = Candidate.objects.create(
            organization=self.organization,
            full_name="Strong Candidate",
            email="strong@example.com",
            total_experience_years=5,
            summary="Python Django backend engineer",
        )
        self.strong_resume = Resume.objects.create(
            candidate=self.strong_candidate,
            organization=self.organization,
            file_name="strong.pdf",
            cloud_url="http://x",
            raw_text="Python Django REST APIs backend engineer",
            embedding=[1.0, 0.0, 0.0],
            is_primary=True,
        )
        Skill.objects.create(resume=self.strong_resume, skill_name="Python")
        Skill.objects.create(resume=self.strong_resume, skill_name="Django")

        self.weak_candidate = Candidate.objects.create(
            organization=self.organization,
            full_name="Weak Candidate",
            email="weak@example.com",
            total_experience_years=1,
            summary="General office profile",
        )
        self.weak_resume = Resume.objects.create(
            candidate=self.weak_candidate,
            organization=self.organization,
            file_name="weak.pdf",
            cloud_url="http://x",
            raw_text="Excel reporting operations",
            embedding=[0.0, 1.0, 0.0],
            is_primary=True,
        )
        Skill.objects.create(resume=self.weak_resume, skill_name="Excel")

        self.non_applicant = Candidate.objects.create(
            organization=self.organization,
            full_name="Non Applicant",
            email="othercandidate@example.com",
            total_experience_years=6,
            summary="Python Django expert",
        )
        self.non_applicant_resume = Resume.objects.create(
            candidate=self.non_applicant,
            organization=self.organization,
            file_name="other.pdf",
            cloud_url="http://x",
            raw_text="Python Django architect",
            embedding=[1.0, 0.0, 0.0],
            is_primary=True,
        )
        Skill.objects.create(resume=self.non_applicant_resume, skill_name="Python")

        self.strong_application = JobApplication.objects.create(
            candidate=self.strong_candidate,
            job=self.job,
            cover_letter="I have strong Python and Django experience for this backend role.",
        )
        self.weak_application = JobApplication.objects.create(
            candidate=self.weak_candidate,
            job=self.job,
            cover_letter="I am interested in this job.",
        )

    def test_recruiter_ranking_only_returns_applied_candidates_for_owned_job(self):
        self.client.force_authenticate(user=self.recruiter)

        response = self.client.get(f"/api/matching/job/{self.job.id}/applicants/?top=5")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_applicants"], 2)
        self.assertEqual(len(response.data["matches"]), 2)
        self.assertEqual(response.data["matches"][0]["candidate"]["id"], self.strong_candidate.id)
        returned_ids = {item["candidate"]["id"] for item in response.data["matches"]}
        self.assertNotIn(self.non_applicant.id, returned_ids)

    def test_recruiter_cannot_access_other_recruiter_job_matching(self):
        self.client.force_authenticate(user=self.recruiter)

        response = self.client.get(f"/api/matching/job/{self.other_job.id}/applicants/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_shortlist_top_candidates_marks_only_top_n(self):
        self.client.force_authenticate(user=self.recruiter)

        response = self.client.post(
            f"/api/matching/job/{self.job.id}/shortlist/",
            {"top_n": 1},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.strong_application.refresh_from_db()
        self.weak_application.refresh_from_db()
        self.assertEqual(self.strong_application.status, JobApplication.Status.SHORTLISTED)
        self.assertEqual(self.weak_application.status, JobApplication.Status.APPLIED)

    def test_matching_payload_exposes_resume_access_url(self):
        self.client.force_authenticate(user=self.recruiter)

        response = self.client.get(f"/api/matching/job/{self.job.id}/applicants/?top=1")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["matches"][0]["candidate"]["resume_url"].startswith("http://testserver/api/resumes/"))

    def test_recruiter_can_update_owned_application_status(self):
        self.client.force_authenticate(user=self.recruiter)

        response = self.client.patch(
            f"/api/jobs/applications/{self.weak_application.id}/status/",
            {"status": "approved"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.weak_application.refresh_from_db()
        self.assertEqual(self.weak_application.status, JobApplication.Status.SHORTLISTED)


class ResumeAccessApiTestCase(APITestCase):
    def setUp(self):
        self.organization, _ = Organization.objects.get_or_create(name="Default Organization", slug="default")
        self.other_organization = Organization.objects.create(name="Other Org", slug="other-org")
        self.candidate_user = User.objects.create_user(
            username="resume-owner@example.com",
            email="resume-owner@example.com",
            password="Candidate123",
        )
        UserProfile.objects.create(
            user=self.candidate_user,
            role=UserProfile.Role.CANDIDATE,
            organization=self.organization,
        )

        self.recruiter = User.objects.create_user(
            username="resume-recruiter@example.com",
            email="resume-recruiter@example.com",
            password="Recruiter123",
        )
        UserProfile.objects.create(
            user=self.recruiter,
            role=UserProfile.Role.RECRUITER,
            organization=self.organization,
        )

        self.candidate = Candidate.objects.create(
            user=self.candidate_user,
            organization=self.organization,
            full_name="Resume Owner",
            email=self.candidate_user.email,
        )
        self.resume = Resume.objects.create(
            candidate=self.candidate,
            organization=self.organization,
            file_name="resume.pdf",
            cloud_url="https://files.example.com/resume.pdf",
            storage_backend=Resume.StorageBackend.SUPABASE,
            is_primary=True,
        )
        self.job = JobDescription.objects.create(
            posted_by=self.recruiter,
            organization=self.organization,
            title="Resume Access Job",
            description="Check resume access",
            embedding=[1.0, 0.0, 0.0],
        )
        JobApplication.objects.create(candidate=self.candidate, job=self.job)

        self.other_recruiter = User.objects.create_user(
            username="other-recruiter@example.com",
            email="other-recruiter@example.com",
            password="Recruiter123",
        )
        UserProfile.objects.create(
            user=self.other_recruiter,
            role=UserProfile.Role.RECRUITER,
            organization=self.other_organization,
        )

    def test_candidate_can_open_resume_file_endpoint(self):
        self.client.force_authenticate(user=self.candidate_user)

        response = self.client.get(f"/api/resumes/{self.resume.id}/file/")

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(response.url, self.resume.cloud_url)

    def test_recruiter_can_open_applicant_resume_file_endpoint(self):
        self.client.force_authenticate(user=self.recruiter)

        response = self.client.get(f"/api/resumes/{self.resume.id}/file/")

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(response.url, self.resume.cloud_url)

    def test_other_org_recruiter_cannot_open_resume_file_endpoint(self):
        self.client.force_authenticate(user=self.other_recruiter)

        response = self.client.get(f"/api/resumes/{self.resume.id}/file/")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
