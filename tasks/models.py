from django.contrib.auth.models import User
from django.db import models


# Project and Task models moved from tasks.models
class Project(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class Task(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tasks")
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="tasks", null=True, blank=True)
    creation_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField(blank=True, null=True)
    duration = models.DurationField(blank=True, null=True)
    priority = models.IntegerField(choices=[(1, "High"), (2, "Medium"), (3, "Low"), (4, "Very Low")], default=3)

    def __str__(self):
        return self.title


class Chat(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=255, blank=True, null=True)
    azure_thread_id = models.CharField(max_length=128, null=True, blank=True)

    def __str__(self):
        return self.title or f"Chat {self.id}"


class ChatMessage(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name="messages")
    message = models.TextField()
    is_bot = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Add fields for async processing
    PROCESSING_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    processing_status = models.CharField(
        max_length=20, 
        choices=PROCESSING_STATUS_CHOICES, 
        default='completed',
        help_text="Status of message processing for Azure AI responses"
    )
    azure_run_id = models.CharField(max_length=128, null=True, blank=True, help_text="Azure AI run ID for tracking")
    error_message = models.TextField(null=True, blank=True, help_text="Error message if processing failed")

    def __str__(self):
        return f"{'Bot' if self.is_bot else 'User'}: {self.message[:30]}..."
