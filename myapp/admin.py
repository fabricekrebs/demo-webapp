from django.contrib import admin

# Register your models here.
from .models import Task

class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'creation_date', 'due_date', 'priority')
    search_fields = ('title', 'description', 'owner__username')
    list_filter = ('priority', 'creation_date', 'due_date')

admin.site.register(Task, TaskAdmin)