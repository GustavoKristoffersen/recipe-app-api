from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Tag, Ingredient
from recipes.serializers import RecipeSerializer, RecipeDetailSerializer


RECIPES_URL = reverse('recipes:recipe-list')


def get_recipe_detail_url(recipe_id):
    """"Returns a custom URL for a given recipe"""
    return reverse('recipes:recipe-detail', args=[recipe_id])

def get_sample_tag(user, name='Vegan'):
    """Create and returns a sample tag object"""
    return Tag.objects.create(user=user, name=name)

def get_sample_ingredient(user, name='Tomato'):
    """Create and return a sample ingredient object"""
    return Ingredient.objects.create(user=user, name=name)

def get_sample_recipe(user, **kwargs):
    """Creates a sample recipe with default values"""
    defaults = {
        'title': 'Sample recipe',
        'time_minutes': 5,
        'price': 5.00,
    }
    defaults.update(kwargs)

    return Recipe.objects.create(user=user, **defaults)


class PublicRecipeApiTests(TestCase):
    """Tests the public recipe endpoints"""

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test that login is required for retrieving user recipes"""
        res = self.client.get(RECIPES_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeApiTests(TestCase):
    """Tests the private recipe endpoints"""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email='gustavo@test.com',
            password='123456'
        )
        self.client.force_authenticate(user=self.user)

    def test_retreiving_recipes(self):
        """Test retrieving user recipes"""
        get_sample_recipe(user=self.user)
        get_sample_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.json(), serializer.data)

    def test_recipes_are_limited_to_user(self):
        """Test that users only have access to their own recipes"""
        new_user = get_user_model().objects.create_user(
            email='newuser@test.com',
            password='123456'
        )
        get_sample_recipe(user=new_user)
        get_sample_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(len(res.json()), 1)
        self.assertEqual(res.json(), serializer.data)

    def test_retrieving_recipe_detail(self):
        """Test retrieving  details of a recipe"""
        recipe = get_sample_recipe(user=self.user)
        recipe.tags.add(get_sample_tag(user=self.user))
        recipe.ingredients.add(get_sample_ingredient(user=self.user))

        url = get_recipe_detail_url(recipe.id)
        res = self.client.get(url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        serializer = RecipeDetailSerializer(recipe)
        print(serializer.data)
        self.assertEqual(res.json(), serializer.data)