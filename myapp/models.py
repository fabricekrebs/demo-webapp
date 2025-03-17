from django.db import models

class Task(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    owner = models.CharField(max_length=100)  # Changed to CharField for text input
    creation_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField(blank=True, null=True)
    duration = models.DurationField(blank=True, null=True)
    priority = models.IntegerField(choices=[(1, 'High'), (2, 'Medium'), (3, 'Low'), (4, 'Very Low')], default=3)

    def __str__(self):
        return self.title