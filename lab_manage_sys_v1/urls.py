"""
URL configuration for lab_manage_sys_v1 project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path,include,re_path
from django.views.static import serve
from django.conf import settings

urlpatterns = [
    path("admin/", admin.site.urls),
    path('', include(('index.urls', 'index'), namespace='index')),
    path('', include(('persons.urls', 'persons'), namespace='persons')),
    path('', include(('equipment.urls', 'equipment'), namespace='equipment')),
    path('', include(('experiment.urls', 'experiment'), namespace='experiment')),
    path('', include(('inventory.urls', 'inventory'), namespace='inventory')),
    path('', include(('dismantle.urls', 'dismantle'), namespace='dismantle')),
    path('', include(('comprehensive.urls', 'comprehensive'), namespace='comprehensive')),
    path('', include(('person_center.urls', 'person_center'), namespace='person_center')),
    path('', include(('admin_back.urls', 'admin_back'), namespace='admin_back')),
    re_path('media/(?P<path>.*)', serve, {"document_root": settings.MEDIA_ROOT}),
    re_path('static/(?P<path>.*)', serve, {"document_root": settings.STATIC_ROOT}),
]
