from django.urls import path
from .views import (
    experiment_tasks_day, get_outlines, save_task, delete_task, 
    experiment_tasks_long, save_gantt_data, get_gantt_data,
    experiment_tasks_apply, experiment_progress, get_task_details, 
    parse_task_pdf, delete_task_application, update_task_application,
    search_task_applications, experiment_tasks_run, save_device_run,
    get_device_run, delete_device_run, experiment_tasks_log,
    experiment_statistics_device, experiment_statistics_project,
    get_device_history, get_experiment_logs, get_experiment_log,
    save_experiment_log, delete_experiment_log, search_experiment_logs
)

app_name = 'experiment'

urlpatterns = [
    ## 设置任务路由
    # 设置日任务路由
    path('experiment_tasks_day/', experiment_tasks_day, name='experiment_tasks_day'),
    path('get_outlines/<str:project_code>/', get_outlines, name='get_outlines'),
    path('save_task/', save_task, name='save_task'),
    path('delete_task/', delete_task, name='delete_task'),
    # 设置长期任务路由
    path('experiment_tasks_long/', experiment_tasks_long, name='experiment_tasks_long'),
    path('save-gantt/', save_gantt_data, name='save_gantt_data'),
    path('get-gantt-data/', get_gantt_data, name='get-gantt-data'),

    # 设置紧急任务路由
    path('experiment_tasks_apply/', experiment_tasks_apply, name='experiment_tasks_apply'),

    ## 设置试验进度路由
    path('experiment_progress/', experiment_progress, name='experiment_progress'),

    
    # 获取任务详情的 API 路由
    path('api/task-details/<str:task_number>/', get_task_details, name='get_task_details'),
    path('api/parse-task-pdf/', parse_task_pdf, name='parse_task_pdf'),
    path('api/delete-task-application/', delete_task_application, name='delete_task_application'),
    path('api/update-task-application/', update_task_application, name='update_task_application'),
    path('api/search-task-applications/', search_task_applications, name='search_task_applications'),

    ## 设置试验统计路由
    # 设置试验运行统计路由
    path('experiment_tasks_run/', experiment_tasks_run, name='experiment_tasks_run'),
    path('api/save-device-run/', save_device_run, name='save_device_run'),
    path('api/get-device-run/<str:record_id>/', get_device_run, name='get_device_run'),
    path('api/delete-device-run/', delete_device_run, name='delete_device_run'),
    path('api/get-device-history/', get_device_history, name='get_device_history'),
    # 设置试验履历表路由
    path('experiment_tasks_log/', experiment_tasks_log, name='experiment_tasks_log'),
    path('api/get-experiment-logs/', get_experiment_logs, name='get_experiment_logs'),
    path('api/get-experiment-log/<str:log_id>/', get_experiment_log, name='get_experiment_log'),
    path('api/save-experiment-log/', save_experiment_log, name='save_experiment_log'),
    path('api/delete-experiment-log/', delete_experiment_log, name='delete_experiment_log'),
    path('api/search-experiment-logs/', search_experiment_logs, name='search_experiment_logs'),
    # 设置按照设备统计路由
    path('experiment_statistics_device/', experiment_statistics_device, name='experiment_statistics_device'),
    # 设置按照项目统计路由
    path('experiment_statistics_project/', experiment_statistics_project, name='experiment_statistics_project'),
]
