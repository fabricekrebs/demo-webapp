"""
Unit tests for Django models.
"""

from datetime import datetime, timedelta

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from tasks.models import Chat, ChatMessage, Project, Task

from .test_base import BaseTestCase


class ProjectModelTestCase(BaseTestCase):
    """Test cases for Project model."""

    def test_project_creation(self):
        """Test creating a project."""
        project = Project.objects.create(name="Test Project Model", description="Testing project model")

        self.assertEqual(project.name, "Test Project Model")
        self.assertEqual(project.description, "Testing project model")
        self.assertTrue(isinstance(project.id, int))

    def test_project_str_method(self):
        """Test project string representation."""
        project = Project.objects.create(name="String Test Project")
        self.assertEqual(str(project), "String Test Project")

    def test_project_without_description(self):
        """Test creating project without description."""
        project = Project.objects.create(name="No Description Project")
        self.assertEqual(project.name, "No Description Project")
        self.assertIsNone(project.description)

    def test_project_name_max_length(self):
        """Test project name maximum length constraint."""
        long_name = "x" * 201  # Exceeds 200 character limit

        with self.assertRaises(ValidationError):
            project = Project(name=long_name)
            project.full_clean()  # Triggers validation

    def test_project_name_required(self):
        """Test that project name is required."""
        with self.assertRaises(ValidationError):
            project = Project(description="Project without name")
            project.full_clean()


class TaskModelTestCase(BaseTestCase):
    """Test cases for Task model."""

    def test_task_creation(self):
        """Test creating a task."""
        task = self.create_test_task(title="Model Test Task")

        self.assertEqual(task.title, "Model Test Task")
        self.assertEqual(task.description, "A test task")
        self.assertEqual(task.owner, self.test_user)
        self.assertEqual(task.project, self.test_project)
        self.assertEqual(task.priority, 2)
        self.assertIsNotNone(task.creation_date)

    def test_task_str_method(self):
        """Test task string representation."""
        task = self.create_test_task(title="String Test Task")
        self.assertEqual(str(task), "String Test Task")

    def test_task_without_project(self):
        """Test creating task without project."""
        task = Task.objects.create(title="Task Without Project", owner=self.test_user, priority=1)

        self.assertEqual(task.title, "Task Without Project")
        self.assertIsNone(task.project)

    def test_task_title_max_length(self):
        """Test task title maximum length constraint."""
        long_title = "x" * 201  # Exceeds 200 character limit

        with self.assertRaises(ValidationError):
            task = Task(title=long_title, owner=self.test_user)
            task.full_clean()

    def test_task_title_required(self):
        """Test that task title is required."""
        with self.assertRaises(ValidationError):
            task = Task(owner=self.test_user, description="Task without title")
            task.full_clean()

    def test_task_owner_required(self):
        """Test that task owner is required."""
        with self.assertRaises(ValidationError):
            task = Task(title="Task Without Owner")
            task.full_clean()

    def test_task_priority_choices(self):
        """Test task priority choices."""
        valid_priorities = [1, 2, 3, 4]

        for priority in valid_priorities:
            task = Task.objects.create(title=f"Task Priority {priority}", owner=self.test_user, priority=priority)
            self.assertEqual(task.priority, priority)

    def test_task_priority_default(self):
        """Test task priority default value."""
        task = Task.objects.create(title="Default Priority Task", owner=self.test_user)
        self.assertEqual(task.priority, 3)  # Default is 'Low'

    def test_task_creation_date_auto_now_add(self):
        """Test that creation_date is automatically set."""
        task = self.create_test_task()

        # Just verify that creation_date is set and is recent (within last minute)
        self.assertIsNotNone(task.creation_date)
        from django.utils import timezone

        time_diff = timezone.now() - task.creation_date
        self.assertLess(time_diff.total_seconds(), 60)  # Created within last 60 seconds

    def test_task_due_date_optional(self):
        """Test that due_date is optional."""
        task = self.create_test_task()
        self.assertIsNone(task.due_date)

    def test_task_duration_optional(self):
        """Test that duration is optional."""
        task = self.create_test_task()
        self.assertIsNone(task.duration)

    def test_task_cascade_delete_with_owner(self):
        """Test that task is deleted when owner is deleted."""
        task = self.create_test_task()
        task_id = task.id

        # Delete the owner
        self.test_user.delete()

        # Task should be deleted due to CASCADE
        with self.assertRaises(Task.DoesNotExist):
            Task.objects.get(id=task_id)

    def test_task_cascade_delete_with_project(self):
        """Test that task is deleted when project is deleted."""
        task = self.create_test_task()
        task_id = task.id

        # Delete the project
        self.test_project.delete()

        # Task should be deleted due to CASCADE
        with self.assertRaises(Task.DoesNotExist):
            Task.objects.get(id=task_id)


class ChatModelTestCase(BaseTestCase):
    """Test cases for Chat model."""

    def test_chat_creation(self):
        """Test creating a chat."""
        chat = Chat.objects.create(title="Test Chat Model")

        self.assertEqual(chat.title, "Test Chat Model")
        self.assertIsNotNone(chat.created_at)
        self.assertIsNone(chat.azure_thread_id)

    def test_chat_without_title(self):
        """Test creating chat without title."""
        chat = Chat.objects.create()

        self.assertIsNone(chat.title)
        self.assertIsNotNone(chat.created_at)

    def test_chat_str_method_with_title(self):
        """Test chat string representation with title."""
        chat = Chat.objects.create(title="Named Chat")
        self.assertEqual(str(chat), "Named Chat")

    def test_chat_str_method_without_title(self):
        """Test chat string representation without title."""
        chat = Chat.objects.create()
        expected_str = f"Chat {chat.id}"
        self.assertEqual(str(chat), expected_str)

    def test_chat_created_at_auto_now_add(self):
        """Test that created_at is automatically set."""
        chat = Chat.objects.create(title="Time Test Chat")

        # Just verify that created_at is set and is recent (within last minute)
        self.assertIsNotNone(chat.created_at)
        from django.utils import timezone

        time_diff = timezone.now() - chat.created_at
        self.assertLess(time_diff.total_seconds(), 60)  # Created within last 60 seconds

    def test_chat_azure_thread_id_optional(self):
        """Test that azure_thread_id is optional."""
        chat = Chat.objects.create(title="Azure ID Test")
        self.assertIsNone(chat.azure_thread_id)

        chat_with_thread_id = Chat.objects.create(title="With Azure Thread ID", azure_thread_id="test-thread-123")
        self.assertEqual(chat_with_thread_id.azure_thread_id, "test-thread-123")


class ChatMessageModelTestCase(BaseTestCase):
    """Test cases for ChatMessage model."""

    def setUp(self):
        """Set up test data."""
        super().setUp()
        self.test_chat = Chat.objects.create(title="Test Chat for Messages")

    def test_chat_message_creation(self):
        """Test creating a chat message."""
        message = ChatMessage.objects.create(chat=self.test_chat, message="Test message content", is_bot=False)

        self.assertEqual(message.chat, self.test_chat)
        self.assertEqual(message.message, "Test message content")
        self.assertFalse(message.is_bot)
        self.assertIsNotNone(message.created_at)

    def test_chat_message_bot_flag(self):
        """Test chat message with bot flag."""
        bot_message = ChatMessage.objects.create(chat=self.test_chat, message="Bot response", is_bot=True)

        self.assertTrue(bot_message.is_bot)

    def test_chat_message_default_is_bot(self):
        """Test chat message default is_bot value."""
        message = ChatMessage.objects.create(chat=self.test_chat, message="Default is_bot message")

        self.assertFalse(message.is_bot)  # Default should be False

    def test_chat_message_str_method_user(self):
        """Test chat message string representation for user."""
        message = ChatMessage.objects.create(chat=self.test_chat, message="User message for string test", is_bot=False)

        expected_str = "User: User message for string test..."
        self.assertEqual(str(message), expected_str)

    def test_chat_message_str_method_bot(self):
        """Test chat message string representation for bot."""
        message = ChatMessage.objects.create(chat=self.test_chat, message="Bot message for string test", is_bot=True)

        expected_str = "Bot: Bot message for string test..."
        self.assertEqual(str(message), expected_str)

    def test_chat_message_str_method_long_message(self):
        """Test chat message string representation for long message."""
        long_message = "This is a very long message that should be truncated in the string representation"

        message = ChatMessage.objects.create(chat=self.test_chat, message=long_message, is_bot=False)

        expected_str = f"User: {long_message[:30]}..."
        self.assertEqual(str(message), expected_str)

    def test_chat_message_created_at_auto_now_add(self):
        """Test that created_at is automatically set."""
        message = ChatMessage.objects.create(chat=self.test_chat, message="Time test message")

        # Just verify that created_at is set and is recent (within last minute)
        self.assertIsNotNone(message.created_at)
        from django.utils import timezone

        time_diff = timezone.now() - message.created_at
        self.assertLess(time_diff.total_seconds(), 60)  # Created within last 60 seconds

    def test_chat_message_cascade_delete_with_chat(self):
        """Test that message is deleted when chat is deleted."""
        message = ChatMessage.objects.create(chat=self.test_chat, message="Message to be cascaded")
        message_id = message.id

        # Delete the chat
        self.test_chat.delete()

        # Message should be deleted due to CASCADE
        with self.assertRaises(ChatMessage.DoesNotExist):
            ChatMessage.objects.get(id=message_id)

    def test_chat_message_related_name(self):
        """Test chat message related name functionality."""
        ChatMessage.objects.create(chat=self.test_chat, message="Message 1")
        ChatMessage.objects.create(chat=self.test_chat, message="Message 2")

        # Test related name 'messages' works
        messages = self.test_chat.messages.all()
        self.assertEqual(messages.count(), 2)

        message_texts = [msg.message for msg in messages]
        self.assertIn("Message 1", message_texts)
        self.assertIn("Message 2", message_texts)
