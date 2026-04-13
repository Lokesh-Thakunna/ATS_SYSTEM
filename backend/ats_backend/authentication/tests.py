from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from candidates.models import Candidate
from authentication.models import Organization, OrganizationInvite, OrganizationSettings, RecruiterProfile, UserProfile

class CandidateRegistrationTest(APITestCase):
    def test_register_candidate_success(self):
        """Test successful candidate registration"""
        data = {
            'email': 'test@example.com',
            'password': 'Testpass123',
            'full_name': 'Test User',
            'phone': '1234567890',
            'summary': 'Test summary',
            'experience': 2
        }
        
        response = self.client.post('/api/auth/register/', data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['message'], 'Candidate registered successfully')
        
        # Check if user was created
        user = User.objects.get(email='test@example.com')
        self.assertEqual(user.username, 'test@example.com')
        
        # Check if profile was created
        profile = UserProfile.objects.get(user=user)
        self.assertEqual(profile.role, 'candidate')
        
        # Check if candidate was created
        candidate = Candidate.objects.get(email='test@example.com')
        self.assertEqual(candidate.full_name, 'Test User')
        self.assertEqual(user.userprofile.organization.slug, 'default')
        self.assertEqual(candidate.organization, user.userprofile.organization)
    
    def test_register_candidate_duplicate_email(self):
        """Test registration with duplicate email"""
        # Create existing user
        User.objects.create_user(username='existing@example.com', email='existing@example.com', password='pass')
        
        data = {
            'email': 'existing@example.com',
            'password': 'Testpass123',
            'full_name': 'Test User'
        }
        
        response = self.client.post('/api/auth/register/', data)
        
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertTrue('error' in response.data or 'detail' in response.data)
    
    def test_register_candidate_missing_fields(self):
        """Test registration with missing required fields"""
        data = {
            'email': 'test@example.com'
            # Missing password and full_name
        }
        
        response = self.client.post('/api/auth/register/', data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_register_recruiter_is_disabled_without_org_admin(self):
        data = {
            'email': 'recruiter@example.com',
            'password': 'Recruiter123',
            'full_name': 'Recruiter User',
            'organization_name': 'Acme Talent',
        }

        response = self.client.post('/api/auth/register/recruiter/', data)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('organization admin', response.data['error'].lower())
        self.assertFalse(User.objects.filter(email='recruiter@example.com').exists())
        self.assertFalse(Organization.objects.filter(slug='acme-talent').exists())

    def test_register_recruiter_is_disabled_even_with_slug_only(self):
        data = {
            'email': 'recruiter@example.com',
            'password': 'Recruiter123',
            'full_name': 'Recruiter User',
            'organization_slug': 'acme-talent',
        }

        response = self.client.post('/api/auth/register/recruiter/', data)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('error', response.data)


class PlatformOrganizationProvisioningTest(APITestCase):
    def setUp(self):
        self.platform_admin = User.objects.create_user(
            username='platform@ats.com',
            email='platform@ats.com',
            password='Adminpass123',
            is_staff=True,
        )
        self.client.force_authenticate(user=self.platform_admin)

    def test_platform_admin_can_create_organization_with_admin(self):
        response = self.client.post(
            '/api/auth/organizations/create/',
            {
                'organization_name': 'Northwind Talent',
                'organization_slug': 'northwind-talent',
                'admin_email': 'orgadmin@northwind.com',
                'admin_password': 'Adminpass123',
                'admin_full_name': 'Northwind Admin',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        organization = Organization.objects.get(slug='northwind-talent')
        admin_user = User.objects.get(email='orgadmin@northwind.com')
        self.assertEqual(admin_user.userprofile.organization, organization)
        self.assertEqual(admin_user.userprofile.role, UserProfile.Role.ORG_ADMIN)

    def test_non_platform_admin_cannot_create_organization(self):
        self.client.force_authenticate(user=None)
        org_admin = User.objects.create_user(
            username='orgadmin@acme.com',
            email='orgadmin@acme.com',
            password='Adminpass123',
        )
        organization = Organization.objects.create(name='Acme Hiring', slug='acme-hiring')
        UserProfile.objects.create(
            user=org_admin,
            role=UserProfile.Role.ORG_ADMIN,
            organization=organization,
        )
        self.client.force_authenticate(user=org_admin)

        response = self.client.post(
            '/api/auth/organizations/create/',
            {
                'organization_name': 'Blocked Org',
                'organization_slug': 'blocked-org',
                'admin_email': 'blocked@org.com',
                'admin_password': 'Adminpass123',
                'admin_full_name': 'Blocked Admin',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class OrganizationAdminSettingsTest(APITestCase):
    def setUp(self):
        self.organization = Organization.objects.create(name="Acme Hiring", slug="acme-hiring")
        self.other_organization = Organization.objects.create(name="Other Org", slug="other-org")

        self.admin_user = User.objects.create_user(
            username="admin@acme.com",
            email="admin@acme.com",
            password="Adminpass123",
            first_name="Acme",
            last_name="Admin",
        )
        UserProfile.objects.create(
            user=self.admin_user,
            role=UserProfile.Role.ORG_ADMIN,
            organization=self.organization,
        )

        self.same_org_recruiter = User.objects.create_user(
            username="recruiter@acme.com",
            email="recruiter@acme.com",
            password="Recruiter123",
            first_name="Same",
            last_name="Org",
        )
        UserProfile.objects.create(
            user=self.same_org_recruiter,
            role=UserProfile.Role.RECRUITER,
            organization=self.organization,
        )

        self.other_org_recruiter = User.objects.create_user(
            username="recruiter@other.com",
            email="recruiter@other.com",
            password="Recruiter123",
            first_name="Other",
            last_name="Org",
        )
        UserProfile.objects.create(
            user=self.other_org_recruiter,
            role=UserProfile.Role.RECRUITER,
            organization=self.other_organization,
        )

        self.client.force_authenticate(user=self.admin_user)

    def test_get_organization_settings_creates_default_settings(self):
        response = self.client.get("/api/auth/organization/settings/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["organization_name"], "Acme Hiring")
        self.assertEqual(response.data["organization_slug"], "acme-hiring")
        self.assertEqual(response.data["candidate_visibility"], "job_only")
        self.assertTrue(OrganizationSettings.objects.filter(organization=self.organization).exists())

    def test_patch_organization_settings_updates_org_and_settings(self):
        response = self.client.patch(
            "/api/auth/organization/settings/",
            {
                "organization_name": "Acme Talent Cloud",
                "domain": "acme.example.com",
                "timezone": "Asia/Kolkata",
                "brand_color": "#0f766e",
                "careers_page_title": "Acme Careers",
                "candidate_visibility": "private",
                "allow_public_job_board": False,
                "auto_publish_jobs": True,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.organization.refresh_from_db()
        settings_obj = OrganizationSettings.objects.get(organization=self.organization)

        self.assertEqual(self.organization.name, "Acme Talent Cloud")
        self.assertEqual(settings_obj.domain, "acme.example.com")
        self.assertEqual(settings_obj.timezone, "Asia/Kolkata")
        self.assertEqual(settings_obj.brand_color, "#0f766e")
        self.assertEqual(settings_obj.careers_page_title, "Acme Careers")
        self.assertEqual(settings_obj.candidate_visibility, "private")
        self.assertFalse(settings_obj.allow_public_job_board)
        self.assertTrue(settings_obj.auto_publish_jobs)

    def test_list_recruiters_is_scoped_to_current_organization(self):
        response = self.client.get("/api/auth/recruiters/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["organization"]["slug"], "acme-hiring")
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["email"], "recruiter@acme.com")

    def test_create_invite_is_scoped_to_admin_organization(self):
        response = self.client.post(
            "/api/auth/organization/invites/",
            {"email": "newhire@acme.com", "role": "recruiter"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        invite = OrganizationInvite.objects.get(email="newhire@acme.com")
        self.assertEqual(invite.organization, self.organization)
        self.assertEqual(invite.status, OrganizationInvite.Status.PENDING)

    def test_admin_created_recruiter_inherits_admin_organization(self):
        response = self.client.post(
            "/api/auth/recruiter/create/",
            {
                "email": "newrecruiter@acme.com",
                "password": "Recruiter123",
                "first_name": "New",
                "last_name": "Recruiter",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user = User.objects.get(email="newrecruiter@acme.com")
        self.assertEqual(user.userprofile.organization, self.organization)
        self.assertEqual(user.recruiterprofile.company_name, self.organization.name)

    def test_recruiter_cannot_create_recruiter_accounts(self):
        self.client.force_authenticate(user=self.same_org_recruiter)

        response = self.client.post(
            "/api/auth/recruiter/create/",
            {
                "email": "blocked@acme.com",
                "password": "Recruiter123",
                "first_name": "Blocked",
                "last_name": "Recruiter",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(User.objects.filter(email="blocked@acme.com").exists())

    def test_accept_invite_creates_recruiter_in_same_organization(self):
        invite = OrganizationInvite.objects.create(
            organization=self.organization,
            email="invitee@acme.com",
            invited_by=self.admin_user,
            role=UserProfile.Role.RECRUITER,
            token="accept-token-123",
        )

        self.client.force_authenticate(user=None)
        response = self.client.post(
            "/api/auth/organization/invites/accept/",
            {
                "token": invite.token,
                "full_name": "Invited Recruiter",
                "password": "InvitePass123",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email="invitee@acme.com")
        self.assertEqual(user.userprofile.role, UserProfile.Role.RECRUITER)
        self.assertEqual(user.userprofile.organization, self.organization)
        self.assertTrue(RecruiterProfile.objects.filter(user=user).exists())

        invite.refresh_from_db()
        self.assertEqual(invite.status, OrganizationInvite.Status.ACCEPTED)
        self.assertEqual(invite.accepted_by, user)

    def test_revoke_invite_blocks_acceptance(self):
        invite = OrganizationInvite.objects.create(
            organization=self.organization,
            email="blocked@acme.com",
            invited_by=self.admin_user,
            role=UserProfile.Role.RECRUITER,
            token="blocked-token-123",
        )

        revoke_response = self.client.post(f"/api/auth/organization/invites/{invite.id}/revoke/")
        self.assertEqual(revoke_response.status_code, status.HTTP_200_OK)

        self.client.force_authenticate(user=None)
        accept_response = self.client.post(
            "/api/auth/organization/invites/accept/",
            {
                "token": invite.token,
                "full_name": "Blocked Recruiter",
                "password": "InvitePass123",
            },
            format="json",
        )

        self.assertEqual(accept_response.status_code, status.HTTP_409_CONFLICT)


class PublicOrganizationProfileTest(APITestCase):
    def setUp(self):
        self.organization = Organization.objects.create(name="Acme Hiring", slug="acme-hiring")
        OrganizationSettings.objects.create(
            organization=self.organization,
            brand_color="#0f766e",
            careers_page_title="Build with Acme",
            company_logo_url="https://example.com/logo.png",
            allow_public_job_board=True,
        )

    def test_public_organization_profile_returns_branding_and_job_count(self):
        from jobs.models import JobDescription

        JobDescription.objects.create(
            title="Backend Engineer",
            description="Build APIs",
            organization=self.organization,
            is_active=True,
        )

        response = self.client.get("/api/auth/organization/public/acme-hiring/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["slug"], "acme-hiring")
        self.assertEqual(response.data["brand_color"], "#0f766e")
        self.assertEqual(response.data["careers_page_title"], "Build with Acme")
        self.assertEqual(response.data["open_jobs_count"], 1)

    def test_public_organization_profile_hides_private_job_boards(self):
        settings_obj = OrganizationSettings.objects.get(organization=self.organization)
        settings_obj.allow_public_job_board = False
        settings_obj.save(update_fields=["allow_public_job_board", "updated_at"])

        response = self.client.get("/api/auth/organization/public/acme-hiring/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
