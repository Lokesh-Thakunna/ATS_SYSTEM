from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from candidates.models import Candidate
from authentication.models import UserProfile

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
