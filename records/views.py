from django.conf import settings
from django.shortcuts import render
import requests

def task_list(request):
    context = {
        'backend_address': settings.BACKEND_ADDRESS,
        'db_host': settings.DB_HOST,
    }
    print("hello")
    return render(request, 'records/task_list.html', context)
