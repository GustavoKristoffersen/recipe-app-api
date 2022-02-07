from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status


CREATE_USER_URL = reverse('user:create')


def create_user(**params):
    """Helper function to create users"""
    return get_user_model().objects.create_user(**params)


class PublicUserApiTests(TestCase):
    """Test public users API"""

    def setUp(self):
        self.client = APIClient()

    def test_create_valid_user_succeed(self):
        """Test creating users with valid data should succeed"""
        payload = {
            'email': 'gustavo@test.com',
            'password': '123456',
            'name': 'Gustavo',
        }
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user_exists = get_user_model().objects.get(**res.json())
        self.assertTrue(user_exists)
        self.assertNotIn('password', res.json())

    def test_create_existing_user_fails(self):
        """Test creating an existing user should fail"""
        payload = {'email': 'gustavo@test.com', 'password': '123456'}
        create_user(**payload)
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_user_with_short_password_fails(self):
        """Test user password must be at least 5 characters"""
        payload = {'email': 'gustavo@test.com', 'password': '123'}
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        user_exists = get_user_model().objects.filter(
            email=payload.get('email')
        ).exists()
        self.assertFalse(user_exists)


