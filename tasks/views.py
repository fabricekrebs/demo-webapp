from django.conf import settings
from django.shortcuts import render
import logging
from datetime import datetime
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import mixins
from .models import Chat, ChatMessage
from .serializers import ChatSerializer, ChatMessageSerializer
import requests
import os
from dotenv import load_dotenv
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.agents.models import ListSortOrder
from rest_framework.decorators import api_view

# Load environment variables from .env file
load_dotenv()

def task_list(request):
    if settings.BACKEND_SAME_HOST == 'True':
        scheme = 'https' if request.is_secure() else 'http'
        
        backendAddress = f"{scheme}://{request.get_host()}"
    else:
        backendAddress = settings.BACKEND_ADDRESS

    context = {
        'backend_address': backendAddress,
        'db_host': settings.DB_HOST,
    }

    return render(request, 'tasks/task_list.html', context)

def project_list(request):
    if settings.BACKEND_SAME_HOST == 'True':
        scheme = 'https' if request.is_secure() else 'http'
        backendAddress = f"{scheme}://{request.get_host()}"
    else:
        backendAddress = settings.BACKEND_ADDRESS
    context = {
        'backend_address': backendAddress,
        'db_host': settings.DB_HOST,
    }
    return render(request, 'tasks/project_list.html', context)

def logger_view(request):
    logger = logging.getLogger("django")
    logger.info(f"Logger is working! Current time: {datetime.now().isoformat()}")
    return render(request, 'tasks/logger.html')

def chatbot_page(request):
    return render(request, 'tasks/chatbot.html')

class ChatListCreateView(generics.ListCreateAPIView):
    queryset = Chat.objects.all().order_by('-created_at')
    serializer_class = ChatSerializer

class ChatDetailView(generics.RetrieveDestroyAPIView):
    queryset = Chat.objects.all()
    serializer_class = ChatSerializer

class ChatMessageCreateView(APIView):
    def post(self, request, chat_id):
        chat = Chat.objects.get(id=chat_id)
        user_message = request.data.get('message')
        if not user_message:
            return Response({'error': 'Message required'}, status=400)
        user_msg_obj = ChatMessage.objects.create(chat=chat, message=user_message, is_bot=False)
        azure_response = self.ask_azure_foundry(user_message, chat)
        bot_msg_obj = ChatMessage.objects.create(chat=chat, message=azure_response, is_bot=True)
        return Response(ChatMessageSerializer([user_msg_obj, bot_msg_obj], many=True).data)

    def ask_azure_foundry(self, message, chat):
        # Azure AI Foundry integration using SDK
        try:
            endpoint = os.getenv('AZURE_FOUNDRY_ENDPOINT')
            agent_id = os.getenv('AZURE_FOUNDRY_AGENT_ID')
            thread_id = getattr(chat, 'azure_thread_id', None)
            if not endpoint or not agent_id:
                return "[Azure Foundry not configured]"

            # Initialize Azure AI Project Client
            project = AIProjectClient(
                credential=DefaultAzureCredential(),
                endpoint=endpoint
            )

            # Get agent
            agent = project.agents.get_agent(agent_id)

            # If no thread exists for this chat, create one and save it
            if not thread_id:
                thread = project.agents.threads.create()
                chat.azure_thread_id = thread.id
                chat.save()
            else:
                thread = project.agents.threads.get(thread_id)

            # Send user message with hybrid HTML formatting instruction
            instructions = (
                "When you answer, use normal text for normal content, "
                "but format tables, bold, and other rich content as Markdown."
            )
            project.agents.messages.create(
                thread_id=thread.id,
                role="user",
                content=f"{instructions}\n\n{message}"
            )

            # Run agent
            run = project.agents.runs.create_and_process(
                thread_id=thread.id,
                agent_id=agent.id
            )

            if run.status == "failed":
                return f"[Azure run failed] {getattr(run, 'last_error', 'Unknown error')}"
            else:
                # Get all messages in the thread, return the last bot message
                messages = project.agents.messages.list(thread_id=thread.id, order=ListSortOrder.ASCENDING)
                bot_reply = None
                for msg in messages:
                    if msg.role == "assistant" and msg.text_messages:
                        bot_reply = msg.text_messages[-1].text.value
                return bot_reply or "[No response from assistant]"
        except Exception as e:
            return f"[Azure error: Exception] {str(e)}"

@api_view(['GET'])
def chatbot_config(request):
    endpoint = os.getenv('AZURE_FOUNDRY_ENDPOINT')
    key = os.getenv('AZURE_FOUNDRY_KEY')
    agent_id = os.getenv('AZURE_FOUNDRY_AGENT_ID')
    enabled = bool(endpoint and endpoint.strip() and key and key.strip() and agent_id and agent_id.strip())
    return Response({'enabled': enabled})