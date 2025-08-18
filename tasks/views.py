from django.conf import settings
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy
import logging
from datetime import datetime
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json
from .models import Chat, ChatMessage
from .serializers import ChatSerializer, ChatMessageSerializer
from .chatbot_service import (
    get_chatbot_service, 
    is_chatbot_enabled, 
    ChatbotError, 
    RateLimitError, 
    AuthenticationError
)
import os
from dotenv import load_dotenv

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

@login_required
def chatbot_page(request):
    """Chatbot page - requires user authentication."""
    return render(request, 'tasks/chatbot.html')

class ChatListCreateView(generics.ListCreateAPIView):
    queryset = Chat.objects.all().order_by('-created_at')
    serializer_class = ChatSerializer
    permission_classes = [IsAuthenticated]

class ChatDetailView(generics.RetrieveDestroyAPIView):
    queryset = Chat.objects.all()
    serializer_class = ChatSerializer
    permission_classes = [IsAuthenticated]

class ChatMessageCreateView(APIView):
    """Enhanced chat message creation with improved error handling and user context."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, chat_id):
        logger = logging.getLogger("django.chat")
        
        try:
            # Get chat instance
            try:
                chat = Chat.objects.get(id=chat_id)
            except Chat.DoesNotExist:
                logger.warning(f"Chat not found: {chat_id}")
                return Response({'error': 'Chat not found'}, status=404)
            
            # Validate message
            user_message = request.data.get('message', '').strip()
            if not user_message:
                logger.warning(f"No message provided for chat_id={chat_id}")
                return Response({'error': 'Message is required'}, status=400)
            
            if len(user_message) > 4000:  # Reasonable message length limit
                logger.warning(f"Message too long for chat_id={chat_id}: {len(user_message)} chars")
                return Response({'error': 'Message is too long (max 4000 characters)'}, status=400)
            
            logger.info(f"Received message for chat_id={chat_id}: {user_message[:100]}...")
            
            # Check if chatbot is enabled
            if not is_chatbot_enabled():
                logger.error("Chatbot is not properly configured")
                return Response({'error': 'Chatbot service is not available'}, status=503)
            
            # Save user message
            user_msg_obj = ChatMessage.objects.create(
                chat=chat, 
                message=user_message, 
                is_bot=False
            )
            logger.debug(f"User message saved: {user_msg_obj.id}")
            
            # Prepare user context for personalization
            user_context = self._get_user_context(request)
            
            # Get chatbot response
            try:
                chatbot_service = get_chatbot_service()
                bot_response = chatbot_service.send_message(
                    message=user_message,
                    chat=chat,
                    user_context=user_context
                )
                
                # Save bot response
                bot_msg_obj = ChatMessage.objects.create(
                    chat=chat, 
                    message=bot_response, 
                    is_bot=True
                )
                logger.debug(f"Bot message saved: {bot_msg_obj.id}")
                
                # Return both messages
                return Response(ChatMessageSerializer([user_msg_obj, bot_msg_obj], many=True).data)
                
            except RateLimitError as e:
                logger.warning(f"Rate limit exceeded for chat_id={chat_id}: {e}")
                return Response({
                    'error': 'Rate limit exceeded. Please wait before sending another message.',
                    'retry_after': 60
                }, status=429)
                
            except AuthenticationError as e:
                logger.error(f"Authentication error for chat_id={chat_id}: {e}")
                return Response({
                    'error': 'Chatbot authentication failed. Please contact support.'
                }, status=500)
                
            except ChatbotError as e:
                logger.error(f"Chatbot error for chat_id={chat_id}: {e}")
                # Save error message for user feedback
                error_response = f"I'm experiencing technical difficulties. Error: {str(e)}"
                bot_msg_obj = ChatMessage.objects.create(
                    chat=chat, 
                    message=error_response, 
                    is_bot=True
                )
                return Response(ChatMessageSerializer([user_msg_obj, bot_msg_obj], many=True).data)
                
        except Exception as e:
            logger.exception(f"Unexpected error in ChatMessageCreateView: {e}")
            return Response({'error': 'Internal server error'}, status=500)
    
    def _get_user_context(self, request) -> dict:
        """Extract user context for personalization."""
        context = {}
        
        # Add user information if authenticated
        if hasattr(request, 'user') and request.user.is_authenticated:
            context['user_name'] = request.user.get_full_name() or request.user.username
            context['user_id'] = request.user.id
        
        # Add any user preferences (could be extended)
        # context['preferences'] = request.session.get('chat_preferences', {})
        
        return context

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def chatbot_config(request):
    """Get chatbot configuration status with enhanced health check."""
    try:
        config = {
            'enabled': is_chatbot_enabled(),
            'status': 'unknown'
        }
        
        if config['enabled']:
            try:
                # Get health status from service
                chatbot_service = get_chatbot_service()
                health_status = chatbot_service.get_health_status()
                config.update({
                    'status': 'healthy' if health_status['healthy'] else 'unhealthy',
                    'agent_name': health_status.get('agent_name'),
                    'last_check': health_status.get('timestamp'),
                    'errors': health_status.get('errors', [])
                })
            except Exception as e:
                config.update({
                    'status': 'error',
                    'error': str(e)
                })
        else:
            config['status'] = 'disabled'
            
        return Response(config)
        
    except Exception as e:
        return Response({
            'enabled': False,
            'status': 'error',
            'error': f'Configuration check failed: {str(e)}'
        }, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def clear_conversation(request, chat_id):
    """Clear conversation history for a chat."""
    try:
        chat = Chat.objects.get(id=chat_id)
        
        if is_chatbot_enabled():
            chatbot_service = get_chatbot_service()
            success = chatbot_service.clear_conversation(chat)
            
            if success:
                # Also clear local message history if desired
                # ChatMessage.objects.filter(chat=chat).delete()
                return Response({'success': True, 'message': 'Conversation cleared'})
            else:
                return Response({'success': False, 'error': 'Failed to clear conversation'}, status=500)
        else:
            return Response({'success': False, 'error': 'Chatbot not available'}, status=503)
            
    except Chat.DoesNotExist:
        return Response({'error': 'Chat not found'}, status=404)
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def conversation_summary(request, chat_id):
    """Get conversation summary from Azure thread."""
    try:
        chat = Chat.objects.get(id=chat_id)
        
        if not chat.azure_thread_id:
            return Response({'summary': []})
        
        if is_chatbot_enabled():
            chatbot_service = get_chatbot_service()
            summary = chatbot_service.get_conversation_summary(
                chat.azure_thread_id,
                limit=int(request.GET.get('limit', 20))
            )
            return Response({'summary': summary})
        else:
            return Response({'error': 'Chatbot not available'}, status=503)
            
    except Chat.DoesNotExist:
        return Response({'error': 'Chat not found'}, status=404)
    except Exception as e:
        return Response({'error': str(e)}, status=500)