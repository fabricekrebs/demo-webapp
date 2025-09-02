from rest_framework import serializers

from .models import Chat, ChatMessage


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ["id", "chat", "message", "is_bot", "created_at", "processing_status", "azure_run_id", "error_message"]


class ChatSerializer(serializers.ModelSerializer):
    messages = ChatMessageSerializer(many=True, read_only=True)

    class Meta:
        model = Chat
        fields = ["id", "created_at", "title", "messages"]
