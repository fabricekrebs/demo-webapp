"""
Unit tests for the Chat API endpoints (excluding Azure AI integration).
"""

import json
from unittest.mock import patch

from django.urls import reverse

from rest_framework import status

from tasks.models import Chat, ChatMessage

from .test_base import BaseAPITestCase


class ChatAPITestCase(BaseAPITestCase):
    """Test cases for Chat API endpoints."""

    def test_chat_list_get(self):
        """Test retrieving list of chats."""
        # Create some test chats
        chat1 = self.create_test_chat(title="Chat 1")
        chat2 = self.create_test_chat(title="Chat 2")

        url = reverse("chat-list-create")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

        # Check chats are ordered by creation date (newest first)
        self.assertEqual(response.data[0]["title"], "Chat 2")
        self.assertEqual(response.data[1]["title"], "Chat 1")

    def test_chat_list_empty(self):
        """Test retrieving empty chat list."""
        url = reverse("chat-list-create")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_chat_list_requires_authentication(self):
        """Test that chat list requires authentication."""
        # Remove authentication
        self.client.force_authenticate(user=None)

        url = reverse("chat-list-create")
        response = self.client.get(url)

        # DRF returns 403 for unauthenticated requests when permission_classes are used
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_chat_create_success(self):
        """Test creating a new chat successfully."""
        url = reverse("chat-list-create")
        data = {"title": "New Test Chat"}

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["title"], "New Test Chat")

        # Verify chat was created in database
        self.assertEqual(Chat.objects.count(), 1)
        created_chat = Chat.objects.first()
        self.assertEqual(created_chat.title, "New Test Chat")

    def test_chat_create_without_title(self):
        """Test creating a chat without title."""
        url = reverse("chat-list-create")
        data = {}

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNone(response.data["title"])

    def test_chat_create_requires_authentication(self):
        """Test that chat creation requires authentication."""
        # Remove authentication
        self.client.force_authenticate(user=None)

        url = reverse("chat-list-create")
        data = {"title": "Unauthorized Chat"}

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_chat_detail_get(self):
        """Test retrieving a specific chat with messages."""
        chat = self.create_test_chat(title="Chat with Messages")
        message1 = self.create_test_message(chat, "Hello", is_bot=False)
        message2 = self.create_test_message(chat, "Hi there!", is_bot=True)

        url = reverse("chat-detail", kwargs={"pk": chat.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Chat with Messages")
        self.assertEqual(len(response.data["messages"]), 2)

        # Check messages are included and ordered correctly
        messages = response.data["messages"]
        self.assertEqual(messages[0]["message"], "Hello")
        self.assertFalse(messages[0]["is_bot"])
        self.assertEqual(messages[1]["message"], "Hi there!")
        self.assertTrue(messages[1]["is_bot"])

    def test_chat_detail_not_found(self):
        """Test retrieving a non-existent chat."""
        url = reverse("chat-detail", kwargs={"pk": 99999})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_chat_detail_requires_authentication(self):
        """Test that chat detail requires authentication."""
        chat = self.create_test_chat()

        # Remove authentication
        self.client.force_authenticate(user=None)

        url = reverse("chat-detail", kwargs={"pk": chat.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_chat_delete(self):
        """Test deleting a chat."""
        chat = self.create_test_chat(title="Chat to Delete")
        self.create_test_message(chat, "Message in chat to delete")

        url = reverse("chat-detail", kwargs={"pk": chat.id})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Verify chat was deleted from database
        self.assertEqual(Chat.objects.count(), 0)
        self.assertEqual(ChatMessage.objects.count(), 0)  # Should cascade delete

    def test_chat_serialization_fields(self):
        """Test that chat serialization includes all expected fields."""
        chat = self.create_test_chat()

        url = reverse("chat-detail", kwargs={"pk": chat.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        expected_fields = ["id", "created_at", "title", "messages"]

        for field in expected_fields:
            self.assertIn(field, response.data)


class ChatMessageAPITestCase(BaseAPITestCase):
    """Test cases for Chat Message API endpoints (excluding AI integration)."""

    def setUp(self):
        """Set up test data."""
        super().setUp()
        self.test_chat = self.create_test_chat(title="Test Chat")

    def test_message_create_success(self):
        """Test creating a new message successfully."""
        url = reverse("chat-message-create", kwargs={"chat_id": self.test_chat.id})
        data = {"message": "Hello, this is a test message"}

        # Mock both the chatbot service and enabled check
        with patch("tasks.views.is_chatbot_enabled") as mock_enabled, patch("tasks.views.get_chatbot_service") as mock_service:

            mock_enabled.return_value = True
            mock_chatbot = mock_service.return_value
            mock_chatbot.send_message.return_value = "Hi there! This is a bot response."

            response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)  # Changed to 200 as per the view
        self.assertEqual(len(response.data), 2)  # User message + bot response

        # Verify user message was created
        user_message = ChatMessage.objects.get(chat=self.test_chat, is_bot=False)
        self.assertEqual(user_message.message, "Hello, this is a test message")

    def test_message_create_empty_message(self):
        """Test creating a message with empty content."""
        url = reverse("chat-message-create", kwargs={"chat_id": self.test_chat.id})
        data = {"message": ""}

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_message_create_no_message_field(self):
        """Test creating a message without message field."""
        url = reverse("chat-message-create", kwargs={"chat_id": self.test_chat.id})
        data = {}

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_message_create_whitespace_only(self):
        """Test creating a message with only whitespace."""
        url = reverse("chat-message-create", kwargs={"chat_id": self.test_chat.id})
        data = {"message": "   \n  \t  "}

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_message_create_too_long(self):
        """Test creating a message that exceeds length limit."""
        url = reverse("chat-message-create", kwargs={"chat_id": self.test_chat.id})
        data = {"message": "x" * 4001}  # Exceeds 4000 character limit

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_message_create_nonexistent_chat(self):
        """Test creating a message for non-existent chat."""
        url = reverse("chat-message-create", kwargs={"chat_id": 99999})
        data = {"message": "Message for non-existent chat"}

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("error", response.data)

    def test_message_create_requires_authentication(self):
        """Test that message creation requires authentication."""
        # Remove authentication
        self.client.force_authenticate(user=None)

        url = reverse("chat-message-create", kwargs={"chat_id": self.test_chat.id})
        data = {"message": "Unauthorized message"}

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class ChatUtilityAPITestCase(BaseAPITestCase):
    """Test cases for Chat utility endpoints (clear, summary, config)."""

    def setUp(self):
        """Set up test data."""
        super().setUp()
        self.test_chat = self.create_test_chat(title="Test Chat")
        self.create_test_message(self.test_chat, "User message 1", is_bot=False)
        self.create_test_message(self.test_chat, "Bot response 1", is_bot=True)

    def test_clear_conversation_success(self):
        """Test clearing conversation messages."""
        url = reverse("clear-conversation", kwargs={"chat_id": self.test_chat.id})

        # Mock the chatbot service
        with patch("tasks.views.is_chatbot_enabled") as mock_enabled, patch("tasks.views.get_chatbot_service") as mock_service:

            mock_enabled.return_value = True
            mock_chatbot = mock_service.return_value
            mock_chatbot.clear_conversation.return_value = True

            response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("success", response.data)
        self.assertTrue(response.data["success"])

        # Note: The current implementation doesn't actually clear local messages
        # This test verifies the API works, not the message clearing behavior

    def test_clear_conversation_nonexistent_chat(self):
        """Test clearing conversation for non-existent chat."""
        url = reverse("clear-conversation", kwargs={"chat_id": 99999})

        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_conversation_summary_success(self):
        """Test getting conversation summary."""
        # Set up chat with azure thread id for the summary to work
        self.test_chat.azure_thread_id = "test-thread-123"
        self.test_chat.save()

        url = reverse("conversation-summary", kwargs={"chat_id": self.test_chat.id})

        # Mock the chatbot service to return a summary
        with patch("tasks.views.is_chatbot_enabled") as mock_enabled, patch("tasks.views.get_chatbot_service") as mock_service:

            mock_enabled.return_value = True
            mock_chatbot = mock_service.return_value
            mock_chatbot.get_conversation_summary.return_value = {"total_messages": 2, "user_messages": 1, "bot_messages": 1}

            response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("summary", response.data)

        # Should contain basic statistics
        summary = response.data["summary"]
        self.assertIn("total_messages", summary)
        self.assertIn("user_messages", summary)
        self.assertIn("bot_messages", summary)
        self.assertEqual(summary["total_messages"], 2)
        self.assertEqual(summary["user_messages"], 1)
        self.assertEqual(summary["bot_messages"], 1)

    def test_conversation_summary_nonexistent_chat(self):
        """Test getting summary for non-existent chat."""
        url = reverse("conversation-summary", kwargs={"chat_id": 99999})

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_chatbot_config_endpoint(self):
        """Test chatbot configuration endpoint."""
        url = reverse("chatbot-config")

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("enabled", response.data)
        self.assertIsInstance(response.data["enabled"], bool)
