from django.urls import path
from django.contrib.auth.views import LoginView,LogoutView
from .views import *

app_name = 'admin_back'

urlpatterns = [
    path('admin_back/', admin_back, name='admin_back'),
]