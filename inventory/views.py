from django.shortcuts import render, redirect

# Create your views here.
def inventory_in(request):
    context = {
        'page_title': '入库登记',
    }
    return render(request, 'inventory_in.html', context)

def inventory_out(request):
    context = {
        'page_title': '出库登记',
    }
    return render(request, 'inventory_out.html', context)

def inventory_alarm(request):
    context = {
        'page_title': '库存预警',
    }
    return render(request, 'inventory_alarm.html', context)

def inventory_discard(request):
    context = {
        'page_title': '报废统计',
    }
    return render(request, 'inventory_discard.html', context)
