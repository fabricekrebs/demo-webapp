from django.contrib.auth.models import User

from rest_framework import serializers

from tasks.models import Project, Task


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email"]


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ["id", "name", "description"]


class TaskSerializer(serializers.ModelSerializer):
    owner = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), write_only=True)
    owner_detail = UserSerializer(source="owner", read_only=True)
    project = ProjectSerializer(allow_null=True, read_only=True)
    project_id = serializers.PrimaryKeyRelatedField(
        queryset=Project.objects.all(), source="project", write_only=True, allow_null=True, required=False
    )

    class Meta:
        model = Task
        fields = [
            "id",
            "title",
            "description",
            "owner",
            "owner_detail",
            "project",
            "project_id",
            "creation_date",
            "due_date",
            "duration",
            "priority",
        ]

    def create(self, validated_data):
        owner = validated_data.pop("owner")
        project = validated_data.pop("project", None)
        return Task.objects.create(owner=owner, project=project, **validated_data)

    def update(self, instance, validated_data):
        owner = validated_data.pop("owner", None)
        project = validated_data.pop("project", None)
        if owner is not None:
            instance.owner = owner
        if project is not None:
            instance.project = project
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep["owner"] = rep.pop("owner_detail")
        rep["project"] = rep["project"]
        rep.pop("project_id", None)
        return rep
