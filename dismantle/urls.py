from django.urls import path
from django.contrib.auth.views import LoginView,LogoutView
from .views import *

app_name = 'dismantle'

urlpatterns = [
    path('dismantle_apply/', dismantle_apply, name='dismantle_apply'),
    path('dismantle_register/', dismantle_register, name='dismantle_register'),
    path('dismantle_issue_summary/', dismantle_issue, name='dismantle_issue'),
    path('dismantle_PQCP/', dismantle_PQCP, name='dismantle_PQCP'),

]