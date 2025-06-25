from django.urls import path
from .views import TaskListCreate, TaskDetail, ProjectListCreate, ProjectDetail, UserListCreate

urlpatterns = [
    path('tasks/', TaskListCreate.as_view(), name='task-list-create'),
    path('tasks/<int:pk>/', TaskDetail.as_view(), name='task-detail'),
    path('projects/', ProjectListCreate.as_view(), name='project-list-create'),
    path('projects/<int:pk>/', ProjectDetail.as_view(), name='project-detail'),
    path('users/', UserListCreate.as_view(), name='user-list-create'),
]