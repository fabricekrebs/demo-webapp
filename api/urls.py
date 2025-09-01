from django.urls import path

from tasks.views import (
    ChatDetailView,
    ChatListCreateView,
    ChatMessageCreateView,
    chatbot_config,
    clear_conversation,
    conversation_summary,
)

from .views import ProjectDetail, ProjectListCreate, TaskDetail, TaskListCreate, UserListCreate, app_info

urlpatterns = [
    path("info/", app_info, name="app-info"),
    path("tasks/", TaskListCreate.as_view(), name="task-list-create"),
    path("tasks/<int:pk>/", TaskDetail.as_view(), name="task-detail"),
    path("projects/", ProjectListCreate.as_view(), name="project-list-create"),
    path("projects/<int:pk>/", ProjectDetail.as_view(), name="project-detail"),
    path("users/", UserListCreate.as_view(), name="user-list-create"),
    path("chats/", ChatListCreateView.as_view(), name="chat-list-create"),
    path("chats/<int:pk>/", ChatDetailView.as_view(), name="chat-detail"),
    path("chats/<int:chat_id>/messages/", ChatMessageCreateView.as_view(), name="chat-message-create"),
    path("chats/<int:chat_id>/clear/", clear_conversation, name="clear-conversation"),
    path("chats/<int:chat_id>/summary/", conversation_summary, name="conversation-summary"),
    path("chats/config/", chatbot_config, name="chatbot-config"),
]
