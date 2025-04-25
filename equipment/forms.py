# forms.py

from django import forms
from .models import MaintenanceRecord, Equipment
from django.utils import timezone
from datetime import timedelta


class MaintenanceRecordForm(forms.ModelForm):
    equipment = forms.ModelChoiceField(
        queryset=Equipment.objects.all(),
        label='设备',
        widget=forms.Select(),
        empty_label=None,
    )

    class Meta:
        model = MaintenanceRecord
        fields = ['equipment', 'maintenance_date', 'description', 'next_maintenance_date']
        widgets = {
            'maintenance_date': forms.DateInput(attrs={'type': 'date'}),
            'next_maintenance_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        # 使用 `initial` 参数传递默认值
        initial = kwargs.get('initial', {})
        today = timezone.now().date()

        # 如果未提供 `maintenance_date` 和 `next_maintenance_date`，则设置默认值
        initial.setdefault('maintenance_date', today)
        initial.setdefault('next_maintenance_date', today + timedelta(days=365))

        # 将更新后的初始值传递回表单
        kwargs['initial'] = initial
        super(MaintenanceRecordForm, self).__init__(*args, **kwargs)

        # 自定义设备下拉框的显示标签
        self.fields['equipment'].label_from_instance = lambda obj: f"{obj.equipment_id} - {obj.name}"
