from django.urls import path
from .views import TaskListCreate, TaskDetail, ProjectListCreate, ProjectDetail, UserListCreate
from tasks.views import ChatListCreateView, ChatDetailView, ChatMessageCreateView, chatbot_config

urlpatterns = [
    path('tasks/', TaskListCreate.as_view(), name='task-list-create'),
    path('tasks/<int:pk>/', TaskDetail.as_view(), name='task-detail'),
    path('projects/', ProjectListCreate.as_view(), name='project-list-create'),
    path('projects/<int:pk>/', ProjectDetail.as_view(), name='project-detail'),
    path('users/', UserListCreate.as_view(), name='user-list-create'),
    path('chats/', ChatListCreateView.as_view(), name='chat-list-create'),
    path('chats/<int:pk>/', ChatDetailView.as_view(), name='chat-detail'),
    path('chats/<int:chat_id>/messages/', ChatMessageCreateView.as_view(), name='chat-message-create'),
    path('chats/config/', chatbot_config, name='chatbot-config'),
]