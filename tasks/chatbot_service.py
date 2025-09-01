"""
Enhanced chatbot service with improved OpenAI integration via Azure AI Foundry.
Implements better error handling, retry logic, conversation management, and security.
"""

import logging
import os
import time
from datetime import datetime
from functools import wraps
from typing import Any, Dict, List, Optional

from django.core.cache import cache

from azure.ai.agents.models import ListSortOrder
from azure.ai.projects import AIProjectClient
from azure.core.exceptions import AzureError, ClientAuthenticationError
from azure.identity import DefaultAzureCredential


class ChatbotError(Exception):
    """Custom exception for chatbot-related errors."""


class RateLimitError(ChatbotError):
    """Exception raised when rate limits are exceeded."""


class AuthenticationError(ChatbotError):
    """Exception raised when authentication fails."""


def rate_limit(calls_per_minute: int = 60):
    """Decorator to implement rate limiting per user/chat."""

    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Get rate limit key (could be user_id, chat_id, or IP)
            rate_limit_key = f"chatbot_rate_limit_{kwargs.get('chat_id', 'default')}"

            # Check current rate limit
            current_calls = cache.get(rate_limit_key, 0)
            if current_calls >= calls_per_minute:
                raise RateLimitError(f"Rate limit exceeded: {calls_per_minute} calls per minute")

            # Increment counter
            cache.set(rate_limit_key, current_calls + 1, 60)  # 60 seconds TTL

            return func(self, *args, **kwargs)

        return wrapper

    return decorator


class EnhancedChatbotService:
    """Enhanced chatbot service with improved Azure AI Foundry integration."""

    def __init__(self):
        self.logger = logging.getLogger("django.chatbot")
        self.endpoint = os.getenv("AZURE_FOUNDRY_ENDPOINT")
        self.agent_id = os.getenv("AZURE_FOUNDRY_AGENT_ID")
        self.max_retries = int(os.getenv("CHATBOT_MAX_RETRIES", "3"))
        self.retry_delay = float(os.getenv("CHATBOT_RETRY_DELAY", "1.0"))
        self.timeout = int(os.getenv("CHATBOT_TIMEOUT", "30"))

        # Validate configuration
        if not self.endpoint or not self.agent_id:
            raise ChatbotError("Azure Foundry not configured: missing endpoint or agent_id")

        # Initialize Azure client with credential
        try:
            self.credential = DefaultAzureCredential()
            self.client = AIProjectClient(credential=self.credential, endpoint=self.endpoint)
            # Test the connection
            self._test_connection()
        except ClientAuthenticationError as e:
            self.logger.error(f"Azure authentication failed: {e}")
            raise AuthenticationError(f"Azure authentication failed: {e}")
        except Exception as e:
            self.logger.error(f"Failed to initialize Azure client: {e}")
            raise ChatbotError(f"Failed to initialize Azure client: {e}")

    def _test_connection(self):
        """Test the Azure AI connection."""
        try:
            agent = self.client.agents.get_agent(self.agent_id)
            self.logger.info(f"Successfully connected to Azure AI agent: {agent.name}")
        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            raise ChatbotError(f"Failed to connect to Azure AI agent: {e}")

    def _retry_on_failure(self, func, *args, **kwargs):
        """Retry logic for handling transient failures."""
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries:
                    delay = self.retry_delay * (2**attempt)  # Exponential backoff
                    self.logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                    time.sleep(delay)
                else:
                    self.logger.error(f"All {self.max_retries + 1} attempts failed. Last error: {e}")
                    break

        raise last_exception

    @rate_limit(calls_per_minute=30)  # Limit to 30 calls per minute per chat
    def send_message(self, message: str, chat, user_context: Optional[Dict] = None) -> str:
        """
        Send a message to the chatbot and get response.

        Args:
            message: User message
            chat: Chat model instance
            user_context: Optional user context for personalization

        Returns:
            Bot response string
        """
        try:
            return self._retry_on_failure(self._send_message_internal, message, chat, user_context)
        except RateLimitError:
            raise
        except AuthenticationError:
            raise
        except Exception as e:
            self.logger.exception(f"Unexpected error in send_message: {e}")
            return f"[Error] Sorry, I encountered an unexpected error: {str(e)}"

    def _send_message_internal(self, message: str, chat, user_context: Optional[Dict] = None) -> str:
        """Internal method to send message with error handling."""
        thread_id = getattr(chat, "azure_thread_id", None)

        try:
            # Get or create thread
            if not thread_id:
                thread = self.client.agents.threads.create()
                chat.azure_thread_id = thread.id
                chat.save()
                thread_id = thread.id
                self.logger.info(f"Created new thread {thread_id} for chat {chat.id}")
            else:
                # Verify thread still exists
                try:
                    thread = self.client.agents.threads.get(thread_id)
                    self.logger.debug(f"Using existing thread {thread_id} for chat {chat.id}")
                except Exception:
                    # Thread doesn't exist, create new one
                    thread = self.client.agents.threads.create()
                    chat.azure_thread_id = thread.id
                    chat.save()
                    thread_id = thread.id
                    self.logger.info(f"Recreated thread {thread_id} for chat {chat.id}")

            # Prepare enhanced instructions with context
            instructions = self._build_instructions(user_context)
            enhanced_message = f"{instructions}\n\n{message}"

            # Send message
            self.client.agents.messages.create(thread_id=thread_id, role="user", content=enhanced_message)
            self.logger.debug(f"Sent user message to thread {thread_id}")

            # Create and process run with timeout
            run = self.client.agents.runs.create_and_process(thread_id=thread_id, agent_id=self.agent_id)

            # Handle run results
            return self._process_run_result(run, thread_id)

        except AzureError as e:
            self.logger.error(f"Azure API error: {e}")
            raise ChatbotError(f"Azure service error: {str(e)}")
        except Exception as e:
            self.logger.exception(f"Unexpected error in _send_message_internal: {e}")
            raise

    def _build_instructions(self, user_context: Optional[Dict] = None) -> str:
        """Build enhanced instructions with user context."""
        base_instructions = (
            "You are a helpful AI assistant. When you answer, use normal text for normal content, "
            "but format tables, bold, and other rich content as Markdown. "
            "Be concise but informative. If you're unsure about something, say so."
        )

        if user_context:
            context_info = []
            if user_context.get("user_name"):
                context_info.append(f"User name: {user_context['user_name']}")
            if user_context.get("preferences"):
                context_info.append(f"User preferences: {user_context['preferences']}")

            if context_info:
                base_instructions += f"\n\nUser context: {', '.join(context_info)}"

        return base_instructions

    def _process_run_result(self, run, thread_id: str) -> str:
        """Process the run result and extract response."""
        if run.status == "failed":
            error_msg = getattr(run, "last_error", "Unknown error")
            self.logger.error(f"Azure run failed: {error_msg}")
            return "[Service Error] I'm having trouble processing your request. Please try again later."

        if run.status == "expired":
            self.logger.warning(f"Azure run expired for thread {thread_id}")
            return "[Timeout] Your request took too long to process. Please try a simpler question."

        if run.status != "completed":
            self.logger.warning(f"Azure run status: {run.status}")
            return f"[Status: {run.status}] I'm still processing your request. Please wait a moment."

        # Get messages and extract response
        try:
            messages = self.client.agents.messages.list(
                thread_id=thread_id, order=ListSortOrder.DESCENDING, limit=10  # Only get recent messages
            )

            # Find the latest assistant message
            for msg in messages:
                if msg.role == "assistant" and msg.text_messages:
                    response = msg.text_messages[-1].text.value
                    self.logger.debug(f"Bot response: {response[:100]}...")
                    return response

            self.logger.warning("No assistant response found in messages")
            return "[No Response] I didn't generate a response. Please try rephrasing your question."

        except Exception as e:
            self.logger.error(f"Error retrieving messages: {e}")
            return "[Error] I had trouble retrieving my response. Please try again."

    def get_conversation_summary(self, thread_id: str, limit: int = 10) -> List[Dict]:
        """Get conversation summary for a thread."""
        try:
            messages = self.client.agents.messages.list(thread_id=thread_id, order=ListSortOrder.ASCENDING, limit=limit)

            summary = []
            for msg in messages:
                if msg.text_messages:
                    summary.append(
                        {"role": msg.role, "content": msg.text_messages[-1].text.value, "timestamp": msg.created_at}
                    )

            return summary
        except Exception as e:
            self.logger.error(f"Error getting conversation summary: {e}")
            return []

    def clear_conversation(self, chat) -> bool:
        """Clear conversation by creating a new thread."""
        try:
            thread = self.client.agents.threads.create()
            chat.azure_thread_id = thread.id
            chat.save()
            self.logger.info(f"Cleared conversation for chat {chat.id}, new thread: {thread.id}")
            return True
        except Exception as e:
            self.logger.error(f"Error clearing conversation: {e}")
            return False

    def get_health_status(self) -> Dict[str, Any]:
        """Get service health status."""
        status = {
            "healthy": False,
            "endpoint": self.endpoint,
            "agent_id": self.agent_id,
            "timestamp": datetime.now().isoformat(),
            "errors": [],
        }

        try:
            # Test connection
            agent = self.client.agents.get_agent(self.agent_id)
            status["healthy"] = True
            status["agent_name"] = getattr(agent, "name", "Unknown")
            status["agent_model"] = getattr(agent, "model", "Unknown")
        except Exception as e:
            status["errors"].append(str(e))

        return status


# Global service instance
_chatbot_service = None


def get_chatbot_service() -> EnhancedChatbotService:
    """Get global chatbot service instance."""
    global _chatbot_service
    if _chatbot_service is None:
        _chatbot_service = EnhancedChatbotService()
    return _chatbot_service


def is_chatbot_enabled() -> bool:
    """Check if chatbot is properly configured and enabled."""
    required_envs = [
        "AZURE_FOUNDRY_ENDPOINT",
        "AZURE_FOUNDRY_AGENT_ID",
        "AZURE_CLIENT_ID",
        "AZURE_TENANT_ID",
        "AZURE_CLIENT_SECRET",
    ]
    return all(os.getenv(var) is not None for var in required_envs)
