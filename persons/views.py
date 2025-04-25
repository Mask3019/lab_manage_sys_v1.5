from django.contrib.auth.decorators import login_required, permission_required
from django.template.loader import render_to_string
from django.utils.dateparse import parse_date

from .models import Person,Skill,Performance,OvertimeApplication
from django.core.exceptions import PermissionDenied
from django.templatetags.static import static
from django.db.models import Max, Avg, Q, Sum
from experiment.models import Tasks
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST
from django.middleware.csrf import get_token
from django.views.decorators.csrf import csrf_exempt
import json
from django.db.models import Count
from django.db.models.functions import ExtractYear  # 用于提取日期的年份部分
from datetime import date, datetime, timedelta
from collections import defaultdict  # 添加此行

from django.shortcuts import render, redirect
from django.utils import timezone
from django.contrib import messages
from decimal import Decimal
from django.http import JsonResponse

# Create your views here.
@login_required
def persons_list(request):
    try:
        if not request.user.has_perm('persons.view_person'):
            raise PermissionDenied
        persons = Person.objects.all().order_by('employee_id')
        user_has_permission = request.user.has_perm('persons.change_person')

        context = {
            'page_title': '人员清单',
            'persons': persons,
            'user_has_permission': user_has_permission,
        }
        return render(request, 'persons_list.html', context)
    except PermissionDenied:
        context = {
            'error_message': '您没有权限查看此页面',
        }
        return render(request, 'persons_list.html', context)

@login_required
@permission_required('persons.change_person', raise_exception=True)
def save_person(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            employee_id = data.get('employee_id')
            name = data.get('name')
            email = data.get('email')
            phone = data.get('phone')
            birth_date = data.get('birth_date')
            address = data.get('address')
            entry_date = data.get('entry_date')
            department = data.get('department')
            role = data.get('role')
            grade = data.get('grade')  # 新增字段
            expertise = data.get('expertise')  # 新增字段
            photo = data.get('photo')

            person, created = Person.objects.update_or_create(
                employee_id=employee_id,
                defaults={
                    'name': name,
                    'email': email,
                    'phone': phone,
                    'birth_date': birth_date,
                    'address': address,
                    'entry_date': entry_date,
                    'department': department,

                    'role': role,
                    'grade': grade,  # 新增字段
                    'expertise': expertise,  # 新增字段
                    'photo': photo,
                }
            )
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

@login_required
@permission_required('persons.delete_person', raise_exception=True)
def delete_person(request):
    if request.method == 'POST':
        employee_id = request.POST.get('employee_id')
        try:
            person = Person.objects.get(employee_id=employee_id)
            person.delete()
            return JsonResponse({'status': 'success'})
        except Person.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Person not found'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error'}, status=400)

def persons_skills(request):
    persons = Person.objects.all()
    current_date = timezone.now().date()  # 将当前时间转换为日期类型
    for person in persons:
        person.years_in_service = (current_date - person.entry_date).days // 365  # 计算在职时间（年）
    context = {
        'page_title': '人员能力',
        'persons': persons,
    }
    return render(request, 'persons_skills.html', context)

def get_person_details(request, person_id):
    person = get_object_or_404(Person, pk=person_id)
    data = {
        'photo': person.photo.url if person.photo else static('images/default_photo.png'),
        'name': person.name,
        'birthdate': person.birth_date,
        'level': person.grade,
        'hiredate': person.entry_date,
        'contact': person.phone,
        'address': person.address,
        'expertise': person.expertise,
        'potential': person.potential,  # 这个值可以根据你的需求进行计算
        'skill': person.skill  # 这个值可以根据你的需求进行计算
    }
    return JsonResponse(data)


def get_person_skill_data(request, person_id, set_name):
    person = get_object_or_404(Person, id=person_id)

    # 尝试获取技能数据，如果不存在则初始化为零
    try:
        skill_data = Skill.objects.get(person=person)
    except Skill.DoesNotExist:
        skill_data = None

    # 尝试获取性能数据，如果不存在则初始化为零
    try:
        performance_data = Performance.objects.get(person=person, set_name=set_name)
    except Performance.DoesNotExist:
        performance_data = None

    # 计算 professional_values 和 test_ability_values 的最大值，若无数据则为零
    professional_values_max = [
        Skill.objects.aggregate(Max('skill1'))['skill1__max'] or 0,
        Skill.objects.aggregate(Max('skill2'))['skill2__max'] or 0,
        Skill.objects.aggregate(Max('skill3'))['skill3__max'] or 0,
        Skill.objects.aggregate(Max('skill4'))['skill4__max'] or 0,
        Skill.objects.aggregate(Max('skill5'))['skill5__max'] or 0
    ]

    test_ability_values_max = [
        Performance.objects.filter(set_name=set_name).aggregate(Max('performance1'))['performance1__max'] or 0,
        Performance.objects.filter(set_name=set_name).aggregate(Max('performance2'))['performance2__max'] or 0,
        Performance.objects.filter(set_name=set_name).aggregate(Max('performance3'))['performance3__max'] or 0,
        Performance.objects.filter(set_name=set_name).aggregate(Max('performance4'))['performance4__max'] or 0,
        Performance.objects.filter(set_name=set_name).aggregate(Max('performance5'))['performance5__max'] or 0,
        Performance.objects.filter(set_name=set_name).aggregate(Max('performance6'))['performance6__max'] or 0
    ]

    # 计算 professional_values 的平均值，如果 skill_data 不存在则返回0
    professional_values_avg = 0
    if skill_data:
        professional_values_avg = int((skill_data.skill1 + skill_data.skill2 + skill_data.skill3 + skill_data.skill4 + skill_data.skill5) / 5)

    # 计算 test_ability_values 的平均值，如果 performance_data 不存在则返回0
    test_ability_values_avg = 0
    if performance_data:
        test_ability_values_avg = int((performance_data.performance1 + performance_data.performance2 +
                                    performance_data.performance3 + performance_data.performance4 +
                                    performance_data.performance5 + performance_data.performance6) / 6)

    # 计算综合值
    compress_value = int(professional_values_avg * 0.4 + test_ability_values_avg * 0.6)

    # 根据 set_name 确定 professional_content 的内容
    if set_name == 'MT':
        professional_content = ['总成耐久', '总成润滑', '总成换档', '总成性能', '零部件', '静扭']
    elif set_name == 'DCT':
        professional_content = ['总成耐久', '总成润滑', '总成换档', 'HCU', '零部件', '静扭/驻车']
    elif set_name == 'AT':
        professional_content = ['总成耐久', '总成润滑', '发动机拖动', 'HCU', '零部件', '静扭/驻车']
    elif set_name == '电驱':
        professional_content = ['总成耐久', '总成润滑', '环境试验', 'MCU', '零部件', '静扭/驻车']
    elif set_name == '混动':
        professional_content = ['总成耐久', '总成润滑', '环境试验', 'MCU', '零部件', '静扭/驻车']
    else:
        professional_content = ['总成耐久', '总成润滑', '总成换档', '总成性能', '零部件', '静扭']

    data = {
        'professional_values': [
            skill_data.skill1 if skill_data else 0,
            skill_data.skill2 if skill_data else 0,
            skill_data.skill3 if skill_data else 0,
            skill_data.skill4 if skill_data else 0,
            skill_data.skill5 if skill_data else 0
        ],
        'professional_values_max': professional_values_max,
        'professional_values_avg': professional_values_avg,
        'test_ability_values': [
            performance_data.performance1 if performance_data else 0,
            performance_data.performance2 if performance_data else 0,
            performance_data.performance3 if performance_data else 0,
            performance_data.performance4 if performance_data else 0,
            performance_data.performance5 if performance_data else 0,
            performance_data.performance6 if performance_data else 0
        ],
        'test_ability_values_max': test_ability_values_max,
        'test_ability_values_avg': test_ability_values_avg,
        'compress_value': compress_value,
        'professional_content': professional_content  # 将 professional_content 添加到返回的数据中
    }
    return JsonResponse(data)


def get_weeks_of_current_year():
    # 获取本年度所有周数（1-52/53）
    today = date.today()
    current_year = today.year
    return list(range(1, 54))  # 一年最多53周

@login_required
def persons_tasks(request):
    today = date.today()
    current_year = today.year
    current_month = today.month
    current_week = int(today.strftime('%W')) + 1
    
    selected_year = request.GET.get('year', current_year)
    selected_month = request.GET.get('month', current_month if 'month' in request.GET else '')
    selected_week = request.GET.get('week', current_week if 'week' in request.GET else '')
    selected_date = request.GET.get('date', '')

    tasks = Tasks.objects.exclude(task_status='已完成').order_by('experimenter', 'task_date')

    if 'year' in request.GET:
        tasks = tasks.filter(task_date__year=selected_year)
    if 'month' in request.GET:
        tasks = tasks.filter(task_date__month=selected_month)
    if 'week' in request.GET:
        # 修改周筛选逻辑
        try:
            selected_year = int(selected_year)
            selected_week = int(selected_week)
            # 计算该周的起始日期和结束日期
            first_day = datetime.strptime(f'{selected_year}-W{selected_week - 1}-1', '%Y-W%W-%w')  # 修正周数
            last_day = first_day + timedelta(days=6)
            tasks = tasks.filter(
                task_date__gte=first_day.date(),
                task_date__lte=last_day.date()
            )
        except ValueError as e:
            print(f"Week calculation error: {e}")
    if 'date' in request.GET:
        tasks = tasks.filter(task_date=selected_date)

    persons = Person.objects.all()
    # 计算任务总和
    total_tasks = tasks.count()
    # 提取任务日期的年份部分并去重
    task_years = Tasks.objects.exclude(task_status='已完成').annotate(year=ExtractYear('task_date')).values_list('year', flat=True).distinct().order_by('-year')
    task_months = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    task_weeks = get_weeks_of_current_year()

    # 获取筛选后的任务数据，用于生成图表
    tasks_data = tasks.values('experimenter', 'task_status').annotate(task_count=Count('task_status'))
    
    # 获取不重复的试验人员作为横坐标
    experimenters = tasks.values_list('experimenter', flat=True).distinct().order_by('experimenter')
    
    # 初始化任务状态数据，使用新的统计逻辑
    task_status_data = {}
    for task in tasks_data:
        experimenter = task['experimenter']
        if experimenter not in task_status_data:
            task_status_data[experimenter] = {
                '装调': 0,  # 对应"样件装调"
                '运行': 0,  # 对应"样件运行"
                '排查': 0,  # 对应"样件排查"和"设备排查"
                '暂停': 0,  # 对应"任务暂停"
            }
        
        # 根据任务状态累加数量
        status = task['task_status']
        count = task['task_count']
        
        if status == '样件装调':
            task_status_data[experimenter]['装调'] += count
        elif status == '样件运行':
            task_status_data[experimenter]['运行'] += count
        elif status in ['样件排查', '设备排查']:
            task_status_data[experimenter]['排查'] += count
        elif status == '任务暂停':
            task_status_data[experimenter]['暂停'] += count

    # 更新图表数据
    if experimenters:
        chart_data = {
            'experimenters': list(experimenters),
            '装调': [task_status_data[e]['装调'] for e in experimenters],
            '运行': [task_status_data[e]['运行'] for e in experimenters],
            '排查': [task_status_data[e]['排查'] for e in experimenters],
            '暂停': [task_status_data[e]['暂停'] for e in experimenters],
        }
    else:
        chart_data = {
            'experimenters': ['无数据'],
            '装调': [0],
            '运行': [0],
            '排查': [0],
            '暂停': [0],
        }

    # 将数据传递给模板
    context = {
        'tasks': tasks,
        'total_tasks': total_tasks,  # 任务总和
        'task_years': task_years,
        'task_months': task_months,
        'task_weeks': task_weeks,
        'persons': persons,
        'page_title': '任务管理',
        'user_has_permission': request.user.has_perm('persons.change_tasks'),
        'csrf_token': get_token(request),
        'chart_data': json.dumps(chart_data),  # 将图表数据传递到模板
        'selected_year': selected_year,
        'selected_month': selected_month,
        'selected_week': selected_week,
        'selected_date': selected_date,
    }
    # 判断是否为AJAX请求
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        html_task_table = render_to_string('persons_tasks.html', {
            'tasks': tasks,
            'user_has_permission': request.user.has_perm('persons.change_tasks')})
        response_data = {
            'html_task_table': html_task_table,
            'chart_data': chart_data,
            'total_tasks': total_tasks  # 将任务总数传递回前端
        }
        return JsonResponse(response_data)

    return render(request, 'persons_tasks.html', context)

@require_POST
@csrf_exempt
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
            outline = data.get('outline')
            equipment_id = data.get('equipment_id')
            task_date = data.get('task_date')
            client = data.get('client')
            experimenter = data.get('experimenter')
            schedule = data.get('schedule')
            remark = data.get('remark')

            # 解析并检查任务日期
            task_date = parse_date(task_date)
            if not task_date:
                return JsonResponse({'status': 'error', 'message': '任务日期格式不正确'}, status=400)

            # 确保任务 ID 非空
            if not task_id:
                return JsonResponse({'status': 'error', 'message': '任务单号不能为空'}, status=400)

            task, created = Tasks.objects.update_or_create(
                task_id=task_id,
                defaults={
                    'task_status': task_status,
                    'project': project,
                    'sample_id': sample_id,
                    'test_content': test_content,
                    'equipment_id': equipment_id,
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

    return JsonResponse({'status': 'error', 'message': '无效请求'}, status=400)


@require_POST
@csrf_exempt  # 如果需要在测试阶段禁用CSRF验证，可以使用此装饰器。但在生产环境中应确保CSRF保护。
def delete_task(request):
    try:
        task_id = request.POST.get('task_id')
        task = get_object_or_404(Tasks, task_id=task_id)
        task.delete()
        return JsonResponse({'status': 'success', 'message': '任务删除成功！'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


# 假设有一个函数可以获取用户的角色
def get_user_role(user):
    # 在实际应用中，应该从数据库或用户属性中获取用户角色
    # 这里为了示例，简单地使用用户名来判断角色
    if user.username.startswith('operator'):
        return 'operator'
    elif user.username.startswith('line_leader'):
        return 'line_leader'
    elif user.username.startswith('department_leader'):
        return 'department_leader'
    else:
        return 'operator'  # 默认角色为运行人员

@login_required
def persons_overtime_apply(request):
    user = request.user
    # 页面标题
    context = {
        'page_title': '加班申请',
    }

    # 获取当前时间作为默认申请日期
    application_date = timezone.now().date()
    context['application_date'] = application_date.strftime('%Y-%m-%d')

    # 将工号、提交人姓名传递到模板
    context['employee_id'] = user.username  # 工号为登录用户的用户名
    context['submitter_name'] = user.get_full_name()  # 提交人姓名为登录用户的全名

    # 默认加班人员姓名为提交人姓名
    context['overtime_employee_name'] = user.get_full_name()

    # 申请编号留空，模型会自动生成
    context['application_number'] = ''  # 将申请编号传递到模板

    # 生成从 08:00 到 23:30 的时间列表，间隔为 30 分钟
    time_options = []
    for hour in range(8, 24):  # 从08:00到23:30
        time_options.append(f'{hour:02d}:00')
        time_options.append(f'{hour:02d}:30')

    context['time_options'] = time_options

    # 获取数据库中所有的申请年份（去重）
    years = OvertimeApplication.objects.dates('application_date', 'year').distinct().order_by('-application_date')
    unique_years = sorted({year.year for year in years}, reverse=True)
    context['years'] = unique_years
    print(years)

    # 获取用户权限
    user_permissions = user.get_all_permissions()
    context['user_permissions'] = list(user_permissions)  # 转换为列表

    # 根据用户角色获取申请数据
    if user.has_perm('persons.can_approve_line_leader') or user.has_perm('persons.can_approve_department_leader'):
        # 条线领导或部门领导，显示所有数据
        applications = OvertimeApplication.objects.all()
    else:
        # 运行人员，只显示自己的数据
        applications = OvertimeApplication.objects.filter(employee_id=user.username)

    applications_list = []
    for app in applications:
        # 修改审批状态判断逻辑
        if app.general_management_approval is True:
            approval_status = '审核通过'
            status_color = 'green'
        elif app.general_management_approval is False:
            approval_status = '审核被驳回'
            status_color = 'red'
        elif app.department_leader_approval is True:
            approval_status = '待综合管理审批'
            status_color = 'blue'
        elif app.department_leader_approval is False:
            approval_status = '部门领导已驳回'
            status_color = 'red'
        elif app.line_leader_approval is True:
            approval_status = '待部门领导审批'
            status_color = '#fcb800'
        elif app.line_leader_approval is False:
            approval_status = '条线领导已驳回'
            status_color = 'red'
        else:
            approval_status = '待审批'
            status_color = '#fcb800'

        applications_list.append({
            'id': app.id,
            'application_number': app.application_number,
            'employee_id': app.employee_id,
            'submitter_name': app.submitter_name,
            'overtime_employee_name': app.overtime_employee_name,
            'application_date': app.application_date.strftime('%Y-%m-%d'),
            'start_time': app.start_time.strftime('%H:%M'),
            'end_time': app.end_time.strftime('%H:%M'),
            'duration': float(app.duration),
            'reason': app.reason,
            'line_leader_approval': app.line_leader_approval,
            'department_leader_approval': app.department_leader_approval,
            'approval_status': approval_status,
            'status_color': status_color,
            'line_leader_rejection_reason': app.line_leader_rejection_reason or '',
            'department_leader_rejection_reason': app.department_leader_rejection_reason or '',
        })
    # 根据审批状态排序
    applications_list.sort(key=lambda x: x['approval_status'])
    context['applications'] = applications_list

    # 返回页面
    return render(request, 'persons_overtime.html', context)

@login_required
def save_overtime_application(request):
    if request.method == 'POST':
        user = request.user
        # 获取表单中的数据
        application_number = request.POST.get('application_number')
        application_date_str = request.POST.get('application_date')
        start_time_str = request.POST.get('start_time')
        end_time_str = request.POST.get('end_time')
        duration_str = request.POST.get('duration')
        overtime_employee_name = request.POST.get('overtime_employee_name')
        reason = request.POST.get('reason')

        # 检查用户的权限
        if user.has_perm('persons.can_approve_line_leader'):
            # 条线领导审批
            line_leader_approval = request.POST.get('line_leader_approval')  # 'agree' or 'reject'
            line_leader_rejection_reason = request.POST.get('line_leader_rejection_reason')

            try:
                application = OvertimeApplication.objects.get(application_number=application_number)
                if line_leader_approval == 'agree':
                    application.line_leader_approval = True
                    application.line_leader_rejection_reason = ''
                elif line_leader_approval == 'reject':
                    application.line_leader_approval = False
                    application.line_leader_rejection_reason = line_leader_rejection_reason
                application.save()
                messages.success(request, '条线领导审批意见已提交！')
            except OvertimeApplication.DoesNotExist:
                messages.error(request, '申请不存在！')
            return redirect('persons:persons_overtime_apply')

        elif user.has_perm('persons.can_approve_department_leader'):
            # 部门领导审批
            department_leader_approval = request.POST.get('department_leader_approval')  # 'agree' or 'reject'
            department_leader_rejection_reason = request.POST.get('department_leader_rejection_reason')

            try:
                application = OvertimeApplication.objects.get(application_number=application_number)
                if application.line_leader_approval == True:
                    if department_leader_approval == 'agree':
                        application.department_leader_approval = True
                        application.department_leader_rejection_reason = ''
                    elif department_leader_approval == 'reject':
                        application.department_leader_approval = False
                        application.department_leader_rejection_reason = department_leader_rejection_reason
                    application.save()
                    messages.success(request, '部门领导审批意见已提交！')
                else:
                    messages.error(request, '条线领导未审批通过，无法进行部门领导审批！')
            except OvertimeApplication.DoesNotExist:
                messages.error(request, '申请不存在！')
            return redirect('persons:persons_overtime_apply')

        elif user.has_perm('persons.can_approve_general_management'):
            # 综合管理审批
            general_management_approval = request.POST.get('general_management_approval')
            general_management_rejection_reason = request.POST.get('general_management_rejection_reason')

            try:
                application = OvertimeApplication.objects.get(application_number=application_number)
                if application.department_leader_approval == True:
                    if general_management_approval == 'agree':
                        application.general_management_approval = True
                        application.general_management_rejection_reason = ''
                    elif general_management_approval == 'reject':
                        application.general_management_approval = False
                        application.general_management_rejection_reason = general_management_rejection_reason
                    application.save()
                    messages.success(request, '综合管理审批意见已提交！')
                else:
                    messages.error(request, '部门领导未审批通过，无法进行综合管理审批！')
            except OvertimeApplication.DoesNotExist:
                messages.error(request, '申请不存在！')
            return redirect('persons:persons_overtime_apply')

        else:
            # 普通运行人员提交申请
            # 检查是否有所有必要的表单字段
            if application_date_str and start_time_str and end_time_str and duration_str and overtime_employee_name and reason:
                # 解析日期和时间
                try:
                    application_date = datetime.strptime(application_date_str, '%Y-%m-%d').date()
                    start_time = datetime.strptime(start_time_str, '%H:%M').time()
                    end_time = datetime.strptime(end_time_str, '%H:%M').time()
                    duration = Decimal(duration_str)
                except ValueError:
                    messages.error(request, '日期或时间格式错误。')
                    return redirect('persons:persons_overtime_apply')

                # 检查是否已存在相同的记录
                existing_application = OvertimeApplication.objects.filter(
                    employee_id=user.username,
                    overtime_employee_name=overtime_employee_name,
                    reason=reason,
                    application_date=application_date
                ).first()

                if existing_application:
                    messages.error(request, '已存在相同的加班申请记录，无法重复提交。')
                    return redirect('persons:persons_overtime_apply')

                # 保存到数据库
                overtime_application = OvertimeApplication(
                    employee_id=user.username,
                    submitter_name=user.get_full_name(),
                    overtime_employee_name=overtime_employee_name,
                    application_date=application_date,
                    start_time=start_time,
                    end_time=end_time,
                    duration=duration,
                    reason=reason,
                    line_leader_approval=None,
                    department_leader_approval=None,
                )
                overtime_application.save()

                messages.success(request, '加班申请提交成功！')
                return redirect('persons:persons_overtime_apply')
            else:
                messages.error(request, '请填写所有必填字段。')
                return redirect('persons:persons_overtime_apply')
    else:
        return redirect('persons:persons_overtime_apply')

@login_required
def get_overtime_application_data(request):
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        application_id = request.POST.get('application_id')
        try:
            application = OvertimeApplication.objects.get(id=application_id)
            data = {
                'application_number': application.application_number,
                'employee_id': application.employee_id,
                'submitter_name': application.submitter_name,
                'overtime_employee_name': application.overtime_employee_name,
                'application_date': application.application_date.strftime('%Y-%m-%d'),
                'start_time': application.start_time.strftime('%H:%M'),
                'end_time': application.end_time.strftime('%H:%M'),
                'duration': str(application.duration),
                'reason': application.reason,
                'line_leader_approval': application.line_leader_approval,
                'department_leader_approval': application.department_leader_approval,
                'line_leader_rejection_reason': application.line_leader_rejection_reason or '',
                'department_leader_rejection_reason': application.department_leader_rejection_reason or '',
            }
            return JsonResponse({'status': 'success', 'data': data})
        except OvertimeApplication.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': '申请不存在'})
    else:
        return JsonResponse({'status': 'error', 'message': '无效的请求方法'})

@login_required
def delete_overtime_application(request):
    if request.method == 'POST':
        application_number = request.POST.get('application_number')
        if application_number:
            try:
                application = OvertimeApplication.objects.get(application_number=application_number)
                # 确保只有申请人本人或具有权限的用户可以删除
                if application.employee_id == request.user.username:
                    application.delete()
                    messages.success(request, '加班申请删除成功！')
                else:
                    messages.error(request, '您没有权限删除此申请。')
            except OvertimeApplication.DoesNotExist:
                messages.error(request, '加班申请不存在，无法删除。')
        else:
            messages.error(request, '未提供申请编号，无法删除。')
    return redirect('persons:persons_overtime_apply')


def persons_overtime_analysis(request):
    # 获取加班人员的唯一姓名列表
    persons = OvertimeApplication.objects.values_list('overtime_employee_name', flat=True).distinct()

    # 获取申请日期的唯一年份列表
    dates = OvertimeApplication.objects.dates('application_date', 'year')
    years = [date.year for date in dates]
    years.sort(reverse=True)  # 可选：按年份降序排序

    # 获取GET参数中的选定人员、年份、月份和申请编号
    selected_person = request.GET.get('person', 'All')
    selected_year = request.GET.get('year', None)
    selected_month = request.GET.get('month', None)
    application_number = request.GET.get('application_number', None)

    # 如果是 AJAX 请求，返回 JSON 数据
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # 过滤OvertimeApplication对象
        applications = OvertimeApplication.objects.all()
        if selected_person != 'All':
            applications = applications.filter(overtime_employee_name=selected_person)
        if selected_year:
            applications = applications.filter(application_date__year=selected_year)
        if selected_month:
            # selected_month 格式为 'YYYY-MM'
            year, month = selected_month.split('-')
            applications = applications.filter(application_date__year=year, application_date__month=month)
        if application_number:
            applications = applications.filter(application_number=application_number)

        # 构建树形数据结构
        tree_data = defaultdict(list)
        for app in applications:
            month = app.application_date.strftime('%Y-%m')
            tree_data[month].append(app.application_number)

        # 将tree_data转换为普通字典
        tree_data = dict(tree_data)

        # 准备表格数据
        applications_list = []
        for app in applications:
            applications_list.append({
                'application_number': app.application_number,
                'overtime_employee_name': app.overtime_employee_name,
                'employee_id': app.employee_id,  # 添加工号
                'reason': app.reason,
                'duration': app.duration,
                'line_leader_approval': app.line_leader_approval,
                'line_leader_rejection_reason': app.line_leader_rejection_reason,
                'department_leader_approval': app.department_leader_approval,
                'department_leader_rejection_reason': app.department_leader_rejection_reason,
            })

        # 准备汇总数据
        summary_data = []
        employee_dict = {}
        for app in applications:
            key = (app.employee_id, app.overtime_employee_name)
            if key not in employee_dict:
                employee_dict[key] = {
                    'total_duration': 0,
                    'approved_duration': 0,
                    'rejected_duration': 0,
                }
            employee_dict[key]['total_duration'] += app.duration
            # 修正通过时长的计算逻辑，只有部门领导批准才计入
            if app.department_leader_approval == True:
                employee_dict[key]['approved_duration'] += app.duration
            elif app.department_leader_approval == False:
                employee_dict[key]['rejected_duration'] += app.duration

        for (employee_id, name), durations in employee_dict.items():
            summary_data.append({
                'employee_id': employee_id,
                'name': name,
                'total_duration': durations['total_duration'],
                'approved_duration': durations['approved_duration'],
                'rejected_duration': durations['rejected_duration'],
            })

        return JsonResponse({'tree_data': tree_data, 'applications': applications_list, 'summary': summary_data})

    # 非 AJAX 请求，渲染模板
    context = {
        'page_title': '加班汇总',
        'persons': persons,
        'years': years,
        'selected_person': selected_person,
        'selected_year': selected_year,
    }
    return render(request, 'persons_overtime_analysis.html', context)

@login_required
@require_POST
def update_skill(request):
    try:
        data = json.loads(request.body)
        person_id = data.get('person_id')
        skill_data = data.get('skill_data')

        person = get_object_or_404(Person, id=person_id)
        skill, created = Skill.objects.update_or_create(
            person=person,
            defaults={
                'skill1': skill_data.get('skill1'),
                'skill2': skill_data.get('skill2'),
                'skill3': skill_data.get('skill3'),
                'skill4': skill_data.get('skill4'),
                'skill5': skill_data.get('skill5'),
            }
        )
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@login_required
@require_POST
def update_performance(request):
    try:
        data = json.loads(request.body)
        person_id = data.get('person_id')
        performance_data = data.get('performance_data')
        set_name = performance_data.get('set_name')

        person = get_object_or_404(Person, id=person_id)
        performance, created = Performance.objects.update_or_create(
            person=person,
            set_name=set_name,
            defaults={
                'performance1': performance_data.get('performance1'),
                'performance2': performance_data.get('performance2'),
                'performance3': performance_data.get('performance3'),
                'performance4': performance_data.get('performance4'),
                'performance5': performance_data.get('performance5'),
                'performance6': performance_data.get('performance6'),
            }
        )
        return JsonResponse({
            'status': 'success',
            'performance_data': {'set_name': set_name}
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)