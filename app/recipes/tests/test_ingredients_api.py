from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from core.models import Ingredient, Recipe
from recipes.serializers import IngredientSerializer


INGREDIENTS_URL = reverse('recipes:ingredient-list')


class PublicIngredientsApiTests(TestCase):
    """Tests the public ingredient endpoints"""

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test that login is required to access user ingredients"""
        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientsApiTests(TestCase):
    """Tests the private ingredient endpoints"""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email='gustavo@test.com',
            password='123456'
        )
        self.client.force_authenticate(user=self.user)

    def test_retrieve_ingredient_list(self):
        """Test retrieving a list of ingredients from the user"""
        Ingredient.objects.create(name='Kale', user=self.user)
        Ingredient.objects.create(name='Salt', user=self.user)
        ingredients = Ingredient.objects.all().order_by('name')
        serializer = IngredientSerializer(ingredients, many=True)
        
        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.json(), serializer.data)

    def test_ingredients_are_limited_to_user(self):
        """Test that users only have access to their own ingredients"""
        new_user = get_user_model().objects.create_user(
            email='newuser@test.com',
            password='123456'
        )
        ingredient = Ingredient.objects.create(name='Vinegar', user=self.user)
        Ingredient.objects.create(name='Tomato', user=new_user)

        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.json()), 1)
        self.assertEqual(res.json()[0]['name'], ingredient.name)

    def test_create_ingredient_successful(self):
        """Test creating a new ingredient should succeed"""
        payload = {'name': 'Eggs'}
        res = self.client.post(INGREDIENTS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        exists = Ingredient.objects.filter(user=self.user, name=payload['name']).exists()
        self.assertTrue(exists)

    def test_creating_ingredient_invalid(self):
        """Test creating a new ingredient with an invalid payload"""
        payload = {'name': ''}
        res = self.client.post(INGREDIENTS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_ingredients_assingned_to_recipes(self):
        """Test retrieving only the ingredients that area assigned to recipes"""
        ingredient1 = Ingredient.objects.create(user=self.user, name='Eggs')
        ingredient2 = Ingredient.objects.create(user=self.user, name='Beet')
        recipe = Recipe.objects.create(
            user=self.user,
            title='Chocolate cake',
            time_minutes=35,
            price=15.20
        )
        recipe.ingredients.add(ingredient1)

        res = self.client.get(INGREDIENTS_URL, {'assigned_only': 'true'})

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        serializer1 = IngredientSerializer(ingredient1)
        serializer2 = IngredientSerializer(ingredient2)
        self.assertIn(serializer1.data, res.json())
        self.assertNotIn(serializer2.data, res.json())

    def test_ingredients_assingned_unique(self):
        """Test that the ingredients retrieved are not being duplicated"""
        ingredient1 = Ingredient.objects.create(user=self.user, name='Eggs')
        ingredient2 = Ingredient.objects.create(user=self.user, name='Beet')
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
        recipe1.ingredients.add(ingredient1)
        recipe2.ingredients.add(ingredient1)

        res = self.client.get(INGREDIENTS_URL, {'assigned_only': 'true'})

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.json()), 1)



