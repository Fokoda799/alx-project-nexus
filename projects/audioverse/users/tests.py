from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

User = get_user_model()

class UserRegistrationTest(APITestCase):
    def setUp(self):
        self.client = APIClient()

    def test_user_registration(self):
        """Test user can register with valid data"""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'SecurePass123!',
            'password2': 'SecurePass123!'
        }
        response = self.client.post('/api/auth/users/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(User.objects.count(), 1)

    def test_registration_password_mismatch(self):
        """Test registration fails with mismatched passwords"""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'SecurePass123!',
            'password2': 'DifferentPass123!'
        }
        response = self.client.post('/api/auth/users/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_registration_duplicate_email(self):
        """Test registration fails with duplicate email"""
        User.objects.create_user(
            username='existing',
            email='test@example.com',
            password='pass123'
        )
        
        data = {
            'username': 'newuser',
            'email': 'test@example.com',
            'password': 'SecurePass123!',
            'password2': 'SecurePass123!'
        }
        response = self.client.post('/api/auth/users/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class UserAuthenticationTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_user_login(self):
        """Test user can login with correct credentials"""
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        response = self.client.post('/api/auth/token/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_login_wrong_password(self):
        """Test login fails with wrong password"""
        data = {
            'username': 'testuser',
            'password': 'wrongpassword'
        }
        response = self.client.post('/api/auth/token/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_user_profile(self):
        """Test authenticated user can get their profile"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/auth/users/profile/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser')
        self.assertEqual(response.data['email'], 'test@example.com')

    def test_unauthenticated_cannot_access_profile(self):
        """Test unauthenticated user cannot access profile"""
        response = self.client.get('/api/auth/users/profile/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_user_profile(self):
        """Test user can update their profile"""
        self.client.force_authenticate(user=self.user)
        data = {
            'bio': 'Updated bio'
        }
        response = self.client.patch('/api/auth/users/profile/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.user.refresh_from_db()
        self.assertEqual(self.user.bio, 'Updated bio')