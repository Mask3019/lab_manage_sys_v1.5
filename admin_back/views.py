from django.shortcuts import render, redirect

# Create your views here.
def admin_back(request):
    # context = {
    #     'user': 'S007158',
    # }
    return render(request, 'admin_index.html')

