from django.conf import settings
from django.shortcuts import render
import logging
from datetime import datetime

def task_list(request):
    if settings.BACKEND_SAME_HOST == 'True':
        scheme = 'https' if request.is_secure() else 'http'
        
        backendAddress = f"{scheme}://{request.get_host()}"
    else:
        backendAddress = settings.BACKEND_ADDRESS

    context = {
        'backend_address': backendAddress,
        'db_host': settings.DB_HOST,
    }

    return render(request, 'records/task_list.html', context)

def logger_view(request):
    logger = logging.getLogger("django")
    logger.info(f"Logger is working! Current time: {datetime.now().isoformat()}")
    return render(request, 'records/logger.html')
