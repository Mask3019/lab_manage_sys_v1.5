from django.shortcuts import render, redirect

# Create your views here.
def dismantle_apply(request):
    context = {
        'page_title': '拆解任务申请',
    }
    return render(request, 'dismantle_apply.html', context)

def dismantle_register(request):
    context = {
        'page_title': '拆解结果登记',
    }
    return render(request, 'dismantle_register.html', context)

def dismantle_issue(request):
    context = {
        'page_title': '失效问题汇总',
    }
    return render(request, 'dismantle_issue_summary.html', context)

def dismantle_PQCP(request):
    context = {
        'page_title': 'PQCP登记',
    }
    return render(request, 'dismantle_PQCP.html', context)
