from django.db import models
from django.contrib.auth.models import User

# Project and Task models moved from tasks.models
class Project(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class Task(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks', null=True, blank=True)
    creation_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField(blank=True, null=True)
    duration = models.DurationField(blank=True, null=True)
    priority = models.IntegerField(choices=[(1, 'High'), (2, 'Medium'), (3, 'Low'), (4, 'Very Low')], default=3)

    def __str__(self):
        return self.title
