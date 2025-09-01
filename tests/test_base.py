"""
Base test configuration and utilities for the demo webapp.
"""

from django.contrib.auth.models import User
from django.test import TestCase

from rest_framework.test import APITestCase

from tasks.models import Chat, ChatMessage, Project, Task


class BaseTestCase(TestCase):
    """Base test case with common setup methods."""

    def setUp(self):
        """Set up test data."""
        test_password = "testpass123"  # nosec B105
        self.test_user = User.objects.create_user(username="testuser", email="test@example.com", password=test_password)
        self.test_project = Project.objects.create(name="Test Project", description="A test project")

    def create_test_task(self, title="Test Task", owner=None, project=None, **kwargs):
        """Helper method to create a test task."""
        return Task.objects.create(
            title=title,
            description="A test task",
            owner=owner or self.test_user,
            project=project or self.test_project,
            priority=kwargs.get("priority", 2),
            **{k: v for k, v in kwargs.items() if k != "priority"},
        )


class BaseAPITestCase(APITestCase):
    """Base API test case with authentication setup."""

    def setUp(self):
        """Set up test data and authentication."""
        test_password = "testpass123"  # nosec B105
        self.test_user = User.objects.create_user(username="testuser", email="test@example.com", password=test_password)
        self.test_user2 = User.objects.create_user(username="testuser2", email="test2@example.com", password=test_password)
        self.test_project = Project.objects.create(name="Test Project", description="A test project")

        # Authenticate the client
        self.client.force_authenticate(user=self.test_user)

    def create_test_task(self, title="Test Task", owner=None, project=None, **kwargs):
        """Helper method to create a test task."""
        return Task.objects.create(
            title=title,
            description="A test task",
            owner=owner or self.test_user,
            project=project or self.test_project,
            priority=kwargs.get("priority", 2),
            **{k: v for k, v in kwargs.items() if k != "priority"},
        )

    def create_test_chat(self, title="Test Chat"):
        """Helper method to create a test chat."""
        return Chat.objects.create(title=title)

    def create_test_message(self, chat, message="Test message", is_bot=False):
        """Helper method to create a test chat message."""
        return ChatMessage.objects.create(chat=chat, message=message, is_bot=is_bot)
