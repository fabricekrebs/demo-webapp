from django.urls import path
from . import views

urlpatterns = [
    path('', views.task_list, name='task_list'),
    path('projects/', views.project_list, name='project_list'),
    path('logger/', views.logger_view, name='logger'),
]
