import os

from django.core.management.base import BaseCommand

from tasks.chatbot_service import (
    AuthenticationError,
    ChatbotError,
    RateLimitError,
    get_chatbot_service,
    is_chatbot_enabled,
)
from tasks.models import Chat


class Command(BaseCommand):
    help = "Test the enhanced chatbot service functionality"

    def add_arguments(self, parser):
        parser.add_argument(
            "--test-message",
            type=str,
            default="Hello, please create a test task for project Apollo.",
            help="Test message to send to the chatbot",
        )
        parser.add_argument("--create-chat", action="store_true", help="Create a new test chat")
        parser.add_argument("--chat-id", type=int, help="Use existing chat ID for testing")

    def handle(self, *args, **options):
        self.stdout.write("🤖 Testing Enhanced Chatbot Service...\n")

        # Check if chatbot is enabled
        self.stdout.write("1. Checking chatbot configuration...")
        if not is_chatbot_enabled():
            self.stdout.write(self.style.ERROR("❌ Chatbot is not enabled. Missing environment variables:"))
            required_envs = [
                "AZURE_FOUNDRY_ENDPOINT",
                "AZURE_FOUNDRY_AGENT_ID",
                "AZURE_CLIENT_ID",
                "AZURE_TENANT_ID",
                "AZURE_CLIENT_SECRET",
            ]
            for env in required_envs:
                status = "✅" if os.getenv(env) else "❌"
                self.stdout.write(f"   {status} {env}")
            return

        self.stdout.write(self.style.SUCCESS("✅ Chatbot is enabled"))

        # Initialize service
        self.stdout.write("\n2. Initializing chatbot service...")
        try:
            service = get_chatbot_service()
            self.stdout.write(self.style.SUCCESS("✅ Service initialized successfully"))
        except AuthenticationError as e:
            self.stdout.write(self.style.ERROR(f"❌ Authentication failed: {e}"))
            return
        except ChatbotError as e:
            self.stdout.write(self.style.ERROR(f"❌ Service initialization failed: {e}"))
            return

        # Get health status
        self.stdout.write("\n3. Checking service health...")
        health = service.get_health_status()
        if health["healthy"]:
            self.stdout.write(self.style.SUCCESS("✅ Service is healthy"))
            if health.get("agent_name"):
                self.stdout.write(f'   Agent: {health["agent_name"]}')
            if health.get("agent_model"):
                self.stdout.write(f'   Model: {health["agent_model"]}')
        else:
            self.stdout.write(self.style.ERROR("❌ Service is unhealthy"))
            for error in health.get("errors", []):
                self.stdout.write(f"   Error: {error}")
            return

        # Get or create chat
        self.stdout.write("\n4. Setting up test chat...")
        if options["chat_id"]:
            try:
                chat = Chat.objects.get(id=options["chat_id"])
                self.stdout.write(f"✅ Using existing chat {chat.id}")
            except Chat.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'❌ Chat {options["chat_id"]} not found'))
                return
        elif options["create_chat"]:
            chat = Chat.objects.create(title="Test Chat from Management Command")
            self.stdout.write(f"✅ Created new chat {chat.id}")
        else:
            # Use existing chat or create one
            chat = Chat.objects.filter(title__icontains="test").first()
            if not chat:
                chat = Chat.objects.create(title="Test Chat from Management Command")
                self.stdout.write(f"✅ Created new chat {chat.id}")
            else:
                self.stdout.write(f"✅ Using existing test chat {chat.id}")

        # Test message sending
        self.stdout.write("\n5. Testing message sending...")
        test_message = options["test_message"]
        self.stdout.write(f'Sending: "{test_message}"')

        try:
            # Test with user context
            user_context = {"user_name": "Test User", "preferences": "concise responses"}

            response = service.send_message(message=test_message, chat=chat, user_context=user_context)

            self.stdout.write(self.style.SUCCESS("✅ Message sent successfully!"))
            self.stdout.write("\n📝 Bot Response:")
            self.stdout.write("-" * 50)
            self.stdout.write(response)
            self.stdout.write("-" * 50)

        except RateLimitError as e:
            self.stdout.write(self.style.WARNING(f"⚠️  Rate limit hit: {e}"))
        except ChatbotError as e:
            self.stdout.write(self.style.ERROR(f"❌ Chatbot error: {e}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Unexpected error: {e}"))
            return

        # Test conversation summary
        self.stdout.write("\n6. Testing conversation summary...")
        if chat.azure_thread_id:
            try:
                summary = service.get_conversation_summary(chat.azure_thread_id, limit=5)
                self.stdout.write(f"✅ Retrieved {len(summary)} messages from conversation")
                for i, msg in enumerate(summary[-3:], 1):  # Show last 3 messages
                    role = "🤖" if msg["role"] == "assistant" else "👤"
                    content = msg["content"][:100] + "..." if len(msg["content"]) > 100 else msg["content"]
                    self.stdout.write(f"   {i}. {role} {content}")
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"⚠️  Could not get summary: {e}"))
        else:
            self.stdout.write("⚠️  No Azure thread ID available for summary")

        # Test conversation clearing
        if self.confirm_action("\n7. Test conversation clearing? (y/N): "):
            try:
                success = service.clear_conversation(chat)
                if success:
                    self.stdout.write(self.style.SUCCESS("✅ Conversation cleared successfully"))
                else:
                    self.stdout.write(self.style.ERROR("❌ Failed to clear conversation"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Error clearing conversation: {e}"))

        self.stdout.write("\n🎉 Chatbot service testing completed!")

    def confirm_action(self, message):
        """Ask for user confirmation."""
        try:
            response = input(message)  # nosec B322
            return response.lower() in ["y", "yes"]
        except (EOFError, KeyboardInterrupt):
            return False
