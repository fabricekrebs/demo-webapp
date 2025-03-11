from django.shortcuts import render
import requests

def task_list(request):
    return render(request, 'records/task_list.html')
