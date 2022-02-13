from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status


CREATE_USER_URL = reverse('users:create')
CREATE_TOKEN_URL = reverse('users:auth')
ME_URL = reverse('users:me')


def create_user(**params):
    """Helper function to create users"""
    return get_user_model().objects.create_user(**params)


class PublicUserApiTests(TestCase):
    """Test public users API"""

    def setUp(self):
        self.client = APIClient()

    def test_create_valid_user_succeed(self):
        """Test creating users with valid data should succeed"""
        payload = {'email': 'gustavo@test.com', 'password': '123456', 'name': 'Gustavo'}
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user_exists = get_user_model().objects.get(**res.json())
        self.assertTrue(user_exists)
        self.assertNotIn('password', res.json())

    def test_create_existing_user_fails(self):
        """Test creating an existing user should fail"""
        payload = {'email': 'gustavo@test.com', 'password': '123456', 'name': 'Gustavo'}
        create_user(**payload)
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_user_with_short_password_fails(self):
        """Test user password must be at least 5 characters"""
        payload = {'email': 'gustavo@test.com', 'password': '123', 'name': 'Gustavo'}
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        user_exists = get_user_model().objects.filter(
            email=payload.get('email')
        ).exists()
        self.assertFalse(user_exists)
    
    def test_create_token_with_valid_credentials_succeed(self):
        """Test generating token with valid crecentials should succeed"""
        payload = {'email': 'gustavo@test.com', 'password': '123456'}
        create_user(**payload)
        res = self.client.post(CREATE_TOKEN_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('token', res.json())

    def test_create_token_with_invalid_credentials_fails(self):
        """Test generating token for invalid credentials should fail"""
        create_user(email='gustavo@test.com', password='123456')
        res = self.client.post(CREATE_TOKEN_URL, {'email': 'gustavo@test.com', 'password': 'wrong'})

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('token', res.json())

    def test_create_token_for_unexisting_user_fails(self):
        """Test generating token for an unexisting user should fail"""
        payload = {'email': 'gustavo@test.com', 'password': '123456'}
        res = self.client.post(CREATE_TOKEN_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('token', res.json())

    def test_create_token_with_missing_fields(self):
        """Test generating token without required fields should fail"""
        create_user(email='gustavo@test.com', password='123456')
        create_user(email='william@test.coom', password='123456')

        res1 = self.client.post(CREATE_TOKEN_URL, {'email': 'gustavo@test.com', 'password': ''})
        res2 = self.client.post(CREATE_TOKEN_URL, {'email': '', 'password': '123456'})

        self.assertEqual(res1.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(res2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('token', res1.json())
        self.assertNotIn('token', res2.json())

    def test_retrieve_user_unauthorized(self):
        """Test that authentication is required for getting users"""
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserApiTests(TestCase):
    """Test API requests that require authentication"""

    def setUp(self):
        self.user = create_user(
            email='gustavo@test.com',
            password='123456',
            name='Gustavo William'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_profile_success(self):
        """Test retrieving profile for logged in users should succeed"""
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.json(), {'name': self.user.name, 'email': self.user.email})

    def test_post_method_is_not_allowed(self):
        """Test that POST method is not allowed should fail"""
        res = self.client.post(ME_URL, {})

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_profile(self):
        payload = {'name': 'newname', 'password': 'newpassword'}
        res = self.client.patch(ME_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(res.json().get('name'), payload.get('name'))
        self.assertTrue(self.user.check_password(payload.get('password')))


