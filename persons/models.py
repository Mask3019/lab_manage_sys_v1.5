from django.db import models
from django.db.models import Max

class Person(models.Model):
    employee_id = models.CharField(max_length=10)
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    birth_date = models.DateField()
    address = models.CharField(max_length=255)
    entry_date = models.DateField()
    department = models.CharField(max_length=100)
    role = models.CharField(max_length=100)
    grade = models.CharField(max_length=50, blank=True, null=True)  # 新增字段：等级
    expertise = models.CharField(max_length=255, blank=True, null=True)  # 新增字段：擅长领域
    remark = models.TextField(blank=True, null=True)
    potential = models.CharField(max_length=10)
    skill = models.CharField(max_length=10)
    photo = models.ImageField(upload_to='persons/', blank=True, null=True)  # 新增字段：头像

    # class Meta:
    #     permissions = [
    #         ("view_person", "Can view person"),
    #         ("change_person", "Can change person"),
    #         ("delete_person", "Can delete person"),
    #     ]

    def __str__(self):
        return self.name

class Skill(models.Model):
    person = models.OneToOneField(Person, on_delete=models.CASCADE, related_name='skill_data')
    skill1 = models.IntegerField(default=0)
    skill2 = models.IntegerField(default=0)
    skill3 = models.IntegerField(default=0)
    skill4 = models.IntegerField(default=0)
    skill5 = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.person.name} Skill Data"

class Performance(models.Model):
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='performance_data')
    set_name = models.CharField(max_length=50)  # 比如 'MT', 'DCT' 等
    performance1 = models.IntegerField(default=0)
    performance2 = models.IntegerField(default=0)
    performance3 = models.IntegerField(default=0)
    performance4 = models.IntegerField(default=0)
    performance5 = models.IntegerField(default=0)
    performance6 = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.person.name} - {self.set_name} Performance Data"


class OvertimeApplication(models.Model):
    application_number = models.CharField(max_length=50, unique=True, null=True, blank=True)  # 申请编号
    employee_id = models.CharField(max_length=10)  # 工号
    submitter_name = models.CharField(max_length=100)  # 提交人姓名
    overtime_employee_name = models.CharField(max_length=100)  # 加班人员姓名
    application_date = models.DateField()  # 申请日期
    created_at = models.DateTimeField(auto_now_add=True)  # 提交时间
    start_time = models.TimeField()  # 开始时间
    end_time = models.TimeField()  # 结束时间
    duration = models.DecimalField(max_digits=5, decimal_places=2)  # 时长
    reason = models.TextField()  # 加班原因

    # 审批状态和驳回原因
    line_leader_approval = models.BooleanField(null=True, blank=True)  # 条线领导审批状态
    line_leader_rejection_reason = models.TextField(null=True, blank=True)  # 条线领导驳回原因

    department_leader_approval = models.BooleanField(null=True, blank=True)  # 部门领导审批状态
    department_leader_rejection_reason = models.TextField(null=True, blank=True)  # 部门领导驳回原因

    # 添加综合管理审批相关字段
    general_management_approval = models.BooleanField(null=True, blank=True)  # 综合管理审批状态
    general_management_rejection_reason = models.TextField(null=True, blank=True)  # 综合管理驳回原因

    def __str__(self):
        return f'{self.application_number} - {self.overtime_employee_name}'

    def save(self, *args, **kwargs):
        if not self.application_number:
            # 生成申请编号
            date_str = self.application_date.strftime('%Y%m%d')
            prefix = f'JBSQ-{date_str}-'

            # 获取当天已有的最大序号
            existing_numbers = OvertimeApplication.objects.filter(
                application_date=self.application_date
            ).values_list('application_number', flat=True)

            max_serial = 0
            for number in existing_numbers:
                # 提取编号中的序号部分
                serial_part = number.split('-')[-1]
                try:
                    serial_number = int(serial_part)
                    if serial_number > max_serial:
                        max_serial = serial_number
                except ValueError:
                    continue  # 忽略无法解析的编号

            new_serial = max_serial + 1
            serial_number = f'{new_serial:02d}'
            self.application_number = prefix + serial_number

        super(OvertimeApplication, self).save(*args, **kwargs)

    class Meta:
        permissions = [
            ('can_approve_line_leader', 'Can approve as line leader'),
            ('can_approve_department_leader', 'Can approve as department leader'),
            ('can_approve_general_management', 'Can approve as general management'),  # 添加综合管理权限
        ]