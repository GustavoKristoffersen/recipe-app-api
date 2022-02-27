from django.test import TestCase
from django.contrib.auth import get_user_model
from unittest.mock import patch

from core.models import Tag, Ingredient, Recipe, recipe_image_file_path


def get_sample_user(email='gustavo@test.com', password='123456'):
    """Returns a sample user instance"""
    return get_user_model().objects.create_user(email, password)


class ModelTests(TestCase):

    def test_create_user_with_email_successful(self):
        """Test creating a new user with an email. Should succeed"""
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
        """Test the email for a new user is normalised"""
        email = "test@GMAIL.COM"
        UserModel = get_user_model()
        user = UserModel.objects.create_user(
            email=email,
            password='123456789',
        )

        self.assertEqual(user.email, email.lower())

    
    def test_new_user_invalid_email(self):
        """Test creating user with no email. Should fail"""
        with self.assertRaises(ValueError):
            UserModel = get_user_model()
            UserModel.objects.create_user(
                email=None,
                password='123456789'
            )

    def test_create_new_superuser(self):
        """Test creating a new superuser. Should succeed"""
        UserModel = get_user_model()
        user = UserModel.objects.create_superuser(
            email='test@gmail.com',
            password='123456789'
        )

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    
    def test_tag_str(self):
        """Test creating tag and its str representation"""
        tag = Tag.objects.create(
            name='Vegan',
            user=get_sample_user()
        )

        self.assertEqual(str(tag), tag.name)

    def test_ingredient_str(self):
        """Test creating an ingredient and its str representation"""
        ingredient = Ingredient.objects.create(
            name='Coconut',
            user=get_sample_user(),
        )
        
        self.assertEqual(str(ingredient), ingredient.name)

    def test_recipe_str(self):
        """Test creating a recipe and its str representation"""
        recipe = Recipe.objects.create(
            title='Sneak and mushroom sauce',
            time_minutes=5,
            price=5.00,
            user=get_sample_user(),
        )

        self.assertEqual(str(recipe), recipe.title)

    @patch('uuid.uuid4')
    def test_recipe_file_name_uuid(self, mock_uuid):
        """Test that images are saved on the correct location and filename"""
        uuid_name = 'uuid testing'
        mock_uuid.return_value = uuid_name

        file_path = recipe_image_file_path(None, 'myimage.jpg')
        desired_path = f'uploads/recipes/{uuid_name}.jpg'

        self.assertEqual(file_path, desired_path)
