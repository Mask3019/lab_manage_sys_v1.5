from django.urls import path
from django.contrib.auth.views import LoginView,LogoutView
from .views import *

urlpatterns = [
    path('personal/', person_center, name='person_center'),

]