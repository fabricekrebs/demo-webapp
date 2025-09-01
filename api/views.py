from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from rest_framework import generics

from demowebapp.version import get_cached_version
from tasks.models import Project, Task

from .serializers import ProjectSerializer, TaskSerializer, UserSerializer


class TaskListCreate(generics.ListCreateAPIView):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer


class TaskDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer


class ProjectListCreate(generics.ListCreateAPIView):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer


class ProjectDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer


class UserListCreate(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer


@csrf_exempt
@require_http_methods(["GET"])
def app_info(request):
    """
    API endpoint that returns basic application information including version.
    This endpoint can be used by the frontend to display app info.
    """
    return JsonResponse({"name": "demo-webapp", "version": get_cached_version(), "description": "Demo Web Application"})
