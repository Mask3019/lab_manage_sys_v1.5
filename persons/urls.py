from django.urls import path
from django.contrib.auth.views import LoginView,LogoutView
from .views import *

app_name = 'persons'

urlpatterns = [
    # 设置人员列表路由地址
    path('persons_list/', persons_list, name='persons_list'),
    path('save_person/', save_person, name='save_person'),
    path('delete_person/', delete_person, name='delete_person'),
    # 设置人员技能路由地址
    path('persons_skills/', persons_skills, name='persons_skills'),
    path('get_person_details/<int:person_id>/', get_person_details, name='get_person_details'),
    path('get_person_skill_data/<int:person_id>/<str:set_name>/', get_person_skill_data, name='get_person_skill_data'),
    path('update_skill/', update_skill, name='update_skill'),
    path('update_performance/', update_performance, name='update_performance'),
    # 设置任务负荷路由地址
    path('persons_tasks/', persons_tasks, name='persons_tasks'),
    path('save_task/', save_task, name='save_task'),
    path('delete_task/',delete_task, name='delete_task'),
    # 设置人员加班路由地址
    path('persons_overtime_apply/', persons_overtime_apply, name='persons_overtime_apply'),
    path('save_overtime_application/', save_overtime_application, name='save_overtime_application'),
    path('get_overtime_application_data/', get_overtime_application_data, name='get_overtime_application_data'),
    path('delete_overtime_application/', delete_overtime_application, name='delete_overtime_application'),
    path('persons_overtime_analysis/', persons_overtime_analysis, name='persons_overtime_analysis'),
    
]