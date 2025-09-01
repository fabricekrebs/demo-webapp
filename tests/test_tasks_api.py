"""
Unit tests for the Tasks API endpoints.
"""

from django.urls import reverse

from rest_framework import status

from tasks.models import Task

from .test_base import BaseAPITestCase


class TaskAPITestCase(BaseAPITestCase):
    """Test cases for Task API endpoints."""

    def test_task_list_get(self):
        """Test retrieving list of tasks."""
        # Create some test tasks
        task1 = self.create_test_task(title="Task 1")
        task2 = self.create_test_task(title="Task 2")

        url = reverse("task-list-create")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]["title"], "Task 1")
        self.assertEqual(response.data[1]["title"], "Task 2")

    def test_task_list_empty(self):
        """Test retrieving empty task list."""
        url = reverse("task-list-create")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_task_create_success(self):
        """Test creating a new task successfully."""
        url = reverse("task-list-create")
        data = {
            "title": "New Test Task",
            "description": "This is a new test task",
            "owner": self.test_user.id,
            "project_id": self.test_project.id,
            "priority": 1,
            "duration": "02:30:00",  # 2.5 hours
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["title"], "New Test Task")
        self.assertEqual(response.data["description"], "This is a new test task")
        self.assertEqual(response.data["owner"]["id"], self.test_user.id)
        self.assertEqual(response.data["project"]["id"], self.test_project.id)
        self.assertEqual(response.data["priority"], 1)

        # Verify task was created in database
        self.assertEqual(Task.objects.count(), 1)
        created_task = Task.objects.first()
        self.assertEqual(created_task.title, "New Test Task")

    def test_task_create_without_project(self):
        """Test creating a task without a project."""
        url = reverse("task-list-create")
        data = {
            "title": "Task Without Project",
            "description": "This task has no project",
            "owner": self.test_user.id,
            "priority": 2,
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["title"], "Task Without Project")
        self.assertIsNone(response.data["project"])

    def test_task_create_invalid_data(self):
        """Test creating a task with invalid data."""
        url = reverse("task-list-create")
        data = {"description": "Task without title", "owner": self.test_user.id}

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("title", response.data)

    def test_task_create_invalid_owner(self):
        """Test creating a task with invalid owner."""
        url = reverse("task-list-create")
        data = {"title": "Test Task", "owner": 99999}  # Non-existent user ID

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_task_detail_get(self):
        """Test retrieving a specific task."""
        task = self.create_test_task(title="Specific Task")

        url = reverse("task-detail", kwargs={"pk": task.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Specific Task")
        self.assertEqual(response.data["id"], task.id)

    def test_task_detail_not_found(self):
        """Test retrieving a non-existent task."""
        url = reverse("task-detail", kwargs={"pk": 99999})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_task_update_put(self):
        """Test updating a task with PUT."""
        task = self.create_test_task(title="Original Title")

        url = reverse("task-detail", kwargs={"pk": task.id})
        data = {
            "title": "Updated Title",
            "description": "Updated description",
            "owner": self.test_user.id,
            "project_id": self.test_project.id,
            "priority": 1,
        }

        response = self.client.put(url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Updated Title")
        self.assertEqual(response.data["description"], "Updated description")
        self.assertEqual(response.data["priority"], 1)

        # Verify task was updated in database
        task.refresh_from_db()
        self.assertEqual(task.title, "Updated Title")

    def test_task_update_patch(self):
        """Test partially updating a task with PATCH."""
        task = self.create_test_task(title="Original Title", priority=3)

        url = reverse("task-detail", kwargs={"pk": task.id})
        data = {"title": "Patched Title"}

        response = self.client.patch(url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Patched Title")
        self.assertEqual(response.data["priority"], 3)  # Should remain unchanged

        # Verify task was updated in database
        task.refresh_from_db()
        self.assertEqual(task.title, "Patched Title")
        self.assertEqual(task.priority, 3)

    def test_task_delete(self):
        """Test deleting a task."""
        task = self.create_test_task(title="Task to Delete")

        url = reverse("task-detail", kwargs={"pk": task.id})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Verify task was deleted from database
        self.assertEqual(Task.objects.count(), 0)

    def test_task_serialization_fields(self):
        """Test that task serialization includes all expected fields."""
        task = self.create_test_task()

        url = reverse("task-detail", kwargs={"pk": task.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        expected_fields = [
            "id",
            "title",
            "description",
            "owner",
            "project",
            "creation_date",
            "due_date",
            "duration",
            "priority",
        ]

        for field in expected_fields:
            self.assertIn(field, response.data)

    def test_task_owner_detail_serialization(self):
        """Test that task owner is properly serialized with details."""
        task = self.create_test_task()

        url = reverse("task-detail", kwargs={"pk": task.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("owner", response.data)
        self.assertIn("id", response.data["owner"])
        self.assertIn("username", response.data["owner"])
        self.assertIn("email", response.data["owner"])
        self.assertEqual(response.data["owner"]["username"], self.test_user.username)

    def test_task_project_detail_serialization(self):
        """Test that task project is properly serialized with details."""
        task = self.create_test_task()

        url = reverse("task-detail", kwargs={"pk": task.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("project", response.data)
        self.assertIn("id", response.data["project"])
        self.assertIn("name", response.data["project"])
        self.assertIn("description", response.data["project"])
        self.assertEqual(response.data["project"]["name"], self.test_project.name)
