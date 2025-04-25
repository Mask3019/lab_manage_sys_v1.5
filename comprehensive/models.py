from django.db import models

# Create your models here.
class Outlines(models.Model):
    sample_style = models.CharField(max_length=30)
    project = models.CharField(max_length=30)
    outline_num = models.CharField(max_length=100)
    outline_name = models.CharField(max_length=150)
    editor = models.CharField(max_length=30)
    save_date = models.DateField()
    outline_status = models.CharField(max_length=30)
    remark = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.outline_name

class Department(models.Model):
    # 委托部门
    name = models.CharField(max_length=100, verbose_name="委托部门")
    # 部门领导
    department_leader = models.CharField(max_length=100, verbose_name="部门领导")
    # 部门领导邮箱
    department_email = models.CharField(max_length=50, verbose_name="部门领导邮箱")
    # 分管领导
    tech_center_leader = models.CharField(max_length=100, verbose_name="部门分管领导")
    # 分管领导
    leader_email = models.CharField(max_length=50, verbose_name="分管领导邮箱")
    # 项目内容
    projects = models.CharField(max_length=255, verbose_name="负责项目")
    def __str__(self):
        return self.name
