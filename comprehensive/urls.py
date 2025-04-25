from django.urls import path
from django.contrib.auth.views import LoginView,LogoutView
from .views import *
from django.conf import settings
from django.conf.urls.static import static

app_name = 'comprehensive'

urlpatterns = [
    path('report_register/', report_register, name='report_register'),
    path('report_delay/', report_delay, name='report_delay'),
    path('report_analysis/', report_analysis, name='report_analysis'),
    # 试验大纲路由配置
    path('outline_register/', outline_register, name='outline_register'),
    path('filter_projects/', filter_projects, name='filter_projects'),
    path('save_outline/', save_outline, name='save_outline'),
    path('delete_outline/', delete_outline, name='delete_outline'),
    path('upload_outline_file/', upload_outline_file, name='upload_outline_file'),
    # 委托方编辑路由设置
    path('client_edit/', client_edit, name='client_edit'),
    path('delete_client/', delete_client, name='delete_client'),
    path('save_client/', save_client, name='save_client'),

]

# # 配置 Django 来提供 media 文件夹中的内容
# if settings.DEBUG:
#     urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)