from django.contrib import admin

from tasks.models import Project, Task


class TaskAdmin(admin.ModelAdmin):
    list_display = ("title", "owner", "project", "creation_date", "due_date", "priority")
    search_fields = ("title", "description", "owner__username", "project__name")
    list_filter = ("priority", "creation_date", "due_date", "project")


admin.site.register(Task, TaskAdmin)
admin.site.register(Project)
