from django.test import TestCase
from django.contrib.auth import get_user_model

class ModelTests(TestCase):

    def test_create_user_with_email_successful(self):
        """
            Test creating a new user with an email. Should succeed.
        """
        email = "test@gmail.com"
        password = "123456789"

        UserModel = get_user_model()
        user = UserModel.objects.create_user(
            email=email,
            password=password
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalised(self):
        """
            Test the email for a new user is normalised.
        """
        email = "test@GMAIL.COM"
        UserModel = get_user_model()
        user = UserModel.objects.create_user(
            email=email,
            password='123456789',
        )

        self.assertEqual(user.email, email.lower())

    
    def test_new_user_invalid_email(self):
        """
            Test creating user with no email. Should fail.
        """
        with self.assertRaises(ValueError):
            UserModel = get_user_model()
            UserModel.objects.create_user(
                email=None,
                password='123456789'
            )

    def test_create_new_superuser(self):
        """
            Test creating a new superuser. Should succeed.
        """
        UserModel = get_user_model()
        user = UserModel.objects.create_superuser(
            email='test@gmail.com',
            password='123456789'
        )

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)