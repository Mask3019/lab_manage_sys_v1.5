from django.contrib import admin
from .models import Equipment, MaintenanceRecord, EquipmentRepairApplication, Supplier

@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ('equipment_id', 'name', 'type', 'equipment_status', 'responsible_person')
    search_fields = ('equipment_id', 'name', 'responsible_person')
    list_filter = ('equipment_status', 'importance', 'type')

@admin.register(MaintenanceRecord)
class MaintenanceRecordAdmin(admin.ModelAdmin):
    list_display = ('equipment', 'maintenance_date', 'next_maintenance_date')
    search_fields = ('equipment__name', 'equipment__equipment_id')
    list_filter = ('maintenance_date', 'next_maintenance_date')

@admin.register(EquipmentRepairApplication)
class EquipmentRepairApplicationAdmin(admin.ModelAdmin):
    list_display = ('application_number', 'device_name', 'submitter_name', 'application_date', 'fault_level')
    search_fields = ('application_number', 'device_name', 'submitter_name')
    list_filter = ('application_date', 'fault_level', 'area_leader_approval', 'device_manager_approval')

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_person', 'contact_phone', 'address', 'repair_scope', 'repair_equipment', 'created_at', 'updated_at')
    search_fields = ('name', 'contact_person', 'contact_phone', 'address', 'repair_scope', 'repair_equipment')
    list_filter = ('created_at', 'updated_at')
    ordering = ('-created_at',)
