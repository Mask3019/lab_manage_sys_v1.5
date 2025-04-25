import logging
import pdfplumber
import re
from django.views.decorators.csrf import csrf_exempt

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from .models import *
from comprehensive.models import *
from django.utils.dateparse import parse_date
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from .models import GanttProject
import json
from datetime import datetime, timedelta
from equipment.models import Equipment
from django.db import models
from django.contrib import messages
import traceback  # 添加traceback模块
from django.db.models import Q, Sum, Count, Avg
from django.utils import timezone
from django.urls import reverse
from django.core.files.storage import FileSystemStorage
from django.core.paginator import Paginator
from django.db import transaction
from django.conf import settings
import os

# Create your views here.
@login_required
def get_outlines(request, project_code):
    try:
        outlines = Outlines.objects.filter(project=project_code).values('outline_num', 'outline_name')
        return JsonResponse({'outlines': list(outlines)})
    except Exception as e:
        logger.error(f"Error in get_outlines: {str(e)}")
        return JsonResponse({'outlines': [], 'error': str(e)}, status=500)

@login_required
def experiment_tasks_day(request):
    try:
        if not request.user.has_perm('experiment.view_tasks'):
            raise PermissionDenied
        tasks = Tasks.objects.exclude(task_status="已完成").order_by('task_date')
        user_has_permission = request.user.has_perm('experiment.change_tasks')

        # 获取所有设备编号
        equipment_list = Equipment.objects.values('equipment_id')

        # 为每个任务根据项目代号获取对应的 outlines
        for task in tasks:
            task.outlines = Outlines.objects.filter(project=task.project)

        context = {
            'page_title': '每日任务',
            'tasks': tasks,
            'user_has_permission': user_has_permission,
            'equipment_list': equipment_list,
        }
        return render(request, 'experiment_tasks_day.html', context)
    except PermissionDenied:
        context = {
            'error_message': '您没有权限查看此页面',
        }
        return render(request, 'experiment_tasks_day.html', context)


@login_required
@permission_required('experiment.change_tasks', raise_exception=True)
def save_task(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            task_id = data.get('task_id')
            task_status = data.get('task_status')
            project = data.get('project')
            sample_id = data.get('sample_id')
            test_content = data.get('test_content')
            equipment_id = data.get('equipment_id')
            work_content = data.get('work_content')
            outline = data.get('outline')
            task_date = data.get('task_date')
            client = data.get('client')
            experimenter = data.get('experimenter')
            schedule = data.get('schedule')
            remark = data.get('remark')

            # 解析并检查任务日期
            task_date = parse_date(task_date)
            if not task_date:
                return JsonResponse({'status': 'error', 'message': '任务日期格式必须为 "YYYY-MM-DD"'}, status=400)

            task, created = Tasks.objects.update_or_create(
                task_id=task_id,
                defaults={
                    'task_status': task_status,
                    'project': project,
                    'sample_id': sample_id,
                    'test_content': test_content,
                    'equipment_id': equipment_id,
                    'work_content': work_content,
                    'outline': outline,
                    'task_date': task_date,
                    'client': client,
                    'experimenter': experimenter,
                    'schedule': schedule,
                    'remark': remark,
                }
            )
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)


@login_required
@permission_required('experiment.delete_tasks', raise_exception=True)
def delete_task(request):
    if request.method == 'POST':
        task_id = request.POST.get('task_id')
        try:
            task = Tasks.objects.get(task_id=task_id)
            task.delete()
            return JsonResponse({'status': 'success'})
        except Tasks.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Task not found'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error'}, status=400)

# 设置长期任务的视图
#=============================================================
@login_required
def experiment_tasks_long(request):
    context = {
        'page_title': '长期任务',
    }
    return render(request, 'experiment_tasks_long.html', context)
# 设置长期任务的甘特图视图函数
logger = logging.getLogger(__name__)
@csrf_exempt
@permission_required('experiment.change_ganttproject', raise_exception=True)
def save_gantt_data(request):
    if request.method == 'POST':
        logger.info(f"User: {request.user.username} is attempting to save Gantt data.")
        if not request.user.has_perm('experiment.change_ganttproject'):
            logger.warning(f"User: {request.user.username} does not have the required permission.")
            raise PermissionDenied

        data = json.loads(request.POST.get('data'))
        current_id = -1  # 从-1开始编号

        # 删除所有现有任务
        GanttProject.objects.all().delete()

        # 重新编号并保存任务
        for task in data['tasks']:
            task['id'] = current_id  # 为任务分配新的负数ID
            GanttProject.objects.update_or_create(
                project_id=current_id,
                defaults=generate_task_defaults(task)
            )
            current_id -= 1  # 递减ID

        return JsonResponse({'status': 'success', 'message': 'Gantt data saved successfully.'})
    return JsonResponse({'status': 'fail', 'message': 'Invalid request method.'})

def generate_task_defaults(task):
    return {
        'name': task.get('name', ''),
        'progress': task.get('progress', 0),
        'progress_by_worklog': task.get('progressByWorklog', False),
        'relevance': task.get('relevance', 0),
        'type': task.get('type', ''),
        'type_id': task.get('typeId', ''),
        'description': task.get('description', ''),
        'code': task.get('code', ''),
        'level': task.get('level', 0),
        'status': task.get('status', 'STATUS_ACTIVE'),
        'depends': task.get('depends', ''),
        'can_write': task.get('canWrite', True),
        'start': datetime.fromtimestamp(task.get('start') / 1000),  # 转换时间戳为日期时间
        'duration': task.get('duration', 0),
        'end': datetime.fromtimestamp(task.get('end') / 1000),  # 转换时间戳为日期时间
        'start_is_milestone': task.get('startIsMilestone', False),
        'end_is_milestone': task.get('endIsMilestone', False),
        'collapsed': task.get('collapsed', False),
        'assigs': task.get('assigs', []),
        'has_child': task.get('hasChild', False),
    }

def get_gantt_data(request):
    tasks = GanttProject.objects.all().values()
    task_list = []

    # 格式化任务数据
    for task in tasks:
        task_list.append({
            'id': task['project_id'],
            'name': task['name'],
            'progress': task['progress'],
            'progressByWorklog': task['progress_by_worklog'],
            'relevance': task['relevance'],
            'type': task['type'],
            'typeId': task['type_id'],
            'description': task['description'],
            'code': task['code'],
            'level': task['level'],
            'status': task['status'],
            'depends': task['depends'],
            'canWrite': task['can_write'],
            'start': int(task['start'].timestamp() * 1000),
            'duration': task['duration'],
            'end': int(task['end'].timestamp() * 1000),
            'startIsMilestone': task['start_is_milestone'],
            'endIsMilestone': task['end_is_milestone'],
            'collapsed': task['collapsed'],
            'assigs': task['assigs'],
            'hasChild': task['has_child']
        })

    response_data = {
        "tasks": task_list,
        "resources": [
            {"id": "tmp_1", "name": "Resource 1"},
            {"id": "tmp_2", "name": "Resource 2"},
            {"id": "tmp_3", "name": "Resource 3"},
            {"id": "tmp_4", "name": "Resource 4"}
        ],
        "roles": [
            {"id": "tmp_1", "name": "Project Manager"},
            {"id": "tmp_2", "name": "Worker"},
            {"id": "tmp_3", "name": "Stakeholder"},
            {"id": "tmp_4", "name": "Customer"}
        ],
        "canWrite": True,
        "canDelete": True,
        "canWriteOnParent": True,
        "canAdd": True
    }

    return JsonResponse({"status": "success", "data": response_data})

@login_required
def experiment_tasks_apply(request):
    if request.method == 'POST':
        try:
            # 处理试验时长，使用parse_chinese_duration函数
            run_time_str = request.POST.get('run')
            try:
                test_time = int(parse_chinese_duration(run_time_str))
            except:
                # 如果无法解析，尝试作为纯数字处理
                test_time = int(run_time_str) if run_time_str.isdigit() else 0
            
            # 创建新的 TaskApplication 实例
            task = TaskApplication(
                task_number=request.POST.get('taskNumber'),
                department=request.POST.get('department'),
                entrusted_person=request.POST.get('entrusted'),
                project_type=request.POST.get('projectName'),
                project_code=request.POST.get('projectCode'),
                sample_name=request.POST.get('sampleName'),
                sample_stage=request.POST.get('sampleStage'),
                sample_quantity=int(request.POST.get('sampleNumber')),
                sample_code=request.POST.get('sampleCode'),
                is_outsourced=request.POST.get('isSeparated'),
                requires_report=request.POST.get('isRequiredReport'),
                storage_period=request.POST.get('savePeriod'),
                oil_storage=request.POST.get('storage'),
                oil_amount=request.POST.get('oilAmount'),
                needs_judgment=request.POST.get('isJudgment'),
                test_content=request.POST.get('testContent'),
                test_contentExtra=request.POST.get('testContentExtra'),
                test_basis=request.POST.get('testBasis'),
                test_specs=request.POST.get('testSpecs'),  
                debug_time=int(request.POST.get('debug')),
                test_time=test_time,  # 使用解析后的时间
                estimated_cost=float(request.POST.get('cost')),
                task_source=request.POST.get('confirmation'),
                business_type=request.POST.get('testtype')
            )
            # 保存到数据库
            task.save()
            
            return JsonResponse({'status': 'success', 'message': '任务申请已提交'})
        except Exception as e:
            logger.error(f"保存任务申请失败: {str(e)}")
            return JsonResponse({'status': 'error', 'message': str(e)})

    # 简化任务数据的组织方式，移除筛选相关代码
    tasks = TaskApplication.objects.all().order_by('-task_number').values(
        'task_number', 'project_code', 'test_content'
    )
    years_data = {}
    
    for task in tasks:
        task_number = task['task_number']
        year = task_number[:4]
        month = task_number[4:6]
        
        if year not in years_data:
            years_data[year] = {}
        if month not in years_data[year]:
            years_data[year][month] = []
            
        years_data[year][month].append(task)

    context = {
        'page_title': '任务委托',
        'can_edit': request.user.has_perm('comprehensive.change_department'),
        'years_data': years_data
    }
    return render(request, 'experiment_tasks_apply.html', context)

@login_required
def get_task_details(request, task_number):
    try:
        task = TaskApplication.objects.get(task_number=task_number)
        return JsonResponse({
            'status': 'success',
            'task_number': task.task_number,
            'department': task.department,
            'entrusted_person': task.entrusted_person,
            'project_type': task.project_type,
            'project_code': task.project_code,
            'sample_name': task.sample_name,
            'sample_stage': task.sample_stage,
            'sample_quantity': task.sample_quantity,
            'sample_code': task.sample_code,
            'is_outsourced': task.is_outsourced,
            'requires_report': task.requires_report,
            'storage_period': task.storage_period,
            'oil_storage': task.oil_storage,
            'oil_amount': task.oil_amount,
            'test_content': task.test_content,
            'test_contentExtra': task.test_contentExtra,
            'test_basis': task.test_basis,
            'test_specs': task.test_specs,
            'debug_time': task.debug_time,
            'test_time': task.test_time,
            'estimated_cost': task.estimated_cost,
            'task_source': task.task_source,
            'business_type': task.business_type,
        })
    except TaskApplication.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': '任务不存在'}, status=404)

def experiment_progress(request):
    context = {
        'page_title': '试验进度',
    }
    return render(request, 'experiment_progress.html', context)


def extract_table_from_pdf(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[0]
        tables = page.extract_tables()
        return tables

@csrf_exempt
@login_required
def parse_task_pdf(request):
    if request.method == 'POST' and request.FILES.get('pdf'):
        try:
            pdf_file = request.FILES['pdf']
            tables = extract_table_from_pdf(pdf_file)

            if tables:
                result_dict = {}
                # 提取委托单位/部门、样品状态/阶段、试验时长、试后件保存期
                result_dict['编号'] = tables[0][1][5]
                result_dict['委托单位/部门'] = tables[0][2][1]
                result_dict['委托人'] = tables[0][2][5]
                result_dict['项目名称'] = tables[0][3][1]
                
                # 确保样品数量是数字
                sample_quantity = tables[0][4][3]
                try:
                    # 尝试提取数字部分
                    sample_quantity = ''.join(filter(str.isdigit, sample_quantity))
                    sample_quantity = int(sample_quantity) if sample_quantity else 1
                except ValueError:
                    sample_quantity = 1  # 如果转换失败，设置默认值为1
                
                result_dict['样品数量'] = str(sample_quantity)
                result_dict['样品状态/阶段'] = tables[0][4][5]
                result_dict['样品编号'] = tables[0][5][1]
                result_dict['是否需要报告'] = tables[0][6][1]
                result_dict['是否分包'] = tables[0][7][1]
                result_dict['试后件保存期'] = tables[0][8][1]
                result_dict['任务来源'] = tables[0][9][1]
                result_dict['业务类型'] = tables[0][10][1]

                test_contents = tables[0][11][0].strip().replace('\n', '').replace('试验目的和要求：','*').replace('任务内容、目的与要求试验内容：','')
                result_dict['试验内容'] = test_contents.split('*')[0]
                result_dict['试验目的和要求'] = test_contents.split('*')[1]

                result_dict['费用：'] = tables[0][12][1]
                result_dict['试验时长'] = parse_chinese_duration(tables[0][12][5])
                result_dict['试验依据：'] = tables[0][13][1]
                result_dict['试验依据内容：'] = tables[0][14][1]

                # 按照字段映射关系返回数据
                task_data = {
                    'status': 'success',
                    'taskNumber': result_dict.get('编号', ''),
                    'department': result_dict.get('委托单位/部门', ''),
                    'entrustedPerson': result_dict.get('委托人', ''),
                    'projectCode': result_dict.get('项目名称', ''),
                    'sampleStage': result_dict.get('样品状态/阶段', ''),
                    'sampleNumber': str(sample_quantity),
                    'sampleCode': result_dict.get('样品编号', ''),
                    'isSeparated': result_dict.get('是否分包', '否'),
                    'isRequiredReport': result_dict.get('是否需要报告', '是'),
                    'savePeriod': result_dict.get('试后件保存期', ''),
                    'testContent': result_dict.get('试验内容', ''),
                    'testContentExtra': result_dict.get('试验目的和要求', ''),
                    'testSpecs': result_dict.get('试验依据内容：', ''),
                    'run': result_dict.get('试验时长', ''),
                    'cost': result_dict.get('费用：', ''),
                    'confirmation': result_dict.get('任务来源', ''),
                    'testtype': result_dict.get('业务类型', '')
                }
                return JsonResponse(task_data)
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': '未找到表格数据'
                })

        except Exception as e:
            logger.error(f"解析PDF失败: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            })

    return JsonResponse({'status': 'error', 'message': '无效的请求'})

def parse_chinese_duration(time_str):
    pattern = r'(\d+(?:\.\d+)?)\s*([天小时分钟]+)'
    matches = re.findall(pattern, time_str)

    total_hours = 0
    unit_map = {
        '月': 24 * 30,
        '天': 24,
        '小时': 1,
        '分钟': 1 / 60
    }

    for value, unit in matches:
        value = float(value)
        for chinese_unit, factor in unit_map.items():
            if chinese_unit in unit:
                total_hours += value * factor
                break
        else:
            raise ValueError(f"无法识别的时间单位: {unit}")

    return total_hours

@login_required
@permission_required('experiment.delete_taskapplication', raise_exception=True)
def delete_task_application(request):
    if request.method == 'POST':
        try:
            task_number = request.POST.get('taskNumber')
            if not task_number:
                return JsonResponse({
                    'status': 'error',
                    'message': '任务单号不能为空'
                }, status=400)

            task = TaskApplication.objects.get(task_number=task_number)
            task.delete()
            
            return JsonResponse({
                'status': 'success',
                'message': f'任务单 {task_number} 已成功删除'
            })
        except TaskApplication.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': '未找到指定的任务单'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'删除失败：{str(e)}'
            }, status=500)
    
    return JsonResponse({
        'status': 'error',
        'message': '不支持的请求方法'
    }, status=405)

@login_required
@permission_required('experiment.change_taskapplication', raise_exception=True)
def update_task_application(request):
    if request.method == 'POST':
        try:
            task_number = request.POST.get('taskNumber')
            if not task_number:
                return JsonResponse({
                    'status': 'error',
                    'message': '任务单号不能为空'
                }, status=400)

            # 检查任务是否存在
            task = TaskApplication.objects.get(task_number=task_number)
            
            # 处理试验时长，使用parse_chinese_duration函数
            run_time_str = request.POST.get('run')
            if run_time_str:
                try:
                    test_time = int(parse_chinese_duration(run_time_str))
                except:
                    # 如果无法解析，尝试作为纯数字处理
                    test_time = int(run_time_str) if run_time_str.isdigit() else task.test_time
            else:
                test_time = task.test_time
            
            # 更新任务信息
            task.department = request.POST.get('department', task.department)
            task.entrusted_person = request.POST.get('entrusted', task.entrusted_person)
            task.project_type = request.POST.get('projectName', task.project_type)
            task.project_code = request.POST.get('projectCode', task.project_code)
            task.sample_name = request.POST.get('sampleName', task.sample_name)
            task.sample_stage = request.POST.get('sampleStage', task.sample_stage)
            task.sample_quantity = int(request.POST.get('sampleNumber', task.sample_quantity))
            task.sample_code = request.POST.get('sampleCode', task.sample_code)
            task.is_outsourced = request.POST.get('isSeparated', task.is_outsourced)
            task.requires_report = request.POST.get('isRequiredReport', task.requires_report)
            task.storage_period = request.POST.get('savePeriod', task.storage_period)
            task.oil_storage = request.POST.get('storage', task.oil_storage)
            task.oil_amount = request.POST.get('oilAmount', task.oil_amount)
            task.needs_judgment = request.POST.get('isJudgment', task.needs_judgment)
            task.test_content = request.POST.get('testContent', task.test_content)
            task.test_contentExtra = request.POST.get('testContentExtra', task.test_contentExtra)
            task.test_basis = request.POST.get('testBasis', task.test_basis)
            task.test_specs = request.POST.get('testSpecs', task.test_specs)
            task.debug_time = int(request.POST.get('debug', task.debug_time))
            task.test_time = test_time  # 使用解析后的时间
            task.estimated_cost = float(request.POST.get('cost', task.estimated_cost))
            task.task_source = request.POST.get('confirmation', task.task_source)
            task.business_type = request.POST.get('testtype', task.business_type)

            task.save()
            
            return JsonResponse({
                'status': 'success',
                'message': f'任务单 {task_number} 已成功更新'
            })

        except TaskApplication.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': '未找到指定的任务单'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'更新失败：{str(e)}'
            }, status=500)
    
    return JsonResponse({
        'status': 'error',
        'message': '不支持的请求方法'
    }, status=405)

@login_required
def search_task_applications(request):
    """搜索任务申请数据"""
    query = request.GET.get('query', '')
    
    if query:
        # 搜索包含查询字符串的任务单号或项目代号
        tasks = TaskApplication.objects.filter(
            models.Q(task_number__icontains=query) | 
            models.Q(project_code__icontains=query)
        ).values('task_number', 'project_code', 'sample_code', 'test_content', 'test_specs')
    else:
        # 如果没有查询字符串，返回最近的20条记录
        tasks = TaskApplication.objects.all().order_by('-created_at')[:20].values(
            'task_number', 'project_code', 'sample_code', 'test_content', 'test_specs'
        )
    
    return JsonResponse({'tasks': list(tasks)})

## 设置试验统计的视图函数
#============================================================
# 设置试验运行登记视图函数
def experiment_tasks_run(request):
    try:
        # 获取设备列表，按equipment_id升序排列
        equipment_list = Equipment.objects.all().order_by('equipment_id').values('equipment_id', 'name')
        
        # 获取TaskApplication中的任务单号和详细信息
        task_applications = list(TaskApplication.objects.all().values(
            'task_number', 'project_code', 'test_content', 'sample_code', 'sample_name'
        ).order_by('-task_number'))  # 按任务单号降序排序，转换为列表
        
        # 处理选择的设备
        selected_device = request.GET.get('device_number', '')
        device_history = []
        device_stats = {
            'progress_avg': 0,
            'records_count': 0,
            'running_total': 0,
            'sample_fault_total': 0
        }

        # 如果有选择设备，获取该设备的历史记录
        if selected_device:
            try:
                # 计算一年前的日期
                one_year_ago = datetime.now() - timedelta(days=365)

                # 获取设备一年内的历史记录
                device_records = Device_run.objects.filter(
                    device_number=selected_device,
                    date__gte=one_year_ago
                ).order_by('-date')

                # 按年月分组
                history_data = {}

                for record in device_records:
                    year = record.date.year
                    month = record.date.month

                    # 创建年月键
                    year_month_key = f"{year}年{month}月"

                    if year_month_key not in history_data:
                        history_data[year_month_key] = []

                    # 添加记录到对应年月分组
                    history_data[year_month_key].append({
                        'id': record.id,
                        'task_number': record.task_number,
                        'sample_number': record.sample_number,
                        'date': record.date.strftime('%Y-%m-%d'),
                        'progress': record.progress,
                        'bench_status': record.bench_status,
                        'running': float(record.running),
                        'debugging': float(record.debugging),
                        'sample_fault': float(record.sample_fault)
                    })

                # 转换为有序列表格式
                for year_month, records in sorted(history_data.items(), reverse=True):
                    device_history.append({
                        'year_month': year_month,
                        'records': records
                    })

                # 计算第一个月的统计数据（如果有数据）
                if device_history and device_history[0]['records']:
                    first_month = device_history[0]
                    total_progress = 0
                    total_running = 0
                    total_sample_fault = 0
                    records_count = len(first_month['records'])

                    for record in first_month['records']:
                        # 提取进度数值
                        progress = record.get('progress', '0%')
                        if progress and isinstance(progress, str) and '%' in progress:
                            progress = float(progress.replace('%', ''))
                        else:
                            progress = 0
                        total_progress += progress

                        # 累计运行时长
                        total_running += float(record.get('running', 0))

                        # 累计样件故障时长
                        total_sample_fault += float(record.get('sample_fault', 0))

                    # 计算统计数据
                    device_stats = {
                        'progress_avg': round(total_progress / records_count) if records_count > 0 else 0,
                        'records_count': records_count,
                        'running_total': round(total_running, 1),
                        'sample_fault_total': round(total_sample_fault, 1)
                    }
            except Exception as e:
                import traceback
                print(f"获取设备历史记录出错: {str(e)}")
                print(traceback.format_exc())
        
        # 获取Device_run中的任务信息，按日期降序排序
        context = {
            'page_title': '运行登记',
            'equipment_list': list(equipment_list),
            'selected_device': selected_device,
            'device_history': device_history,
            'device_stats': device_stats,
            'today_date': datetime.now()  # 添加当前日期到上下文
        }
        
        return render(request, 'experiment_tasks_run.html', context)
    
    except Exception as e:
        # 记录错误并提供友好的错误提示
        logger.error(f"加载运行登记页面错误: {str(e)}")
        context = {
            'page_title': '运行登记',
            'error_message': '加载数据时发生错误，请刷新页面或联系管理员',
            'equipment_list': [],
            'task_applications': [],
            'device_tasks': [],
            'today_date': datetime.now()  # 添加当前日期到上下文
        }
        return render(request, 'experiment_tasks_run.html', context)
    
# 设备运行信息API视图函数
#============================================================
@csrf_exempt
@login_required
def save_device_run(request):
    """保存设备运行信息记录"""
    if request.method == 'POST':
        try:
            # 获取记录ID（如果存在表示更新）
            record_id = request.POST.get('id', '')
            
            # 准备数据
            task_number = request.POST.get('task_number')
            date_str = request.POST.get('date')
            device_number = request.POST.get('device_number')
            bench_status = request.POST.get('bench_status', '')
            remarks = request.POST.get('remarks', '').strip()
            
            # 验证四个时长总和不为零
            try:
                debugging = float(request.POST.get('debugging', 0) or 0)
                running = float(request.POST.get('running', 0) or 0)
                sample_fault = float(request.POST.get('sample_fault', 0) or 0)
                bench_fault = float(request.POST.get('bench_fault', 0) or 0)
                
                total_time = debugging + running + sample_fault + bench_fault
                
                if total_time == 0:
                    message = '四个时长（调试、运行、样件故障、台架故障）的总和不能为零'
                    logger.warning(f"保存失败: {message}")
                    
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'status': 'error',
                            'message': message
                        }, status=400)
                    
                    messages.error(request, message)
                    return redirect('experiment:experiment_tasks_run')
                
                # 新增验证：检查台架状态与时长匹配
                status_time_valid = True
                status_time_message = ''
                
                if bench_status == '试验调试' and debugging <= 0:
                    status_time_valid = False
                    status_time_message = '台架状态为"试验调试"时，调试时长必须大于零'
                elif bench_status == '试验运行' and running <= 0:
                    status_time_valid = False
                    status_time_message = '台架状态为"试验运行"时，运行时长必须大于零'
                elif bench_status == '样件故障' and sample_fault <= 0:
                    status_time_valid = False
                    status_time_message = '台架状态为"样件故障"时，样件故障时长必须大于零'
                elif bench_status == '设备故障' and bench_fault <= 0:
                    status_time_valid = False
                    status_time_message = '台架状态为"设备故障"时，台架故障时长必须大于零'
                
                if not status_time_valid:
                    logger.warning(f"保存失败: {status_time_message}")
                    
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'status': 'error',
                            'message': status_time_message
                        }, status=400)
                    
                    messages.error(request, status_time_message)
                    return redirect('experiment:experiment_tasks_run')
                
                # 新增验证：当有故障时长大于0时，备注不能为空
                if (sample_fault > 0 or bench_fault > 0) and not remarks:
                    message = '当"样件故障时长"或"台架故障时长"大于零时，备注不能为空'
                    logger.warning(f"保存失败: {message}")
                    
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'status': 'error',
                            'message': message
                        }, status=400)
                    
                    messages.error(request, message)
                    return redirect('experiment:experiment_tasks_run')
                
                # 新增验证：如果运行时长大于零，新进度应大于原始进度
                if running > 0 and record_id:
                    try:
                        existing_record = Device_run.objects.get(id=record_id)
                        existing_progress = float(existing_record.progress.replace('%', ''))
                        current_progress = float(request.POST.get('progress', '0').replace('%', ''))
                        
                        if current_progress <= existing_progress:
                            message = f'运行时长大于零时，试验进度应该比原来的进度({existing_progress}%)有所增加'
                            logger.warning(f"保存失败: {message}")
                            
                            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                                return JsonResponse({
                                    'status': 'error',
                                    'message': message
                                }, status=400)
                            
                            messages.error(request, message)
                            return redirect('experiment:experiment_tasks_run')
                    except Device_run.DoesNotExist:
                        logger.info("没有找到现有记录，跳过进度验证")
                    except Exception as e:
                        logger.warning(f"进度验证异常: {str(e)}")
                
            except ValueError:
                logger.warning("时长值转换失败，将继续进行其他验证")
            
            # 后端验证必填字段
            required_fields = {
                'task_number': '任务单号',
                'task_status': '任务状态', 
                'transmission_model': '样件型号',
                'test_content': '试验内容',
                'date': '日期',
                'sample_number': '样品编号',
                'device_number': '设备编号',
                'bench_status': '台架状态'
            }
            
            missing_fields = []
            for field, field_name in required_fields.items():
                value = request.POST.get(field, '').strip()
                if not value:
                    missing_fields.append(field_name)
            
            if missing_fields:
                missing_list = '、'.join(missing_fields)
                message = f'以下必填字段不能为空: {missing_list}'
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'status': 'error',
                        'message': message
                    }, status=400)
                
                messages.error(request, message)
                return redirect('experiment:experiment_tasks_run')
            
            # 如果提供了记录ID，检查关键字段是否有变化
            if record_id:
                try:
                    # 查找现有记录
                    existing_record = Device_run.objects.get(id=record_id)
                    
                    # 检查三个关键字段是否有变化
                    existing_date_str = existing_record.date.strftime('%Y-%m-%d')
                    if (existing_record.device_number != device_number or 
                        existing_record.task_number != task_number or 
                        existing_date_str != date_str):
                        
                        logger.info(f"检测到关键字段变更，将创建新记录而不是更新。原始值：device={existing_record.device_number}, task={existing_record.task_number}, date={existing_date_str}，新值：device={device_number}, task={task_number}, date={date_str}")
                        
                        # 关键字段有变化，清空记录ID，创建新记录
                        record_id = ''
                except Device_run.DoesNotExist:
                    # 如果记录不存在，也创建新记录
                    logger.info(f"提供的记录ID {record_id} 不存在，将创建新记录")
                    record_id = ''
            
            # 如果没有ID，则自动生成一个顺序ID
            if not record_id:
                # 获取当前年月
                current_date = datetime.strptime(date_str, '%Y-%m-%d')
                year_month = current_date.strftime('%Y%m')
                
                # 查找该年月下最大的序号
                latest_records = Device_run.objects.filter(
                    id__startswith=f"DR{year_month}"
                ).order_by('-id')
                
                if latest_records.exists():
                    # 如果存在记录，提取最后一个记录的序号并加1
                    latest_id = latest_records[0].id
                    try:
                        # 假设格式为 DR2025060001, 提取最后的序号部分
                        seq_number = int(latest_id[8:]) + 1
                    except ValueError:
                        # 如果提取失败，从1开始
                        seq_number = 1
                else:
                    # 如果不存在记录，从1开始
                    seq_number = 1
                
                # 生成新ID：DR + 年月 + 4位序号，例如DR2025060001
                record_id = f"DR{year_month}{seq_number:04d}"
                logger.debug(f"自动生成设备运行记录ID: {record_id}")
            
            # 准备设备运行数据
            device_data = {
                'task_number': task_number,
                'task_status': request.POST.get('task_status'),
                'transmission_model': request.POST.get('transmission_model'),
                'test_content': request.POST.get('test_content'),
                # 修复日期时区问题：将日期设置为当天中午12点，避免时区转换导致日期变化
                'date': datetime.strptime(date_str + ' 12:00:00', '%Y-%m-%d %H:%M:%S'),
                'sample_number': request.POST.get('sample_number'),
                'device_number': device_number,
                'bench_status': bench_status,
                'remarks': remarks,
            }
            
            # 处理数值字段，确保有默认值
            try:
                device_data['debugging'] = float(request.POST.get('debugging', 0))
            except ValueError:
                device_data['debugging'] = 0
                
            try:
                device_data['running'] = float(request.POST.get('running', 0))
            except ValueError:
                device_data['running'] = 0
                
            try:
                device_data['sample_fault'] = float(request.POST.get('sample_fault', 0))
            except ValueError:
                device_data['sample_fault'] = 0
                
            try:
                device_data['bench_fault'] = float(request.POST.get('bench_fault', 0))
            except ValueError:
                device_data['bench_fault'] = 0
                
            try:
                device_data['idle'] = float(24-device_data['debugging']-device_data['running']-device_data['sample_fault']-device_data['bench_fault'])
            except ValueError:
                device_data['idle'] = 0
            
            # 处理进度字段，确保是字符串格式
            progress = request.POST.get('progress', '0')
            device_data['progress'] = f"{progress}%"
            
            device_data['dvp_plan'] = request.POST.get('dvp_plan', '是')
            device_data['responsible_person'] = request.POST.get('responsible_person', request.user.username)
                
            # 更新或创建记录
            try:
                device_run, created = Device_run.objects.update_or_create(
                    id=record_id,
                    defaults=device_data
                )
                
                action = "创建" if created else "更新"
                
                # 如果是AJAX请求，返回JSON响应
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'status': 'success',
                        'message': f'设备运行信息已{action}',
                        'record_id': record_id,
                        'created': created
                    })
                
                # 否则，使用消息通知并重定向
                messages.success(request, f'设备运行信息已成功{action}！记录ID：{record_id}')
                return redirect('experiment:experiment_tasks_run')
                
            except Exception as db_error:
                logger.error(f"数据库操作失败: {str(db_error)}")
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'status': 'error',
                        'message': f'数据库操作失败: {str(db_error)}',
                        'detail': str(db_error)
                    }, status=500)
                
                messages.error(request, f'数据库操作失败: {str(db_error)}')
                return redirect('experiment:experiment_tasks_run')
            
        except Exception as e:
            import traceback
            error_traceback = traceback.format_exc()
            logger.error(f"保存设备运行信息失败: {str(e)}\n{error_traceback}")
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error',
                    'message': f'保存失败: {str(e)}',
                    'traceback': error_traceback
                }, status=500)
            
            messages.error(request, f'保存失败: {str(e)}')
            return redirect('experiment:experiment_tasks_run')
    
    # 对于GET请求，重定向到表单页面
    return redirect('experiment:experiment_tasks_run')

@login_required
def get_device_run(request, record_id):
    """获取特定设备运行记录"""
    try:
        device_run = Device_run.objects.get(id=record_id)
        
        return JsonResponse({
            'status': 'success',
            'data': {
                'id': device_run.id,
                'task_number': device_run.task_number,
                'task_status': device_run.task_status,
                'transmission_model': device_run.transmission_model,
                'test_content': device_run.test_content,
                'date': device_run.date.strftime('%Y-%m-%d'),
                'sample_number': device_run.sample_number,
                'device_number': device_run.device_number,
                'bench_status': device_run.bench_status,
                'remarks': device_run.remarks,
                'debugging': float(device_run.debugging),
                'running': float(device_run.running),
                'sample_fault': float(device_run.sample_fault),
                'bench_fault': float(device_run.bench_fault),
                'idle': float(device_run.idle),
                'progress': device_run.progress,
                'dvp_plan': device_run.dvp_plan,
                'responsible_person': device_run.responsible_person,
            }
        })
    except Device_run.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': '未找到指定的设备运行记录'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'获取记录失败: {str(e)}'
        }, status=500)

@csrf_exempt
@login_required
@permission_required('experiment.delete_device_run', raise_exception=True)
def delete_device_run(request):
    """删除设备运行记录"""
    if request.method == 'POST':
        try:
            record_id = request.POST.get('record_id')
            if not record_id:
                return JsonResponse({
                    'status': 'error',
                    'message': '记录ID不能为空'
                }, status=400)
                
            device_run = Device_run.objects.get(id=record_id)
            device_run.delete()
            
            return JsonResponse({
                'status': 'success',
                'message': f'记录 {record_id} 已成功删除'
            })
        except Device_run.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': '未找到指定的记录'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'删除失败: {str(e)}'
            }, status=500)
    
    return JsonResponse({
        'status': 'error',
        'message': '不支持的请求方法'
    }, status=405)

# 设置试验履历表视图函数
@login_required
def experiment_tasks_log(request):
    # 从Equipment模型获取所有设备列表
    equipment_list = Equipment.objects.all().values('equipment_id', 'name')
    
    context = {
        'page_title': '履历表登记',
        'today_date': datetime.now(),  # 添加当前日期到上下文
        'equipment_list': equipment_list,  # 添加设备列表到上下文
    }
    return render(request, 'experiment_tasks_log.html', context)

# 获取所有试验履历表记录
@login_required
def get_experiment_logs(request):
    """获取试验履历表记录，支持按时间筛选"""
    try:
        filter_type = request.GET.get('filter', 'all')
        
        # 根据筛选类型确定查询范围
        if filter_type == 'week':
            # 最近一周的记录
            start_date = datetime.now() - timedelta(days=7)
            logs = ExperimentLog.objects.filter(log_date__gte=start_date)
        elif filter_type == 'month':
            # 最近一个月的记录
            start_date = datetime.now() - timedelta(days=30)
            logs = ExperimentLog.objects.filter(log_date__gte=start_date)
        elif filter_type == 'year':
            # 最近一年的记录
            start_date = datetime.now() - timedelta(days=365)
            logs = ExperimentLog.objects.filter(log_date__gte=start_date)
        else:
            # 所有记录，限制50条，避免数据量过大
            logs = ExperimentLog.objects.all()[:50]
        
        # 将记录转换为JSON格式
        logs_data = []
        for log in logs:
            logs_data.append({
                'log_id': log.log_id,
                'task_number': log.task_number,
                'project_code': log.project_code,
                'sample_number': log.sample_number,
                'test_content': log.test_content,
                'equipment_id': log.equipment_id,  # 添加设备编号
                'stop_duration': float(log.stop_duration),
                'log_date': log.log_date.strftime('%Y-%m-%dT%H:%M:%S'),
                'alarm_phenomenon': log.alarm_phenomenon,
                'alarm_reason': log.alarm_reason,
                'solution': log.solution,
                'solver': log.solver,
                'data_path': log.data_path,
                'analysis_report': log.analysis_report,  # 添加分析报告字段
                'remarks': log.remarks
            })
        
        return JsonResponse({'status': 'success', 'logs': logs_data})
    except Exception as e:
        logger.error(f"获取试验履历表记录失败: {str(e)}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

# 获取单条履历表记录
@login_required
def get_experiment_log(request, log_id):
    """获取单条试验履历表记录"""
    try:
        log = ExperimentLog.objects.get(log_id=log_id)
        
        log_data = {
            'log_id': log.log_id,
            'task_number': log.task_number,
            'project_code': log.project_code,
            'sample_number': log.sample_number,
            'test_content': log.test_content,
            'equipment_id': log.equipment_id,  # 添加设备编号
            'stop_duration': float(log.stop_duration),
            'log_date': log.log_date.strftime('%Y-%m-%dT%H:%M:%S'),
            'alarm_phenomenon': log.alarm_phenomenon,
            'alarm_reason': log.alarm_reason,
            'solution': log.solution,
            'solver': log.solver,
            'data_path': log.data_path,
            'analysis_report': log.analysis_report,  # 添加分析报告字段
            'remarks': log.remarks
        }
        
        return JsonResponse({'status': 'success', 'data': log_data})
    except ExperimentLog.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': '未找到指定的履历表记录'}, status=404)
    except Exception as e:
        logger.error(f"获取试验履历表记录失败: {str(e)}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

# 保存履历表记录
@csrf_exempt
@login_required
def save_experiment_log(request):
    """保存试验履历表记录"""
    logger.info(f"收到保存履历表请求: 方法={request.method}, 用户={request.user.username}")
    logger.info(f"POST数据: {request.POST}")
    logger.info(f"GET数据: {request.GET}")
    
    if request.method == 'POST':
        try:
            # 获取记录ID，判断是新增还是编辑
            log_id = request.POST.get('log_id')
            logger.info(f"处理记录ID: {log_id}")
            
            # 检查是否只更新分析报告字段（特殊处理删除报告功能）
            if log_id and 'analysis_report' in request.POST and len(request.POST) <= 3:  # log_id, analysis_report 和 csrfmiddlewaretoken
                logger.info(f"检测到仅更新分析报告字段的请求")
                try:
                    # 查找现有记录
                    log = ExperimentLog.objects.get(log_id=log_id)
                    # 更新分析报告字段
                    log.analysis_report = request.POST.get('analysis_report', '')
                    log.save(update_fields=['analysis_report', 'updated_at'])
                    
                    return JsonResponse({
                        'status': 'success',
                        'message': '分析报告已成功更新'
                    })
                except ExperimentLog.DoesNotExist:
                    logger.warning(f"更新分析报告失败：记录 {log_id} 不存在")
                    return JsonResponse({
                        'status': 'error',
                        'message': f'记录 {log_id} 不存在'
                    }, status=404)
                except Exception as e:
                    logger.error(f"更新分析报告失败: {str(e)}")
                    return JsonResponse({
                        'status': 'error',
                        'message': f'更新分析报告失败: {str(e)}'
                    }, status=500)
            
            # 验证必填字段
            required_fields = {
                'task_number': '任务单编号',
                'project_code': '项目代号',
                'sample_number': '样件编号',
                'test_content': '试验内容',
                'equipment_id': '设备编号',  # 添加设备编号必填字段
                'stop_duration': '停止时长',
                'log_date': '登记日期',
                'alarm_phenomenon': '报警现象',
                'alarm_reason': '报警原因',
                'solution': '解决办法',
                'solver': '解决人'
            }
            
            missing_fields = []
            for field, field_name in required_fields.items():
                value = request.POST.get(field, '').strip()
                if not value:
                    missing_fields.append(field_name)
                    logger.warning(f"缺少必填字段: {field_name}")
            
            if missing_fields:
                missing_list = '、'.join(missing_fields)
                logger.warning(f"表单验证失败，缺少必填字段: {missing_list}")
                
                # 检查是否是AJAX请求
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'status': 'error',
                        'message': f'以下必填字段不能为空: {missing_list}'
                    }, status=400)
                else:
                    messages.error(request, f'以下必填字段不能为空: {missing_list}')
                    return redirect('experiment:experiment_tasks_log')
            
            # 处理登记日期
            try:
                log_date = datetime.strptime(request.POST.get('log_date') + ' 12:00:00', '%Y-%m-%d %H:%M:%S')
            except ValueError:
                logger.warning(f"日期格式无效: {request.POST.get('log_date')}")
                log_date = datetime.now()
                
            try:
                stop_duration = float(request.POST.get('stop_duration', 0))
            except ValueError:
                logger.warning(f"停止时长无效: {request.POST.get('stop_duration')}")
                stop_duration = 0.0
                
            # 获取五个关键字段
            task_number = request.POST.get('task_number')
            project_code = request.POST.get('project_code')
            equipment_id = request.POST.get('equipment_id')
            sample_number = request.POST.get('sample_number')
            
            # 查找是否存在具有相同四个字段的记录
            existing_records = ExperimentLog.objects.filter(
                task_number=task_number,
                project_code=project_code,
                equipment_id=equipment_id,
                sample_number=sample_number
            )
            
            # 新的处理逻辑
            if existing_records.exists():
                # 检查是否有完全匹配的记录（包括日期）
                exact_match = existing_records.filter(
                    log_date__date=log_date.date()
                ).first()
                
                if exact_match:
                    # 五个关键字段完全匹配，更新此记录
                    log_id = exact_match.log_id
                    logger.info(f"找到完全匹配的记录，将更新: {log_id}")
                    action = "更新"
                else:
                    # 日期不同，创建新记录
                    log_id = None
                    logger.info("日期不同，将创建新记录")
                    action = "创建"
            else:
                # 没有找到匹配的记录，创建新记录
                log_id = None
                logger.info("没有找到匹配的记录，将创建新记录")
                action = "创建"
            
            # 如果是新记录，自动生成ID
            if not log_id:
                # 获取当前年月
                year_month = log_date.strftime('%Y%m')
                
                # 查找该年月下最大的序号
                latest_logs = ExperimentLog.objects.filter(
                    log_id__startswith=f"EL{year_month}"
                ).order_by('-log_id')
                
                if latest_logs.exists():
                    # 提取最后一个记录的序号并加1
                    latest_id = latest_logs[0].log_id
                    try:
                        # 假设格式为 EL2025060001
                        seq_number = int(latest_id[8:]) + 1
                    except ValueError:
                        seq_number = 1
                else:
                    seq_number = 1
                
                # 生成新ID：EL + 年月 + 4位序号
                log_id = f"EL{year_month}{seq_number:04d}"
                logger.info(f"生成新记录ID: {log_id}")
                
            # 处理数据路径和分析报告文件
            data_path = request.POST.get('data_path', '')
            
            # 首先检查前端是否直接传入了analysis_report字段（用于删除报告功能）
            analysis_report = request.POST.get('analysis_report', '')
            
            # 如果没有传入analysis_report字段，或者是新增记录，再处理上传文件和现有记录的情况
            if not analysis_report:
                # 如果是更新操作，从数据库获取现有的分析报告路径
                if action == "更新" and log_id:
                    try:
                        existing_log = ExperimentLog.objects.get(log_id=log_id)
                        analysis_report = existing_log.analysis_report or ''
                    except ExperimentLog.DoesNotExist:
                        analysis_report = ''
                
                # 处理上传的分析报告文件（支持多文件）
                if 'analysis_report' in request.FILES:
                    # 获取所有上传的文件
                    upload_files = request.FILES.getlist('analysis_report')
                    upload_paths = []
                    
                    # 创建保存目录
                    upload_dir = 'media/files/Analysis_report'
                    os.makedirs(upload_dir, exist_ok=True)
                    
                    # 处理每个上传的文件
                    for upload_file in upload_files:
                        # 保留原文件名
                        original_filename = upload_file.name
                        file_date = log_date.strftime('%Y%m%d')
                        
                        # 生成一个基于时间戳的唯一前缀，确保文件名唯一
                        import time
                        timestamp = int(time.time() * 1000)
                        unique_prefix = f"{timestamp}_{log_id}_"
                        
                        # 完整文件名：唯一前缀_原始文件名
                        file_name = f"{unique_prefix}{original_filename}"
                        
                        # 保存文件
                        file_path_full = os.path.join(upload_dir, file_name)
                        with open(file_path_full, 'wb+') as destination:
                            for chunk in upload_file.chunks():
                                destination.write(chunk)
                        
                        # 将相对路径添加到上传路径列表
                        file_relative_path = f"files/Analysis_report/{file_name}"
                        upload_paths.append(file_relative_path)
                        logger.info(f"分析报告文件已保存: {file_relative_path}")
                    
                    # 如果有现有的分析报告路径，添加新的路径（以分号分隔）
                    if analysis_report and upload_paths:
                        analysis_report = f"{analysis_report};{';'.join(upload_paths)}"
                    else:
                        analysis_report = ';'.join(upload_paths)
            
            logger.info(f"最终分析报告列表: {analysis_report}")
            
            # 准备保存数据
            log_data = {
                'task_number': task_number,
                'project_code': project_code,
                'sample_number': sample_number,
                'test_content': request.POST.get('test_content'),
                'equipment_id': equipment_id,
                'stop_duration': stop_duration,
                'log_date': log_date,
                'alarm_phenomenon': request.POST.get('alarm_phenomenon'),
                'alarm_reason': request.POST.get('alarm_reason'),
                'solution': request.POST.get('solution'),
                'solver': request.POST.get('solver'),
                'data_path': data_path,
                'analysis_report': analysis_report,
                'remarks': request.POST.get('remarks', '')
            }
            
            logger.info(f"准备{action}数据: {log_data}")
            
            # 保存记录
            log, created = ExperimentLog.objects.update_or_create(
                log_id=log_id,
                defaults=log_data
            )
            
            logger.info(f"记录已{action}: {log_id}")
            
            # 检查是否是AJAX请求
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'success',
                    'message': f'履历表记录已成功{action}！',
                    'log_id': log.log_id
                })
            else:
                messages.success(request, f'履历表记录已成功{action}！')
                return redirect('experiment:experiment_tasks_log')
            
        except Exception as e:
            logger.error(f"保存履历表记录失败: {str(e)}")
            logger.error(traceback.format_exc())
            
            # 检查是否是AJAX请求
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error',
                    'message': f'保存失败: {str(e)}'
                }, status=500)
            else:
                messages.error(request, f'保存失败: {str(e)}')
                return redirect('experiment:experiment_tasks_log')
    
    else:
        return JsonResponse({
            'status': 'error',
            'message': '只支持POST请求'
        }, status=405)

# 删除履历表记录
@csrf_exempt
@login_required
def delete_experiment_log(request):
    """删除试验履历表记录"""
    if request.method == 'POST':
        try:
            log_id = request.POST.get('log_id')
            if not log_id:
                return JsonResponse({
                    'status': 'error',
                    'message': '记录ID不能为空'
                }, status=400)
            
            log = ExperimentLog.objects.get(log_id=log_id)
            log.delete()
            
            return JsonResponse({
                'status': 'success',
                'message': f'记录 {log_id} 已成功删除'
            })
        except ExperimentLog.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': '未找到指定的记录'
            }, status=404)
        except Exception as e:
            logger.error(f"删除试验履历表记录失败: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': f'删除失败: {str(e)}'
            }, status=500)
    
    return JsonResponse({
        'status': 'error',
        'message': '不支持的请求方法'
    }, status=405)

# 搜索履历表记录
@login_required
def search_experiment_logs(request):
    """搜索试验履历表记录"""
    query = request.GET.get('query', '')
    
    if query:
        # 搜索包含查询字符串的记录
        logs = ExperimentLog.objects.filter(
            models.Q(task_number__icontains=query) | 
            models.Q(project_code__icontains=query) |
            models.Q(sample_number__icontains=query)
        )
    else:
        # 如果没有查询字符串，返回最近的20条记录
        logs = ExperimentLog.objects.all().order_by('-log_date')[:20]
    
    # 将记录转换为JSON格式
    logs_data = []
    for log in logs:
        logs_data.append({
            'log_id': log.log_id,
            'task_number': log.task_number,
            'project_code': log.project_code,
            'sample_number': log.sample_number,
            'test_content': log.test_content,
            'equipment_id': log.equipment_id,  # 添加设备编号
            'stop_duration': float(log.stop_duration),
            'log_date': log.log_date.strftime('%Y-%m-%dT%H:%M:%S'),
            'alarm_phenomenon': log.alarm_phenomenon,
            'alarm_reason': log.alarm_reason,
            'solution': log.solution,
            'solver': log.solver,
            'data_path': log.data_path,
            'analysis_report': log.analysis_report,  # 添加分析报告字段
            'remarks': log.remarks
        })
    
    return JsonResponse({'status': 'success', 'logs': logs_data})

# 设置按设备统计视图函数
def experiment_statistics_device(request):
    context = {
        'page_title': '按设备统计',
    }
    return render(request, 'experiment_statistics_device.html', context)

# 设置按项目统计视图函数
def experiment_statistics_project(request):
    context = {
        'page_title': '按项目统计',
    }
    return render(request, 'experiment_statistics_project.html', context)

# 新增API：获取设备历史记录
@login_required
def get_device_history(request):
    """获取特定设备的历史运行记录，按年月分组"""
    device_number = request.GET.get('device_number', '')
    
    if not device_number:
        return JsonResponse({
            'status': 'error',
            'message': '设备编号不能为空'
        }, status=400)
    
    try:
        # 计算一年前的日期
        one_year_ago = datetime.now() - timedelta(days=365)
        
        # 获取设备一年内的历史记录
        device_records = Device_run.objects.filter(
            device_number=device_number,
            date__gte=one_year_ago
        ).order_by('-date')
        print(device_records)
        # 按年月分组
        history_data = {}
        
        for record in device_records:
            year = record.date.year
            month = record.date.month
            
            # 创建年月键
            year_month_key = f"{year}年{month}月"
            
            if year_month_key not in history_data:
                history_data[year_month_key] = []
            
            # 添加记录到对应年月分组
            history_data[year_month_key].append({
                'id': record.id,
                'task_number': record.task_number,
                'sample_number': record.sample_number,
                'date': record.date.strftime('%Y-%m-%d'),
                'progress': record.progress,
                'bench_status': record.bench_status,
                'running': float(record.running),  # 添加运行时长
                'debugging': float(record.debugging),  # 添加调试时长
                'sample_fault': float(record.sample_fault)  # 添加样件故障时长
            })
        
        # 转换为有序列表格式，以便前端展示
        history_list = []
        for year_month, records in sorted(history_data.items(), reverse=True):
            history_list.append({
                'year_month': year_month,
                'records': records
            })
        print(history_list)
        return JsonResponse({
            'status': 'success',
            'data': history_list,
            'device_number': device_number  # 返回设备编号
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'获取设备历史记录失败: {str(e)}'
        }, status=500)


