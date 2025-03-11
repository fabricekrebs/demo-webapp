from django.conf import settings

def backend_address(request):
    return {
        'backend_address': settings.BACKEND_ADDRESS
    }