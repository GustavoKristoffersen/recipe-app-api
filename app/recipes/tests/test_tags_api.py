from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag, Recipe
from recipes.serializers import TagSerializer


TAGS_URL = reverse('recipes:tag-list')


class PublicTagApiTests(TestCase):
    """Test the public tags endpoints"""

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test that login is required for retrieving user tags"""
        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagApiTests(TestCase):
    """Test the private tags endpoints"""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email='gustavo@test.com',
            password='123456'
        )
        self.client.force_authenticate(user=self.user)

    def test_retrieving_user_tags(self):
        """Test retrieving logged in user tags should succeed"""
        Tag.objects.create(name='Vegan', user=self.user)
        Tag.objects.create(name='Dessert', user=self.user)
        tags = Tag.objects.all().order_by('name')
        
        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        serializer = TagSerializer(tags, many=True)
        self.assertEqual(res.json(), serializer.data)
        
    def test_tags_are_limited_to_user(self):
        """Test that users only have access to their own tags"""
        user2 = get_user_model().objects.create_user(email='test@test.com', password='123456')
        Tag.objects.create(name='Dessert', user=user2)
        tag = Tag.objects.create(name='Vegan', user=self.user)

        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.json()), 1)
        self.assertEqual(res.json()[0]['name'], tag.name)

    def test_create_tag_successful(self):
        """Test creating a new tag should succeed"""
        payload = {'name': 'testag'}
        res = self.client.post(TAGS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        exists = Tag.objects.filter(user=self.user, name=payload['name']).exists()
        self.assertTrue(exists)

    def test_create_tag_invalid(self):
        """Test creating a new tag with an invalid payload"""
        payload = {'name': ''}
        res = self.client.post(TAGS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_tags_assingned_to_recipes(self):
        """Test retrieving only the tags that area assigned to recipes"""
        tag1 = Tag.objects.create(user=self.user, name='Vegan')
        tag2 = Tag.objects.create(user=self.user, name='Cakes')
        recipe = Recipe.objects.create(
            user=self.user,
            title='Chocolate cake',
            time_minutes=35,
            price=15.20
        )
        recipe.tags.add(tag1)

        res = self.client.get(TAGS_URL, {'assigned_only': 'true'})

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        serializer1 = TagSerializer(tag1)
        serializer2 = TagSerializer(tag2)
        self.assertIn(serializer1.data, res.json())
        self.assertNotIn(serializer2.data, res.json())

    def test_tags_assingned_unique(self):
        """Test that the tags retrieved are not being duplicated"""
        tag1 = Tag.objects.create(user=self.user, name='Vegan')
        tag2 = Tag.objects.create(user=self.user, name='Cake')
        recipe1 = Recipe.objects.create(
            user=self.user,
            title='Chocolate cake',
            time_minutes=45,
            price=15.00
        )
        recipe2 = Recipe.objects.create(
            user=self.user,
            title='Strawberry cake',
            time_minutes=45,
            price=15.00
        )
        recipe1.tags.add(tag1)
        recipe2.tags.add(tag1)

        res = self.client.get(TAGS_URL, {'assigned_only': 'true'})

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.json()), 1)

        