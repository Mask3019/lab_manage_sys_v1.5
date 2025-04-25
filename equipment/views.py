import uuid
import json
import logging
from datetime import datetime, timedelta

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Permission, User
from django.contrib.contenttypes.models import ContentType
from django.contrib import messages
from django.db.models import Max, Q
from django.db.models.functions import ExtractYear
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.views.generic import TemplateView
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction

from .models import Equipment, MaintenanceRecord, EquipmentRepairApplication, Supplier  # 添加 Supplier
from .forms import MaintenanceRecordForm

logger = logging.getLogger(__name__)


class EquipmentInformationView(TemplateView):
    template_name = 'equipment_info.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': "设备信息",
            'equipment_list': Equipment.objects.all(),
            'user_has_permission': self.request.user.has_perm('equipment.change_equipment'),
        })
        return context


@csrf_exempt
def save_equipment(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            equipment_id = data.get('equipment_id')

            if not equipment_id:
                return JsonResponse({
                    "status": "error",
                    "message": "设备编号不能为空"
                }, status=400)

            # 使用update_or_create而不是create
            equipment, created = Equipment.objects.update_or_create(
                equipment_id=equipment_id,  # 查找条件
                defaults={                  # 更新或创建的字段
                    'name': data.get('name'),
                    'type': data.get('type'),
                    'usage_frequency': data.get('usage_frequency'),
                    'responsible_person': data.get('responsible_person'),
                    'waiting_cost': float(data.get('waiting_cost', 0)),
                    'debugging_cost': float(data.get('debugging_cost', 0)),
                    'operating_cost': float(data.get('operating_cost', 0)),
                    'remark': data.get('remark')
                }
            )

            return JsonResponse({
                "status": "success",
                "message": "设备信息保存成功",
                "created": created
            })

        except Equipment.MultipleObjectsReturned:
            # 处理可能存在的重复记录
            logger.error(f"Multiple records found for equipment_id: {equipment_id}")
            return JsonResponse({
                "status": "error",
                "message": "数据库中存在重复记录，请联系管理员"
            }, status=500)
            
        except Exception as e:
            logger.exception("保存设备信息出错")
            return JsonResponse({
                "status": "error",
                "message": f"保存失败: {str(e)}"
            }, status=500)

    return JsonResponse({
        "status": "error",
        "message": "无效的请求"
    }, status=400)


@csrf_exempt
def delete_equipment(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            equipment_id = data.get('equipment_id')

            if not equipment_id:
                return JsonResponse({
                    "status": "error",
                    "message": "设备编号不能为空"
                }, status=400)

            try:
                with transaction.atomic():
                    equipment = Equipment.objects.get(equipment_id=equipment_id)
                    # 删除设备会触发 Equipment 模型中的 delete 方法
                    equipment.delete()
                    return JsonResponse({
                        "status": "success",
                        "message": "删除成功"
                    })
            except Equipment.DoesNotExist:
                return JsonResponse({
                    "status": "error",
                    "message": "设备不存在"
                }, status=404)
            except Exception as e:
                logger.exception("删除设备时出错")
                return JsonResponse({
                    "status": "error",
                    "message": f"删除失败: {str(e)}"
                }, status=500)

        except json.JSONDecodeError:
            return JsonResponse({
                "status": "error",
                "message": "无效的JSON数据"
            }, status=400)

    return JsonResponse({
        "status": "error",
        "message": "无效的请求方法"
    }, status=400)


def equipment_status(request):
    # 获取筛选参数
    equipment_status_filter = request.GET.get('equipment_status', '')
    region_filter = request.GET.get('region', '')

    # 获取所有设备
    equipment_list = Equipment.objects.all()

    # 根据设备状态筛选
    if equipment_status_filter:
        equipment_list = equipment_list.filter(equipment_status=equipment_status_filter)

    # 根据区域筛选
    if region_filter:
        if region_filter in ['A区', 'B区', 'C区', 'D区']:
            region_letter = region_filter[0]
            equipment_list = equipment_list.filter(equipment_id__icontains=region_letter)
        elif region_filter == '其他':
            equipment_list = equipment_list.exclude(
                Q(equipment_id__icontains='A') |
                Q(equipment_id__icontains='B') |
                Q(equipment_id__icontains='C') |
                Q(equipment_id__icontains='D')
            )

    # 区域名称列表
    region_names = ['A区', 'B区', 'C区', 'D区', '其他']
    region_devices = {region: [] for region in region_names}

    # 将设备按照区域分类
    for device in equipment_list:
        equipment_id = device.equipment_id.upper()
        for region in region_names[:-1]:
            if region[0] in equipment_id:
                region_devices[region].append(device)
                break
        else:
            region_devices['其他'].append(device)

    context = {
        'equipment_list': equipment_list,
        'region_device_items': [(name, region_devices[name]) for name in region_names],
        'page_title': '设备状态',
        'request': request,
    }

    return render(request, 'equipment_status.html', context)


def equipment_maintenance(request):
    equipments = Equipment.objects.all()
    records = MaintenanceRecord.objects.select_related('equipment').all().order_by('equipment__equipment_id')

    # 获取年份筛选参数，如果为空则不进行年份过滤
    try:
        year_filter = request.GET.get('year_filter', '')
        selected_year = int(year_filter) if year_filter.strip() else timezone.now().year
    except (ValueError, TypeError):
        selected_year = timezone.now().year
    
    selected_equipment_id = request.GET.get('equipment_id_filter', '')

    # 过滤记录
    if selected_year:
        records = records.filter(maintenance_date__year=selected_year)
    if selected_equipment_id:
        records = records.filter(equipment__equipment_id=selected_equipment_id)

    today = timezone.now().date()

    # 获取所有设备及其最新保养记录
    equipments_with_maintenance = Equipment.objects.all()
    pending_equipments = []

    for equipment in equipments_with_maintenance:
        # 获取设备的最新保养记录
        latest_record = MaintenanceRecord.objects.filter(
            equipment=equipment
        ).order_by('-maintenance_date').first()

        # 根据设备重要程度设置提前提醒天数
        advance_notice_days = {
            'high': 30,    # 高重要度设备提前30天提醒
            'medium': 15,  # 中等重要度设备提前15天提醒
            'low': 7       # 低重要度设备提前7天提醒
        }.get(equipment.importance, 15)  # 默认提前15天

        # 获取下次保养日期
        if latest_record and latest_record.next_maintenance_date:
            # 优先使用保养记录中设置的下次保养日期
            next_maintenance_date = latest_record.next_maintenance_date
            equipment.next_maintenance_date = next_maintenance_date
        elif equipment.last_maintenance_date:
            # 如果没有保养记录或没有设置下次保养日期，使用设备的最后保养日期计算
            next_maintenance_date = equipment.last_maintenance_date + timedelta(days=equipment.maintenance_cycle)
            equipment.next_maintenance_date = next_maintenance_date
        else:
            # 如果没有任何保养记录和最后保养日期，将其添加到待保养列表
            pending_equipments.append(equipment)
            continue

        # 检查是否需要保养
        days_until_maintenance = (next_maintenance_date - today).days
        if days_until_maintenance <= advance_notice_days:
            pending_equipments.append(equipment)

    # 获取所有设备编号用于筛选下拉框
    equipment_ids = equipments.values_list('equipment_id', flat=True).distinct()

    # 获取所有保养年份列表用于年份筛选，包括全部选项
    maintenance_years = MaintenanceRecord.objects.dates('maintenance_date', 'year', order='DESC')
    year_list = [year.year for year in maintenance_years]
    
    context = {
        'page_title': '设备保养',
        'equipments': equipments,
        'records': records,
        'pending_equipments': pending_equipments,
        'equipment_ids': equipment_ids,
        'maintenance_years': year_list,
        'selected_year': selected_year,
        'selected_equipment_id': selected_equipment_id,
    }
    return render(request, 'equipment_maintenance.html', context)


def add_maintenance_record(request):
    equipment_id = request.GET.get('equipment_id')
    today = timezone.now().date()
    next_year = today + timedelta(days=365)

    if request.method == 'POST':
        form = MaintenanceRecordForm(request.POST)
        if form.is_valid():
            maintenance_record = form.save(commit=False)
            equipment = maintenance_record.equipment
            maintenance_record.maintenance_date = maintenance_record.maintenance_date or today
            maintenance_record.next_maintenance_date = maintenance_record.next_maintenance_date or next_year
            maintenance_record.save()
            equipment.last_maintenance_date = maintenance_record.maintenance_date
            equipment.save()
            return redirect('equipment:equipment_maintenance')
    else:
        initial_data = {
            'maintenance_date': today,
            'next_maintenance_date': next_year
        }
        if equipment_id:
            initial_data['equipment'] = get_object_or_404(Equipment, equipment_id=equipment_id)

        form = MaintenanceRecordForm(initial=initial_data)

    context = {
        'page_title': '添加保养记录',
        'form': form,
    }
    return render(request, 'add_maintenance_record.html', context)


@login_required
def equipment_repair(request):
    user = request.user
    application_date = timezone.now().date()
    context = {
        'page_title': '设备维修',
        'application_date': application_date.strftime('%Y-%m-%d'),
        'end_time': application_date.strftime('%Y-%m-%d'),
        'employee_id': user.username,
        'submitter_name': user.get_full_name(),
        'application_number': '',
    }

    years = EquipmentRepairApplication.objects.dates('application_date', 'year').distinct().order_by('-application_date')
    unique_years = sorted({year.year for year in years}, reverse=True)
    context['years'] = unique_years

    user_permissions = list(user.get_all_permissions())
    context['user_permissions'] = user_permissions

    if any(user.has_perm(perm) for perm in [
        'equipment.can_approve_line_leader',
        'equipment.can_approve_department_leader',
        'equipment.can_approve_area_leader',
        'equipment.can_approve_device_manager',
        'equipment.can_approve_device_repairer',
    ]):
        applications = EquipmentRepairApplication.objects.all()
    else:
        applications = EquipmentRepairApplication.objects.filter(employee_id=user.username)

    applications_list = []
    for app in applications:
        approval_status, status_color = get_approval_status(app)
        applications_list.append({
            'id': app.id,
            'application_number': app.application_number,
            'employee_id': app.employee_id,
            'submitter_name': app.submitter_name,
            'application_date': app.application_date.strftime('%Y-%m-%d'),
            'end_time': app.end_time.strftime('%Y-%m-%d') if app.end_time else '',
            'device_name': app.device_name,
            'fault_phenomenon': app.fault_phenomenon,
            'fault_locations': app.fault_locations,
            'fault_level': app.fault_level,
            'fault_reason': app.fault_reason,
            'solution': app.solution,
            'line_leader_approval': app.line_leader_approval,
            'department_leader_approval': app.department_leader_approval,
            'area_leader_approval': app.area_leader_approval,
            'device_manager_approval': app.device_manager_approval,
            'device_repairer_approval': app.device_repairer_approval,
            'approval_status': approval_status,
            'status_color': status_color,
            'line_leader_rejection_reason': app.line_leader_rejection_reason or '',
            'department_leader_rejection_reason': app.department_leader_rejection_reason or '',
            'area_leader_rejection_reason': app.area_leader_rejection_reason or '',
            'device_manager_rejection_reason': app.device_manager_rejection_reason or '',
            'device_repairer_rejection_reason': app.device_repairer_rejection_reason or '',
        })

    applications_list.sort(key=lambda x: x['application_date'], reverse=True)
    context['applications'] = applications_list
    context['equipments'] = Equipment.objects.all()

    application_number = request.POST.get('application_number') or request.GET.get('application_number')
    if application_number:
        application = EquipmentRepairApplication.objects.filter(application_number=application_number).first()
    else:
        application = None

    # 添加这段新的权限和状态控制代码
    approval_permissions = {
        'show_area_leader_approval': user.has_perm('equipment.can_approve_area_leader'),
        'show_device_repairer_approval': user.has_perm('equipment.can_approve_device_repairer'),
        'show_line_leader_approval': user.has_perm('equipment.can_approve_line_leader'),
        'show_department_leader_approval': user.has_perm('equipment.can_approve_department_leader'),
        'show_device_manager_approval': user.has_perm('equipment.can_approve_device_manager'),
    }
    
    if application:
        # 根据审批流程状态调整显示权限
        approval_permissions['show_device_repairer_approval'] = (
            approval_permissions['show_device_repairer_approval'] 
            and application.area_leader_approval is True
        )
        approval_permissions['show_line_leader_approval'] = (
            approval_permissions['show_line_leader_approval'] 
            and application.device_repairer_approval is True
        )
        approval_permissions['show_department_leader_approval'] = (
            approval_permissions['show_department_leader_approval'] 
            and application.line_leader_approval is True
        )
        approval_permissions['show_device_manager_approval'] = (
            approval_permissions['show_device_manager_approval'] 
            and application.department_leader_approval is True
        )

    # 更新 context
    context.update(approval_permissions)
    context['application'] = application
    context['related_persons'] = get_related_persons(application)

    user_permissions = []
    permission_mapping = {
        'equipment.can_approve_area_leader': 'can_approve_area_leader',
        'equipment.can_approve_device_repairer': 'can_approve_device_repairer',
        'equipment.can_approve_line_leader': 'can_approve_line_leader',
        'equipment.can_approve_department_leader': 'can_approve_department_leader',
        'equipment.can_approve_device_manager': 'can_approve_device_manager',
    }
    
    # 检查用户权限
    for perm, perm_code in permission_mapping.items():
        if request.user.has_perm(perm):
            user_permissions.append(perm)
    
    context['user_permissions'] = user_permissions

    return render(request, 'equipment_repair.html', context)


def get_approval_status(app):
    # 如果有被驳回并指定了接收人，按照新的逻辑处理
    if app.rejected_to:
        return '待区域主管审批', 'orange'  # 所有被驳回的申请都显示为待区域主管审批
        
    # 正常审批流程的状态判断
    if app.area_leader_approval is None:
        return '待区域主管审批', 'orange'
    elif app.area_leader_approval is False:
        return '区域主管已驳回', 'red'
    elif app.line_leader_approval is None:
        return '待条线领导审批', 'orange'
    elif app.line_leader_approval is False:
        return '条线领导已驳回', 'red'
    elif app.device_manager_approval is False:
        return '设备管理员已驳回', 'red'
    elif all([
        app.area_leader_approval is True,
        app.line_leader_approval is True,
        app.device_manager_approval is True,
    ]):
        return '审核通过', 'green'
    else:
        return '待审核', 'orange'


def get_related_persons(application):
    related_persons = []
    if application:
        related_persons.append({'name': application.submitter_name, 'employee_id': application.employee_id})

    approver_permissions = [
        # 'can_approve_area_leader',
        'can_approve_device_repairer',
        # 'can_approve_line_leader',
        # 'can_approve_department_leader',
        # 'can_approve_device_manager',
    ]
    for perm_codename in approver_permissions:
        users = get_users_with_permission(perm_codename)
        for user in users:
            person = {'name': user.get_full_name(), 'employee_id': user.username}
            if person not in related_persons:
                related_persons.append(person)
    return related_persons


def get_users_with_permission(permission_codename):
    content_type = ContentType.objects.get_for_model(EquipmentRepairApplication)
    permission = Permission.objects.get(codename=permission_codename, content_type=content_type)
    return User.objects.filter(Q(user_permissions=permission) | Q(groups__permissions=permission)).distinct()


@login_required
def save_device_repair_application(request):
    if request.method == 'POST':
        user = request.user
        # 获取表单中的数据
        application_number = request.POST.get('application_number')
        application_date_str = request.POST.get('application_date')
        device_name = request.POST.get('device_name')
        fault_phenomenon = request.POST.get('fault_phenomenon')
        submitter_name = request.POST.get('submitter_name')

        if application_number:
            try:
                application = EquipmentRepairApplication.objects.get(application_number=application_number)
                
                # 添加设备维修员的特殊权限判断
                if user.has_perm('equipment.can_approve_device_repairer'):
                    # 设备维修员可以修改所有字段
                    application.application_date = datetime.strptime(application_date_str, '%Y-%m-%d').date()
                    application.device_name = device_name
                    application.fault_phenomenon = fault_phenomenon
                    application.fault_level = request.POST.get('fault_level')
                    application.fault_locations = request.POST.get('fault_locations')
                    application.fault_reason = request.POST.get('fault_reason')
                    application.solution = request.POST.get('solution')
                    application.end_time = request.POST.get('end_time')
                    application.duration = request.POST.get('duration')
                    application.save()
                    messages.success(request, '维修信息更新成功！')
                    return redirect('equipment:equipment_repair')

                # 其他角色的原有处理逻辑
                elif user.has_perm('equipment.can_approve_area_leader'):
                    # 区域领导审批
                    area_leader_approval = request.POST.get('area_leader_approval')  # 'agree' or 'reject'
                    area_leader_rejection_reason = request.POST.get('area_leader_rejection_reason')
                    area_leader_rejected_to = request.POST.get('area_leader_rejected_to')

                    if area_leader_approval == 'agree':
                        application.area_leader_approval = True
                        application.area_leader_rejection_reason = ''
                        application.rejected_to = None
                    elif area_leader_approval == 'reject':
                        application.area_leader_approval = False
                        application.area_leader_rejection_reason = area_leader_rejection_reason
                        application.rejected_to = area_leader_rejected_to
                        # 重置所有后续审批状态
                        application.line_leader_approval = None
                        application.device_manager_approval = None

                    # 保存区域领导可编辑的字段
                    application.application_date = datetime.strptime(application_date_str, '%Y-%m-%d').date()
                    application.device_name = device_name
                    application.fault_phenomenon = fault_phenomenon

                    application.save()
                    messages.success(request, '区域主管审批意见已提交！')
                    return redirect('equipment:equipment_repair')

                elif user.has_perm('equipment.can_approve_line_leader') and application.area_leader_approval == True:
                    # 条线领导审批
                    line_leader_approval = request.POST.get('line_leader_approval')  # 'agree' or 'reject'
                    line_leader_rejection_reason = request.POST.get('line_leader_rejection_reason')
                    line_leader_rejected_to = request.POST.get('line_leader_rejected_to')

                    if line_leader_approval == 'agree':
                        application.line_leader_approval = True
                        application.line_leader_rejection_reason = ''
                        application.rejected_to = None
                    elif line_leader_approval == 'reject':
                        application.line_leader_approval = False
                        application.line_leader_rejection_reason = line_leader_rejection_reason
                        application.rejected_to = line_leader_rejected_to
                        # 重置驳回接收人之后的所有审批状态
                        # 根据驳回接收人的角色重置不同的审批状态
                        users_with_perm = get_users_with_permission('can_approve_area_leader')
                        if any(user.username == rejected_to for user in users_with_perm):
                            application.area_leader_approval = None
                            application.line_leader_approval = None
                            application.device_manager_approval = None

                    application.save()
                    messages.success(request, '条线领导审批意见已提交！')
                    return redirect('equipment:equipment_repair')

                elif user.has_perm('equipment.can_approve_device_manager') and application.line_leader_approval == True:
                    # 设备管理员审批
                    device_manager_approval = request.POST.get('device_manager_approval')  # 'agree' or 'reject'
                    device_manager_rejection_reason = request.POST.get('device_manager_rejection_reason')
                    device_manager_rejected_to = request.POST.get('device_manager_rejected_to')

                    if device_manager_approval == 'agree':
                        application.device_manager_approval = True
                        application.device_manager_rejection_reason = ''
                        application.rejected_to = None
                    elif device_manager_approval == 'reject':
                        application.device_manager_approval = False
                        application.device_manager_rejection_reason = device_manager_rejection_reason
                        rejected_to = device_manager_rejected_to
                        application.rejected_to = rejected_to
                        # 根据驳回接收人的角色重置不同的审批状态
                        users_with_area_leader_perm = get_users_with_permission('can_approve_area_leader')
                        users_with_line_leader_perm = get_users_with_permission('can_approve_line_leader')
                        
                        if any(user.username == rejected_to for user in users_with_area_leader_perm):
                            # 驳回给区域主管，重置所有状态
                            application.area_leader_approval = None
                            application.line_leader_approval = None
                            application.device_manager_approval = None
                        elif any(user.username == rejected_to for user in users_with_line_leader_perm):
                            # 驳回给条线领导，重置条线领导及之后的状态
                            application.line_leader_approval = None
                            application.device_manager_approval = None

                    application.save()
                    messages.success(request, '设备管理员审批意见已提交！')
                    return redirect('equipment:equipment_repair')

                else:
                    # 申请人或被驳回对象重新提交
                    if application.employee_id == user.username or application.rejected_to == user.username:
                        # 清空 rejected_to 字段
                        application.rejected_to = None
                        # 更新申请数据
                        try:
                            application.application_date = datetime.strptime(application_date_str, '%Y-%m-%d').date()
                        except ValueError:
                            messages.error(request, '日期格式错误。')
                            return redirect('equipment:equipment_repair')
                        application.device_name = device_name
                        application.fault_phenomenon = fault_phenomenon
                        # 重置被驳回的审批状态
                        if application.area_leader_approval is False:
                            application.area_leader_approval = None
                        elif application.line_leader_approval is False:
                            application.line_leader_approval = None
                        elif application.device_manager_approval is False:
                            application.device_manager_approval = None
                        application.save()
                        messages.success(request, '已重新提交被驳回的申请！')
                        return redirect('equipment:equipment_repair')
                    else:
                        messages.error(request, '您没有权限更新此申请。')
                        return redirect('equipment:equipment_repair')

            except EquipmentRepairApplication.DoesNotExist:
                messages.error(request, '申请不存在，无法更新。')
                return redirect('equipment:equipment_repair')

        # 未提供申请编号，视为新建申请
        else:
            if application_date_str and device_name and fault_phenomenon:
                try:
                    application_date = datetime.strptime(application_date_str, '%Y-%m-%d').date()

                    # 检查是否已存在相同的记录
                    existing_application = EquipmentRepairApplication.objects.filter(
                        employee_id=user.username,
                        submitter_name=submitter_name,
                        fault_phenomenon=fault_phenomenon,
                        application_date=application_date
                    ).first()

                    if existing_application:
                        messages.error(request, '已存在相同的申请记录，无法重复提交。')
                        return redirect('equipment:equipment_repair')

                    # 保存到数据库
                    equipment_repair_application = EquipmentRepairApplication(
                        employee_id=user.username,
                        submitter_name=user.get_full_name(),
                        application_date=application_date,
                        device_name=device_name,
                        fault_phenomenon=fault_phenomenon,
                        area_leader_approval=None,
                        line_leader_approval=None,
                        device_manager_approval=None,
                        rejected_to=None,
                    )
                    equipment_repair_application.save()

                    messages.success(request, '设备维修申请提交成功！')
                    return redirect('equipment:equipment_repair')

                except ValueError:
                    messages.error(request, '日期格式错误。')
                    return redirect('equipment:equipment_repair')
            else:
                messages.error(request, '请填写所有必填字段。')
                return redirect('equipment:equipment_repair')
    
    return redirect('equipment:equipment_repair')


@login_required
def get_device_repair_application_data(request):
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        application_id = request.POST.get('application_id')
        try:
            application = EquipmentRepairApplication.objects.get(id=application_id)
            # 添加审批状态
            status_text, status_color = get_approval_status(application)
            
            data = {
                'application_number': application.application_number,
                'employee_id': application.employee_id,
                'submitter_name': application.submitter_name,
                'application_date': application.application_date.strftime('%Y-%m-%d'),
                'end_time': application.end_time.strftime('%Y-%m-%d') if application.end_time else timezone.now().date(),
                'duration': application.duration,
                'device_name': application.device_name,
                'fault_phenomenon': application.fault_phenomenon,
                'fault_locations': application.fault_locations,
                'fault_level': application.fault_level,
                'fault_reason': application.fault_reason,
                'solution': application.solution,
                'line_leader_approval': application.line_leader_approval,
                'area_leader_approval': application.area_leader_approval,
                'device_manager_approval': application.device_manager_approval,
                'line_leader_rejection_reason': application.line_leader_rejection_reason or '',
                'area_leader_rejection_reason': application.area_leader_rejection_reason or '',
                'device_manager_rejection_reason': application.device_manager_rejection_reason or '',
                'approval_status': status_text,  # 添加审批状态文本
                'status_color': status_color     # 添加审批状态颜色
            }
            return JsonResponse({'status': 'success', 'data': data})
        except EquipmentRepairApplication.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': '申请不存在'})
    else:
        return JsonResponse({'status': 'error', 'message': '无效的请求方法'})


@login_required
def delete_device_repair_application(request):
    if request.method == 'POST':
        application_number = request.POST.get('application_number')
        if application_number:
            try:
                application = EquipmentRepairApplication.objects.get(application_number=application_number)
                if application.employee_id == request.user.username:
                    application.delete()
                    messages.success(request, '维修申请删除成功！')
                else:
                    messages.error(request, '您没有权限删除此申请。')
            except EquipmentRepairApplication.DoesNotExist:
                messages.error(request, '维修申请不存在，无法删除。')
        else:
            messages.error(request, '未提供申请编号，无法删除。')
    return redirect('equipment:equipment_repair')

#===================================================
def reject_application(request):
    if request.method == 'POST':
        application_id = request.POST.get('application_id')
        application = get_object_or_404(EquipmentRepairApplication, pk=application_id)

        # 获取驳回角色并设置驳回状态
        role = request.POST.get('role')
        setattr(application, f'{role}_approval', False)
        setattr(application, f'{role}_rejection_reason', request.POST.get('rejection_reason'))

        # 将后续的审批状态设置为待审批
        role_order = ['area_leader', 'device_repairer', 'line_leader', 'department_leader', 'device_manager']
        role_index = role_order.index(role)
        for next_role in role_order[role_index + 1:]:
            setattr(application, f'{next_role}_approval', None)  # 设置为待审批状态

        application.save()
        return JsonResponse({'status': 'success'})


def equipment_medical_card(request):
    """设备病历视图函数"""
    # 获取所有维修申请记录，但先不排序
    repair_records = EquipmentRepairApplication.objects.all()

    # 处理设备编号：获取第二个"-"之前的字符串作为设备编号
    for record in repair_records:
        parts = record.device_name.split('-')
        if len(parts) >= 2:
            record.equipment_id = '-'.join(parts[:2])
        else:
            record.equipment_id = record.device_name

    # 根据筛选条件过滤数据
    selected_device = request.GET.get('device_name', '')
    selected_fault_level = request.GET.get('fault_level', '')
    selected_fault_location = request.GET.get('fault_location', '')
    selected_year = request.GET.get('year', '')
    selected_month = request.GET.get('month', '')
    
    # 将QuerySet转换为list以进行自定义排序
    repair_records = list(repair_records)
    
    # 多重排序：先按设备编号升序，再按故障日期升序
    repair_records.sort(key=lambda x: (x.equipment_id, x.application_date))
    
    # 应用其他筛选条件
    if selected_device:
        repair_records = [r for r in repair_records if r.equipment_id == selected_device]
    if selected_fault_level:
        repair_records = [r for r in repair_records if r.fault_level == selected_fault_level]
    if selected_fault_location:
        repair_records = [r for r in repair_records if r.fault_locations == selected_fault_location]
    if selected_year:
        repair_records = [r for r in repair_records if str(r.application_date.year) == selected_year]
    if selected_month:
        repair_records = [r for r in repair_records if str(r.application_date.month) == selected_month]

    # 获取筛选选项的唯一值
    device_ids = sorted(set(record.equipment_id for record in repair_records))
    fault_levels = sorted(set(record.fault_level for record in repair_records if record.fault_level))
    fault_locations = sorted(set(record.fault_locations for record in repair_records if record.fault_locations))
    years = sorted(set(record.application_date.year for record in repair_records), reverse=True)
    months = list(range(1, 13))

    context = {
        'page_title': '设备病历',
        'repair_records': repair_records,
        'device_names': device_ids,
        'fault_levels': fault_levels,
        'fault_locations': fault_locations,
        'years': years,
        'months': months,
        'selected_device': selected_device,
        'selected_fault_level': selected_fault_level,
        'selected_fault_location': selected_fault_location,
        'selected_year': selected_year,
        'selected_month': selected_month,
    }

    # 如果是AJAX请求，只返回表格部分的HTML
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, 'equipment_medical_card.html', context)
    
    return render(request, 'equipment_medical_card.html', context)


def equipment_analysis(request):
    """统计分析视图函数"""
    return render(request, 'equipment_analysis.html')


@login_required
def supplier_management(request):
    """供应商管理视图函数"""
    user = request.user
    can_manage = user.has_perm('equipment.can_approve_device_manager') or \
                 user.has_perm('equipment.can_approve_device_repairer')
    
    if request.method == 'POST' and can_manage:
        action = request.POST.get('action')
        
        if action == 'add':
            Supplier.objects.create(
                name=request.POST.get('name'),
                contact_person=request.POST.get('contact_person'),  # 添加联系人
                contact_phone=request.POST.get('contact_phone'),    # 添加联系电话
                address=request.POST.get('address'),
                repair_scope=request.POST.get('repair_scope'),
                repair_equipment=request.POST.get('repair_equipment')
            )
            messages.success(request, '供应商添加成功')
        
        elif action == 'update':
            supplier_id = request.POST.get('supplier_id')
            supplier = get_object_or_404(Supplier, id=supplier_id)
            supplier.name = request.POST.get('name')
            supplier.contact_person = request.POST.get('contact_person')  # 添加联系人
            supplier.contact_phone = request.POST.get('contact_phone')    # 添加联系电话
            supplier.address = request.POST.get('address')
            supplier.repair_scope = request.POST.get('repair_scope')
            supplier.repair_equipment = request.POST.get('repair_equipment')
            supplier.save()
            messages.success(request, '供应商信息更新成功')
        
        elif action == 'delete':
            supplier_id = request.POST.get('supplier_id')
            Supplier.objects.filter(id=supplier_id).delete()
            messages.success(request, '供应商删除成功')
        
        return redirect('equipment:supplier_management')

    suppliers = Supplier.objects.all()
    context = {
        'page_title': '供应商管理',
        'suppliers': suppliers,
        'can_manage': can_manage,
    }
    return render(request, 'supplier_management.html', context)