from django.urls import path

from users import views


app_name = 'users'

urlpatterns = [
    path('', views.CreateUserView.as_view(), name='create'),
    path('auth/', views.CreateTokenView.as_view(), name='auth'),
    path('me/', views.ManageUserView.as_view(), name='me'),
]