from django.db import models
from django.contrib.auth.models import User


class Equipment(models.Model):
    IMPORTANCE_CHOICES = [
        ('high', '高'),
        ('medium', '中'),
        ('low', '低'),
    ]

    MAINTENANCE_CYCLE_CHOICES = [
        (30, '每月'),
        (90, '每季度'),
        (180, '每半年'),
        (365, '每年'),
    ]

    equipment_id = models.CharField(
        max_length=50, 
        primary_key=True, 
        unique=True,  # 添加unique约束
        db_index=True,  # 添加索引以提高查询效率
        verbose_name="设备编号"
    )
    name = models.CharField(max_length=100, verbose_name="设备名称")
    type = models.CharField(max_length=100, verbose_name="设备类型")
    equipment_status = models.CharField(max_length=50, verbose_name="设备状态")
    last_maintenance_date = models.DateField(
        "最新保养日期", null=True, blank=True)
    usage_frequency = models.CharField(
        max_length=50, verbose_name="使用频率")
    responsible_person = models.CharField(
        max_length=100, verbose_name="设备负责人")
    waiting_cost = models.FloatField(verbose_name="等待费用")
    debugging_cost = models.FloatField(verbose_name="调试费用")
    operating_cost = models.FloatField(verbose_name="运行费用")
    importance = models.CharField(
        max_length=10,
        choices=IMPORTANCE_CHOICES,
        default='medium',
        verbose_name="重要程度"
    )
    maintenance_cycle = models.IntegerField(
        choices=MAINTENANCE_CYCLE_CHOICES,
        default=365,
        verbose_name="保养周期(天)"
    )
    remark = models.TextField(
        blank=True, null=True, verbose_name="备注")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "设备"
        verbose_name_plural = "设备"
        constraints = [
            models.UniqueConstraint(
                fields=['equipment_id'], 
                name='unique_equipment_id'
            )
        ]


class MaintenanceRecord(models.Model):
    equipment = models.ForeignKey(
        Equipment, on_delete=models.CASCADE, verbose_name="设备")
    equipment_serial_number = models.CharField(
        "设备编号", max_length=100, blank=True)
    maintenance_date = models.DateField("保养日期")
    description = models.TextField("保养描述")
    next_maintenance_date = models.DateField(
        "下次保养日期", null=True, blank=True)

    def __str__(self):
        return f"{self.equipment.name} - {self.maintenance_date}"


class EquipmentRepairApplication(models.Model):
    application_number = models.CharField(
        max_length=50, unique=True, null=True, blank=True, verbose_name="申请编号")
    employee_id = models.CharField(max_length=10, verbose_name="工号")
    submitter_name = models.CharField(max_length=100, verbose_name="提交人姓名")
    application_date = models.DateField(verbose_name="申请日期")
    device_name = models.CharField(max_length=100, verbose_name="设备名称")
    fault_phenomenon = models.TextField(verbose_name="故障现象")
    fault_reason = models.TextField(
        null=True, blank=True, verbose_name="故障原因")
    fault_locations = models.CharField(
        max_length=50, null=True, blank=True, verbose_name="故障位置")
    fault_level = models.CharField(
        max_length=50, null=True, blank=True, verbose_name="故障等级")
    solution = models.TextField(
        null=True, blank=True, verbose_name="解决办法")
    start_time = models.DateField(
        null=True, blank=True, verbose_name="开始时间")
    end_time = models.DateField(
        null=True, blank=True, verbose_name="结束时间")
    duration = models.CharField(
        max_length=10, null=True, blank=True, verbose_name="时长")

    # 审批状态和驳回原因
    line_leader_approval = models.BooleanField(
        null=True, blank=True, verbose_name="条线领导审批状态")
    line_leader_rejection_reason = models.TextField(
        null=True, blank=True, verbose_name="条线领导驳回原因")

    department_leader_approval = models.BooleanField(
        null=True, blank=True, verbose_name="部门领导审批状态")
    department_leader_rejection_reason = models.TextField(
        null=True, blank=True, verbose_name="部门领导驳回原因")

    area_leader_approval = models.BooleanField(
        null=True, blank=True, verbose_name="区域领导审批状态")
    area_leader_rejection_reason = models.TextField(
        null=True, blank=True, verbose_name="区域领导驳回原因")

    device_manager_approval = models.BooleanField(
        null=True, blank=True, verbose_name="设备管理员审批状态")
    device_manager_rejection_reason = models.TextField(
        null=True, blank=True, verbose_name="设备管理员驳回原因")

    device_repairer_approval = models.BooleanField(
        null=True, blank=True, verbose_name="设备维修员审批状态")
    device_repairer_rejection_reason = models.TextField(
        null=True, blank=True, verbose_name="设备维修员驳回原因")

    rejected_to = models.CharField(
        max_length=100, null=True, blank=True, verbose_name="驳回给")

    def __str__(self):
        return f"{self.application_number} - {self.submitter_name}"

    def save(self, *args, **kwargs):
        if not self.application_number:
            # 生成申请编号
            date_str = self.application_date.strftime("%Y%m%d")
            prefix = f"SBWX-{date_str}-"

            # 获取当天已有的最大序号
            existing_numbers = EquipmentRepairApplication.objects.filter(
                application_date=self.application_date
            ).values_list("application_number", flat=True)

            max_serial = 0
            for number in existing_numbers:
                # 提取编号中的序号部分
                serial_part = number.split("-")[-1]
                try:
                    serial_number = int(serial_part)
                    if serial_number > max_serial:
                        max_serial = serial_number
                except ValueError:
                    continue  # 忽略无法解析的编号

            new_serial = max_serial + 1
            serial_number = f"{new_serial:02d}"
            self.application_number = prefix + serial_number

        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "设备维修申请"
        verbose_name_plural = "设备维修申请"
        permissions = [
            ("can_approve_line_leader", "Can approve as line leader"),
            ("can_approve_department_leader", "Can approve as department leader"),
            ("can_approve_area_leader", "Can approve as area leader"),
            ("can_approve_device_manager", "Can approve as device manager"),
            ("can_approve_device_repairer", "Can approve as device repairer"),
        ]


class Supplier(models.Model):
    name = models.CharField(max_length=200, verbose_name="供应商名称")
    address = models.CharField(max_length=500, verbose_name="供应商地址")
    contact_person = models.CharField(max_length=100, verbose_name="联系人")  # 新增字段
    contact_phone = models.CharField(max_length=20, verbose_name="联系电话")  # 新增字段
    repair_scope = models.TextField(verbose_name="维修范围")
    repair_equipment = models.TextField(verbose_name="维修台架")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "供应商"
        verbose_name_plural = "供应商"
        ordering = ['-created_at']
        permissions = [
            ("can_manage_supplier", "Can manage supplier"),
        ]
