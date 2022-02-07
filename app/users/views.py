from rest_framework.generics import CreateAPIView
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.settings import api_settings

from users.serializers import UserSerializer, AuthTokenSerializer


class CreateUserView(CreateAPIView):
    """View that peforms user creation"""
    serializer_class = UserSerializer


class CreateTokenView(ObtainAuthToken):
    """Generates an auth token for the user"""
    serializer_class = AuthTokenSerializer
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES