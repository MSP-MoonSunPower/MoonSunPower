<<<<<<< HEAD
from django.urls import path, include
from django.contrib import admin  
from .views import SignupView, LoginView, LogoutView
=======
from django.urls import path
from .views import *
>>>>>>> fix

urlpatterns = [
    path('signup/', SignupView.as_view(), name='signup'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
<<<<<<< HEAD
=======
    path('change-photo/', ProfileImageUpdateView.as_view(), name='change-photo'),
    path('delete-photo/', ProfileImageDeleteView.as_view(), name='delete-photo'),
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('delete-account/', UserDeleteView.as_view(), name='delete-account')
>>>>>>> fix
]
