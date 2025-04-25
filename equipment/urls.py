from django.urls import path
from django.contrib.auth.views import LoginView,LogoutView
from .views import *

app_name = 'equipment'

urlpatterns = [
    # path('equipment_info/', equipment_information, name='equipment_information'),
    path('equipment_info/', EquipmentInformationView.as_view(), name='equipment_information'),
    path('save-equipment/', save_equipment, name='save_equipment'),
    path('delete-equipment/', delete_equipment, name='delete_equipment'),

    path('equipment_status/', equipment_status, name='equipment_status'),

    path('equipment_maintenance/', equipment_maintenance, name='equipment_maintenance'),
    path('add_maintenance_record/', add_maintenance_record, name='add_maintenance_record'),

    path('equipment_repair/', equipment_repair, name='equipment_repair'),
    path('equipment_medical_card/', equipment_medical_card, name='equipment_medical_card'),
    path('save_device_repair_application/', save_device_repair_application, name='save_device_repair_application'),
    path('get_device_repair_application_data/', get_device_repair_application_data, name='get_device_repair_application_data'),
    path('delete_device_repair_application/', delete_device_repair_application, name='delete_device_repair_application'),

    path('equipment_medical_card/', equipment_medical_card, name='equipment_medical_card'),

    path('equipment_analysis/', equipment_analysis, name='equipment_analysis'),
    # 添加供应商管理的URL配置
    path('supplier_management/', supplier_management, name='supplier_management'),
]