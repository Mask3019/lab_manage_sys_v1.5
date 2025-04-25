from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate,logout
from django.contrib.auth.forms import AuthenticationForm

# Create your views here.
# @login_required
def person_center(request):
    context = {
        'task_add': '5',
        'task_delay': '2',
        'task_sum': '25',
    }
    return render(request, 'index_person.html', context)