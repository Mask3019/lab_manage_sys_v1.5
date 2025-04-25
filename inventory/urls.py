from django.urls import path
from django.contrib.auth.views import LoginView,LogoutView
from .views import *

app_name = 'inventory'

urlpatterns = [
    path('inventory_in/', inventory_in, name='inventory_in'),
    path('inventory_out/', inventory_out, name='inventory_out'),
    path('inventory_alarm/', inventory_alarm, name='inventory_alarm'),
    path('inventory_discard/', inventory_discard, name='inventory_discard'),
]