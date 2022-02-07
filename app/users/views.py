from rest_framework.generics import CreateAPIView

from users.serializers import UserSerializer


class CreateUserView(CreateAPIView):
    """View that peforms user creation"""
    serializer_class = UserSerializer