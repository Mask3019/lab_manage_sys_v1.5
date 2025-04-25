from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate,logout
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpResponseRedirect,JsonResponse
from django.urls import reverse
from django.views.decorators.http import require_POST

# Create your views here.
def index(request):
    return render(request, 'index.html')

def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse('index:index'))  # Redirect to a home page or other page after login
        else:
            # Return an 'invalid login' error message.
            return render(request, 'user_login.html', {'error_message': 'Invalid login'})

    return render(request, 'index.html')

@require_POST
def user_logout(request):
    logout(request)
    return redirect('index:index')  # Redirect to a home page after logout


def user_login_ajax(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return JsonResponse({'msg': '登录成功', 'status': 'success'})
        else:
            return JsonResponse({'msg': '用户名或密码错误', 'status': 'fail'})
    return JsonResponse({'msg': '无效的请求方式', 'status': 'fail'})

