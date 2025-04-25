from django.db import models

# Create your models here.
class Tasks(models.Model):
    task_id = models.CharField(max_length=10, db_index=True)
    task_status = models.CharField(max_length=10, db_index=True)
    project = models.CharField(max_length=30, db_index=True)
    sample_id = models.CharField(max_length=100)
    test_content = models.CharField(max_length=25)
    outline = models.CharField(max_length=255)
    equipment_id = models.CharField(max_length=30)
    task_date = models.DateField(db_index=True)
    client = models.CharField(max_length=25)
    experimenter = models.CharField(max_length=10)
    schedule = models.CharField(max_length=10)
    remark = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.task_id

    class Meta:
        indexes = [
            models.Index(fields=['task_status', 'task_date']),
        ]


# 甘特图数据模型
#=======================================================================================
class GanttProject(models.Model):
    project_id = models.IntegerField(primary_key=True)  # 保存任务的ID
    name = models.CharField(max_length=255)  # 保存任务的名称
    progress = models.FloatField(default=0)  # 任务的进度
    progress_by_worklog = models.BooleanField(default=False)  # 是否按工作日志计算进度
    relevance = models.FloatField(default=0)  # 任务的相关性
    type = models.CharField(max_length=100, blank=True)  # 任务的类型
    type_id = models.CharField(max_length=50, blank=True)  # 任务类型的ID
    description = models.TextField(blank=True)  # 任务描述
    code = models.CharField(max_length=100, blank=True)  # 任务代码
    level = models.IntegerField(default=0)  # 任务层级
    status = models.CharField(max_length=50)  # 任务状态
    depends = models.CharField(max_length=100, blank=True)  # 依赖关系
    can_write = models.BooleanField(default=True)  # 是否可写
    start = models.DateTimeField(db_index=True)  # 开始日期时间
    duration = models.IntegerField()  # 持续时间
    end = models.DateTimeField(db_index=True)  # 结束日期时间
    start_is_milestone = models.BooleanField(default=False)  # 是否是里程碑
    end_is_milestone = models.BooleanField(default=False)  # 是否是里程碑
    collapsed = models.BooleanField(default=False)  # 是否折叠
    assigs = models.JSONField(default=list)  # 任务分配
    has_child = models.BooleanField(default=False)  # 是否有子任务

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['project_id']

class Device_run(models.Model):
    # 文本类型字段，允许设置字符集和排序规则
    id = models.CharField('序号', max_length=20, primary_key=True)  # 将任务单号作为主键
    task_number = models.CharField('任务单号', max_length=100, db_index=True)  # 任务单号
    task_status = models.CharField('任务状态', max_length=20, db_index=True)  # 任务状态
    transmission_model = models.CharField('变速器型号', max_length=100)  # 变速器型号
    test_content = models.CharField('试验内容', max_length=150)  # 试验内容
    date = models.DateTimeField(db_index=True)  # 日期
    sample_number = models.CharField('样品编号', max_length=100)  # 样品编号
    device_number = models.CharField('设备编号', max_length=50, db_index=True)  # 设备编号
    bench_status = models.CharField('台架状态', max_length=20)  # 台架状态
    remarks = models.TextField('备注', blank=True)  # 备注
    # 小数类型字段
    debugging = models.DecimalField('调试', max_digits=5, decimal_places=2, default=0)  # 调试
    running = models.DecimalField('运行', max_digits=5, decimal_places=2, default=0)  # 运行
    sample_fault = models.DecimalField('样件故障', max_digits=5, decimal_places=2, default=0)  # 暂停
    bench_fault = models.DecimalField('台架故障', max_digits=5, decimal_places=2, default=0)  # 故障
    idle = models.DecimalField('闲置', max_digits=5, decimal_places=2, default=0)  # 闲置
    progress = models.CharField('试验进度', max_length=10)  # 试验进度
    dvp_plan = models.CharField('DVP计划内', max_length=5)  # DVP计划内
    responsible_person = models.CharField('责任人', max_length=50)  # 责任人

    class Meta:
        db_table = 'device_run'  # 修改表名为 'device_run'
        verbose_name = '设备运行'
        verbose_name_plural = '设备运行'
        indexes = [
            models.Index(fields=['task_status', 'date']),
            models.Index(fields=['device_number', 'date']),
        ]
        ordering = ['-date', '-id']

    def __str__(self):
        return self.task_number

# 试验履历表模型
class ExperimentLog(models.Model):
    log_id = models.CharField('记录ID', max_length=20, primary_key=True)
    task_number = models.CharField('任务单编号', max_length=100, db_index=True)
    project_code = models.CharField('项目代号', max_length=100, db_index=True)
    sample_number = models.CharField('样件编号', max_length=100)
    test_content = models.CharField('试验内容', max_length=150)
    equipment_id = models.CharField('设备编号', max_length=30, db_index=True)  # 添加设备编号字段
    stop_duration = models.DecimalField('停止时长', max_digits=5, decimal_places=2, default=0)
    log_date = models.DateTimeField('登记日期', db_index=True)
    alarm_phenomenon = models.TextField('报警现象', blank=True)
    alarm_reason = models.TextField('报警原因', blank=True)
    solution = models.TextField('解决办法', blank=True)
    solver = models.CharField('解决人', max_length=50)
    data_path = models.CharField('数据记录路径', max_length=255, blank=True)
    analysis_report = models.CharField('分析报告', max_length=255, blank=True)  # 明确添加分析报告字段
    remarks = models.TextField('备注', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'experiment_log'  # 添加回自定义表名
        verbose_name = '试验履历表'
        verbose_name_plural = '试验履历表'
        ordering = ['-log_date', '-log_id']
        
    def __str__(self):
        return self.log_id

class TaskApplication(models.Model):
    task_number = models.CharField(max_length=100, unique=True, db_index=True)
    department = models.CharField(max_length=100)
    entrusted_person = models.CharField(max_length=100)
    project_type = models.CharField(max_length=50)
    project_code = models.CharField(max_length=100, db_index=True)
    sample_name = models.CharField(max_length=200)
    sample_stage = models.CharField(max_length=100)
    sample_quantity = models.IntegerField()
    sample_code = models.CharField(max_length=100)
    is_outsourced = models.CharField(max_length=10)  # 是否分包
    requires_report = models.CharField(max_length=10)  # 是否要报告
    storage_period = models.CharField(max_length=20)  # 样品保存期
    oil_storage = models.CharField(max_length=20)  # 试后油品
    oil_amount = models.CharField(max_length=50)
    needs_judgment = models.CharField(max_length=10)  # 是否判定
    test_content = models.TextField()  # 试验内容
    test_contentExtra = models.TextField()  # 试验内容
    test_basis = models.TextField()  # 试验依据
    test_specs = models.TextField()  # 试验大纲或技术要求
    debug_time = models.IntegerField()  # 预估调试时长
    test_time = models.IntegerField()  # 预估试验时长
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=2)  # 预估试验费用
    task_source = models.CharField(max_length=20)  # 试验任务来源
    business_type = models.CharField(max_length=20)  # 试验业务类型
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    def __str__(self):
        return self.task_number
        
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['task_source', 'business_type']),
        ]

