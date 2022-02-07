from django.urls import path

from users import views


app_name = 'user'

urlpatterns = [
    path('', views.CreateUserView.as_view(), name='create'),
]