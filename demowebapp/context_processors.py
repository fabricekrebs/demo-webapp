from django.conf import settings

from .version import get_cached_version


def backend_address(request):
    return {"backend_address": str(settings.BACKEND_ADDRESS)}


def app_version(request):
    """Add application version to all template contexts."""
    return {"app_version": get_cached_version()}
