import tempfile
import os

from PIL import Image

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Tag, Ingredient
from recipes.serializers import RecipeSerializer, RecipeDetailSerializer


RECIPES_URL = reverse('recipes:recipe-list')


def get_image_upload_url(recipe_id):
    """Returns a URL for recipe image upload"""
    return reverse('recipes:recipe-upload-image', args=[recipe_id])


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
        self.assertEqual(res.json(), serializer.data)

    def test_creating_basic_recipe(self):
        """Test creating a basic recipe with only mandatory fields"""
        payload = {
            'title': 'Chocolate cheescake',
            'time_minutes': 30,
            'price': 14.50
        }
        res = self.client.post(RECIPES_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.json()['id'])
        for key in payload.keys():
            self.assertEqual(payload[key], getattr(recipe, key))

    def test_creating_recipe_with_tags(self):
        """Test creating a recipe with tags"""
        tag1 = get_sample_tag(user=self.user, name='Vegan')
        tag2 = get_sample_tag(user=self.user, name='Dessert')
        payload = {
            'title': 'Avocado lime cheescake',
            'tags': [tag1.id, tag2.id],
            'time_minutes': 60,
            'price': 15.00
        }

        res = self.client.post(RECIPES_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.json()['id'])
        tags = recipe.tags.all()
        self.assertEqual(tags.count(), 2)
        self.assertIn(tag1, tags)
        self.assertIn(tag2, tags)

    def test_creating_recipe_with_ingredients(self):
        """Test creating a recipe with ingredients"""
        ingredient1 = get_sample_ingredient(user=self.user, name='Prawns')
        ingredient2 = get_sample_ingredient(user=self.user, name='Ginger')
        payload = {
            'title': 'Thai prawn red curry',
            'ingredients': [ingredient1.id, ingredient2.id],
            'time_minutes': 35,
            'price': 125.00
        }

        res = self.client.post(RECIPES_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.json()['id'])
        ingredients = recipe.ingredients.all()
        self.assertEqual(ingredients.count(), 2)
        self.assertIn(ingredient1, ingredients)
        self.assertIn(ingredient2, ingredients)

    def test_partially_updating_recipe(self):
        """Test partially updating recipe field with patch"""
        recipe = get_sample_recipe(user=self.user)
        recipe.tags.add(get_sample_tag(user=self.user))
        new_tag = get_sample_tag(user=self.user)
        url = get_recipe_detail_url(recipe.id)
        payload = {
            'title': 'New recipe name haha',
            'tags': [new_tag.id]
        }

        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.tags.count(), 1)
        self.assertIn(new_tag, recipe.tags.all())

    def test_fully_updating_recipe(self):
        """Test fully updating recipe fields with put"""
        recipe = get_sample_recipe(user=self.user)
        recipe.tags.add(get_sample_tag(user=self.user))
        url = get_recipe_detail_url(recipe.id)
        payload = {
            'title': 'New title for recipe',
            'time_minutes': 45,
            'price': 135
        }

        res = self.client.put(url, payload)

        recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.time_minutes, payload['time_minutes'])
        self.assertEqual(recipe.price, payload['price'])
        self.assertEqual(recipe.tags.count(), 0)

    def test_retrieving_recipes_filtered_by_tags(self):
        """Test retrieving recipe with specific tags"""
        recipe1 = get_sample_recipe(user=self.user, title='Something with mushrooms idk')
        recipe2 = get_sample_recipe(user=self.user, title='Coconut pancakes')
        recipe3 = get_sample_recipe(user=self.user, title='Eggs and bacon')
        tag1 = get_sample_tag(user=self.user, name='Vegan')
        tag2 = get_sample_tag(user=self.user, name='Pancakes')
        recipe1.tags.add(tag1)
        recipe2.tags.add(tag2)

        res = self.client.get(RECIPES_URL, {'tags': f'{tag1.id},{tag2.id}'})

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        serializer1 = RecipeSerializer(recipe1)
        serializer2 = RecipeSerializer(recipe2)
        serializer3 = RecipeSerializer(recipe3)
        self.assertIn(serializer1.data, res.json())
        self.assertIn(serializer2.data, res.json())
        self.assertNotIn(serializer3.data, res.json())

    def test_retrieving_recipes_filtered_by_ingredients(self):
        """Test retrieving recipes with specific ingredients"""
        recipe1 = get_sample_recipe(user=self.user, title='Something with mushrooms idk')
        recipe2 = get_sample_recipe(user=self.user, title='Coconut pancakes')
        recipe3 = get_sample_recipe(user=self.user, title='Eggs and bacon')
        ingredient1 = get_sample_ingredient(user=self.user, name='Mushroom')
        ingredient2 = get_sample_ingredient(user=self.user, name='Bacon')
        recipe1.ingredients.add(ingredient1)
        recipe2.ingredients.add(ingredient2)

        res = self.client.get(RECIPES_URL, {'ingredients': f'{ingredient1.id},{ingredient2.id}'})

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        serializer1 = RecipeSerializer(recipe1)
        serializer2 = RecipeSerializer(recipe2)
        serializer3 = RecipeSerializer(recipe3)
        self.assertIn(serializer1.data, res.json())
        self.assertIn(serializer2.data, res.json())
        self.assertNotIn(serializer3.data, res.json())


class RecipeImageUploadingTests(TestCase):
    """Tests for recipe image uploads"""

    def setUp(self):
        self.user = get_user_model().objects.create(
            email='gustavo@test.com',
            password='123456'
        )
        self.recipe = get_sample_recipe(self.user)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def tearDown(self):
        self.recipe.image.delete()

    def test_uploading_image_to_recipe(self):
        """Test uploading an image to a recipe"""
        url = get_image_upload_url(self.recipe.id)
        with tempfile.NamedTemporaryFile(suffix='.jpg') as ntf:
            img = Image.new('RGB', (10, 10))
            img.save(ntf, format='JPEG')
            ntf.seek(0)
            res = self.client.post(url, {'image': ntf}, format='multipart')

        self.recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('image', res.json())
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_uploading_image_incorrectly(self):
        """Test uploading an invalid image"""
        url = get_image_upload_url(self.recipe.id)
        res = self.client.post(url, {'image': 'wrong image'}, format='multipart')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
