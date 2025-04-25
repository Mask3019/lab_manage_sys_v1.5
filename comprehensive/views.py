from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from .models import *
from django.http import JsonResponse
import json
from django.utils.dateparse import parse_date
import logging
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import os

# Create your views here.
def report_register(request):
    context = {
        'page_title': '报告出具登记',
    }
    return render(request, 'report_register.html', context)

def report_delay(request):
    context = {
        'page_title': '拖延报告汇总',
    }
    return render(request, 'report_delay.html', context)

def report_analysis(request):
    context = {
        'page_title': '报告汇总分析',
    }
    return render(request, 'report_analysis.html', context)

# 设置大纲登记的视图函数
logger = logging.getLogger(__name__)
@login_required
def filter_projects(request):
    if request.method == 'GET':
        outline_status = request.GET.get('outline_status')
        sample_style = request.GET.get('sample_style')
        project = request.GET.get('project')  # 新增这行

        # 构建查询条件
        filters = {}
        if outline_status:
            filters['outline_status'] = outline_status
        if sample_style:
            filters['sample_style'] = sample_style
        if project:  # 新增这个条件
            filters['project'] = project

        # 根据筛选条件查询大纲
        outlines = Outlines.objects.filter(**filters).order_by('id')

        # 提取项目代号下拉框内容
        filtered_projects = Outlines.objects.values_list('project', flat=True).distinct()
        if sample_style:
            filtered_projects = filtered_projects.filter(sample_style=sample_style)
        if outline_status:
            filtered_projects = filtered_projects.filter(outline_status=outline_status)

        # 构建响应数据
        data = {
            'projects': list(filtered_projects),  # 返回匹配的项目代号列表
            'outlines': list(outlines.values(
                'id', 'sample_style', 'project', 'outline_num', 'outline_name', 'editor', 'save_date', 'outline_status', 'remark'
            ))
        }

        return JsonResponse(data)


@login_required
def outline_register(request):
    try:
        if not request.user.has_perm('comprehensive.view_outlines'):
            raise PermissionDenied
        outlines = Outlines.objects.order_by('outline_num')  # 获取所有大纲
        user_has_permission = request.user.has_perm('comprehensive.change_outlines')

        # 获取所有不重复的项目代号，无论用户权限如何都传递
        projects = Outlines.objects.values_list('project', flat=True).distinct()

        context = {
            'page_title': '试验大纲登记',
            'outlines': outlines,
            'user_has_permission': user_has_permission,
            'projects': projects,  # 始终传递项目代号到模板
        }
        return render(request, 'outline_register.html', context)
    except PermissionDenied:
        context = {
            'error_message': '您没有权限查看此页面',
        }
        return render(request, 'outline_register.html', context)

#上传文件
@csrf_exempt
def upload_outline_file(request):
    if request.method == 'POST' and request.FILES.get('file'):
        file = request.FILES['file']
        outline_num = request.POST.get('outline_num')

        # 获取文件名的第一个部分（以“-”分隔）
        project_code = outline_num.split('-')[0]

        # 文件保存路径，使用 project_code 来构建路径
        save_path = os.path.join(settings.MEDIA_ROOT, 'files', project_code)

        # 确保目录存在，如果不存在则创建
        os.makedirs(save_path, exist_ok=True)

        # 构建完整的文件保存路径
        file_path = os.path.join(save_path, file.name)

        # 保存文件
        with open(file_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)

        # 返回上传成功的响应
        return JsonResponse({'success': True})

    # 如果不是 POST 请求或文件缺失，则返回上传失败的响应
    return JsonResponse({'success': False, 'error': '上传失败'})
# 保存大纲
@login_required
@permission_required('comprehensive.change_outlines', raise_exception=True)
def save_outline(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            sample_style = data.get('sample_style')
            project = data.get('project')
            outline_num = data.get('outline_num')
            outline_name = data.get('outline_name')
            editor = data.get('editor')
            save_date = data.get('save_date')
            outline_status = data.get('outline_status')
            remark = data.get('remark')
            # 解析并检查归档日期
            save_date = parse_date(save_date)
            if not save_date:
                return JsonResponse({'status': 'error', 'message': '归档日期格式必须为 "YYYY-MM-DD"'}, status=400)

            outlines, created = Outlines.objects.update_or_create(
                outline_num=outline_num,
                defaults={
                    'sample_style': sample_style,
                    'project': project,
                    'outline_name': outline_name,
                    'editor': editor,
                    'save_date': save_date,
                    'outline_status': outline_status,
                    'remark': remark,
                }
            )
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)


@login_required
@permission_required('comprehensive.delete_outlines', raise_exception=True)
def delete_outline(request):
    if request.method == 'POST':
        outline_num = request.POST.get('outline_num')  # 从 POST 数据中获取 outline_num
        try:
            outline = Outlines.objects.get(outline_num=outline_num)
            outline.delete()
            return JsonResponse({'status': 'success'})
        except Outlines.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Outline not found'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def client_edit(request):
    try:
        if not request.user.has_perm('comprehensive.view_department'):
            raise PermissionDenied
        items = Department.objects.order_by('name')  # 获取部门名称
        user_has_permission = request.user.has_perm('comprehensive.change_department')
        print(items)
        context = {
            'page_title': '委托方编辑',
            'items': items,
            'user_has_permission': user_has_permission,
        }
        return render(request, 'client_edit.html', context)
    except PermissionDenied:
        context = {
            'error_message': '您没有权限查看此页面',
        }
        return render(request, 'client_edit.html', context)

@login_required
@permission_required('comprehensive.delete_department', raise_exception=True)
def delete_client(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        try:
            client = Department.objects.get(name=name)  # 修改为 Department
            client.delete()
            return JsonResponse({'status': 'success'})
        except Department.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Client not found'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error'}, status=400)

@login_required
@permission_required('comprehensive.change_department', raise_exception=True)
def save_client(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            name = data.get('name')
            department_leader = data.get('department_leader')
            department_email = data.get('department_email')
            tech_center_leader = data.get('tech_center_leader')
            leader_email = data.get('leader_email')
            projects = data.get('projects')

            department, created = Department.objects.update_or_create(
                name=name,
                defaults={
                    'department_leader': department_leader,
                    'department_email': department_email,
                    'tech_center_leader': tech_center_leader,
                    'leader_email': leader_email,
                    'projects': projects,
                }
            )
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)
