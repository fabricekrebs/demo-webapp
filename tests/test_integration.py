"""
Integration tests for API workflows and cross-endpoint functionality.
"""

from unittest.mock import patch

from django.urls import reverse

from rest_framework import status

from tasks.models import Project, Task

from .test_base import BaseAPITestCase


class APIIntegrationTestCase(BaseAPITestCase):
    """Integration tests for API workflows."""

    def test_full_task_lifecycle(self):
        """Test complete task lifecycle: create, read, update, delete."""
        # Step 1: Create a project
        project_url = reverse("project-list-create")
        project_data = {"name": "Integration Test Project", "description": "Project for integration testing"}
        project_response = self.client.post(project_url, project_data)
        self.assertEqual(project_response.status_code, status.HTTP_201_CREATED)
        project_id = project_response.data["id"]

        # Step 2: Create a task in the project
        task_url = reverse("task-list-create")
        task_data = {
            "title": "Integration Test Task",
            "description": "Task for integration testing",
            "owner": self.test_user.id,
            "project_id": project_id,
            "priority": 1,
        }
        task_response = self.client.post(task_url, task_data)
        self.assertEqual(task_response.status_code, status.HTTP_201_CREATED)
        task_id = task_response.data["id"]

        # Step 3: Read the task
        task_detail_url = reverse("task-detail", kwargs={"pk": task_id})
        get_response = self.client.get(task_detail_url)
        self.assertEqual(get_response.status_code, status.HTTP_200_OK)
        self.assertEqual(get_response.data["title"], "Integration Test Task")
        self.assertEqual(get_response.data["project"]["name"], "Integration Test Project")

        # Step 4: Update the task
        update_data = {
            "title": "Updated Integration Test Task",
            "description": "Updated description",
            "owner": self.test_user.id,
            "project_id": project_id,
            "priority": 2,
        }
        update_response = self.client.put(task_detail_url, update_data)
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        self.assertEqual(update_response.data["title"], "Updated Integration Test Task")

        # Step 5: Delete the task
        delete_response = self.client.delete(task_detail_url)
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)

        # Step 6: Verify deletion
        get_after_delete = self.client.get(task_detail_url)
        self.assertEqual(get_after_delete.status_code, status.HTTP_404_NOT_FOUND)

    def test_task_project_relationship(self):
        """Test task-project relationship in various scenarios."""
        # Create multiple projects
        project1 = Project.objects.create(name="Project 1", description="First project")
        project2 = Project.objects.create(name="Project 2", description="Second project")

        # Create tasks in different projects
        task1_data = {"title": "Task in Project 1", "owner": self.test_user.id, "project_id": project1.id}
        task2_data = {"title": "Task in Project 2", "owner": self.test_user.id, "project_id": project2.id}
        task3_data = {"title": "Task without Project", "owner": self.test_user.id}

        task_url = reverse("task-list-create")

        # Create tasks
        response1 = self.client.post(task_url, task1_data)
        response2 = self.client.post(task_url, task2_data)
        response3 = self.client.post(task_url, task3_data)

        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response3.status_code, status.HTTP_201_CREATED)

        # Verify project associations
        self.assertEqual(response1.data["project"]["name"], "Project 1")
        self.assertEqual(response2.data["project"]["name"], "Project 2")
        self.assertIsNone(response3.data["project"])

        # Verify tasks are properly listed
        list_response = self.client.get(task_url)
        self.assertEqual(len(list_response.data), 3)

    def test_user_task_ownership(self):
        """Test task ownership by different users."""
        # Create task with test_user
        task_data = {"title": "User 1 Task", "owner": self.test_user.id, "project_id": self.test_project.id}
        task_url = reverse("task-list-create")
        response1 = self.client.post(task_url, task_data)
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)

        # Create task with test_user2
        task_data2 = {"title": "User 2 Task", "owner": self.test_user2.id, "project_id": self.test_project.id}
        response2 = self.client.post(task_url, task_data2)
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)

        # Verify ownership in responses
        self.assertEqual(response1.data["owner"]["username"], "testuser")
        self.assertEqual(response2.data["owner"]["username"], "testuser2")

        # List all tasks
        list_response = self.client.get(task_url)
        self.assertEqual(len(list_response.data), 2)

    def test_chat_message_workflow(self):
        """Test complete chat and message workflow."""
        # Step 1: Create a chat
        chat_url = reverse("chat-list-create")
        chat_data = {"title": "Integration Test Chat"}
        chat_response = self.client.post(chat_url, chat_data)
        self.assertEqual(chat_response.status_code, status.HTTP_201_CREATED)
        chat_id = chat_response.data["id"]

        # Step 2: Send messages to chat (mock chatbot to avoid Azure integration)
        message_url = reverse("chat-message-create", kwargs={"chat_id": chat_id})

        with (
            patch("tasks.views.is_chatbot_enabled") as mock_enabled,
            patch("tasks.views.get_chatbot_service") as mock_service,
        ):

            mock_enabled.return_value = True
            mock_chatbot = mock_service.return_value
            mock_chatbot.send_message.return_value = "Bot response"

            # Send first message
            message_data1 = {"message": "Hello, this is my first message"}
            response1 = self.client.post(message_url, message_data1, format="json")
            self.assertEqual(response1.status_code, status.HTTP_200_OK)

            # Send second message
            message_data2 = {"message": "This is my second message"}
            response2 = self.client.post(message_url, message_data2, format="json")
            self.assertEqual(response2.status_code, status.HTTP_200_OK)

        # Step 3: Retrieve chat with messages
        chat_detail_url = reverse("chat-detail", kwargs={"pk": chat_id})
        chat_detail = self.client.get(chat_detail_url)
        self.assertEqual(chat_detail.status_code, status.HTTP_200_OK)
        self.assertEqual(len(chat_detail.data["messages"]), 4)  # 2 user + 2 bot messages

        # Step 4: Get conversation summary
        summary_url = reverse("conversation-summary", kwargs={"chat_id": chat_id})
        summary_response = self.client.get(summary_url)
        self.assertEqual(summary_response.status_code, status.HTTP_200_OK)
        # Note: Summary will be empty list since chat doesn't have azure_thread_id
        self.assertEqual(summary_response.data["summary"], [])

        # Step 5: Clear conversation
        clear_url = reverse("clear-conversation", kwargs={"chat_id": chat_id})
        with (
            patch("tasks.views.is_chatbot_enabled") as mock_enabled,
            patch("tasks.views.get_chatbot_service") as mock_service,
        ):

            mock_enabled.return_value = True
            mock_chatbot = mock_service.return_value
            mock_chatbot.clear_conversation.return_value = True

            clear_response = self.client.post(clear_url)
            self.assertEqual(clear_response.status_code, status.HTTP_200_OK)

        # Step 6: Verify messages are still there (current implementation doesn't clear local messages)
        chat_after_clear = self.client.get(chat_detail_url)
        self.assertEqual(len(chat_after_clear.data["messages"]), 4)

        # Step 7: Delete chat
        delete_response = self.client.delete(chat_detail_url)
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)

    def test_project_deletion_cascade(self):
        """Test that deleting a project cascades to its tasks."""
        # Create a project with tasks
        project = Project.objects.create(name="Project to Delete", description="Will be deleted")

        # Create multiple tasks in the project
        task1 = Task.objects.create(title="Task 1", owner=self.test_user, project=project)
        task2 = Task.objects.create(title="Task 2", owner=self.test_user2, project=project)

        # Verify tasks exist
        self.assertEqual(Task.objects.filter(project=project).count(), 2)

        # Delete the project via API
        project_url = reverse("project-detail", kwargs={"pk": project.id})
        delete_response = self.client.delete(project_url)
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)

        # Verify project and its tasks are deleted
        self.assertEqual(Project.objects.filter(id=project.id).count(), 0)
        self.assertEqual(Task.objects.filter(project=project).count(), 0)

    def test_error_handling_cascade(self):
        """Test error handling in various cascade scenarios."""
        # Try to create task with non-existent project
        task_url = reverse("task-list-create")
        invalid_task_data = {
            "title": "Task with Invalid Project",
            "owner": self.test_user.id,
            "project_id": 99999,  # Non-existent project
        }

        response = self.client.post(task_url, invalid_task_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Try to create task with non-existent user
        invalid_user_data = {"title": "Task with Invalid User", "owner": 99999}  # Non-existent user

        response = self.client.post(task_url, invalid_user_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_api_consistency_across_endpoints(self):
        """Test consistency of data representation across different endpoints."""
        # Create test data
        project = Project.objects.create(name="Consistency Test Project")
        task = Task.objects.create(title="Consistency Test Task", owner=self.test_user, project=project, priority=1)

        # Get task from task detail endpoint
        task_detail_url = reverse("task-detail", kwargs={"pk": task.id})
        task_detail = self.client.get(task_detail_url)

        # Get task from task list endpoint
        task_list_url = reverse("task-list-create")
        task_list = self.client.get(task_list_url)

        # Data should be consistent between endpoints
        task_from_detail = task_detail.data
        task_from_list = next((t for t in task_list.data if t["id"] == task.id), None)

        self.assertIsNotNone(task_from_list)

        # Compare key fields
        for field in ["id", "title", "priority"]:
            self.assertEqual(task_from_detail[field], task_from_list[field])

        # Verify nested objects are consistently serialized
        self.assertEqual(task_from_detail["owner"]["username"], task_from_list["owner"]["username"])
        self.assertEqual(task_from_detail["project"]["name"], task_from_list["project"]["name"])
