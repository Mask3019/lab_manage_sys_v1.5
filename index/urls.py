from django.urls import path
from django.contrib.auth import views as auth_views
from .views import user_login_ajax, index

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='user_login.html'), name='user_login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='user_logout'),
    path('ajax_login_data/', user_login_ajax, name='ajax_login_data'),
    path('', index, name='index'),
]
