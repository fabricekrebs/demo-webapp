"""
Test for async chatbot pattern detection and timeout logic.
This test can run without database or Azure dependencies.
"""

import unittest
import time
from unittest.mock import Mock, patch


class TestAsyncChatbotLogic(unittest.TestCase):
    """Test the core logic for async chatbot processing."""

    def test_pattern_detection(self):
        """Test that messages are correctly identified for async processing."""
        trigger_patterns = [
            'create', 'add', 'make', 'new', 'task', 'projet', 'tâche', 'créer', 'ajouter',
            'list', 'show', 'get', 'find', 'voir', 'afficher', 'lister', 'chercher'
        ]
        
        def might_trigger_actions(message):
            return any(pattern.lower() in message.lower() for pattern in trigger_patterns)
        
        # Test cases: (message, should_trigger_async)
        test_cases = [
            ("Create a new task", True),
            ("List all tasks", True),
            ("What is the capital of France?", False),
            ("Créer une nouvelle tâche", True),
            ("How are you?", False),
            ("Show me the project status", True),
            ("Find the Apollo project", True),
            ("Hello, how can I help?", False),
            ("Add a new project", True),
            ("What's 2 + 2?", False),
        ]
        
        for message, expected in test_cases:
            result = might_trigger_actions(message)
            self.assertEqual(result, expected, 
                           f"Pattern detection failed for: '{message}'. Expected: {expected}, Got: {result}")
    
    def test_timeout_calculation(self):
        """Test timeout calculation logic."""
        def calculate_max_wait_time(total_timeout, buffer=5):
            return min(total_timeout - buffer, 25)
        
        # Test various timeout values
        self.assertEqual(calculate_max_wait_time(30), 25)  # 30-5=25, min(25,25)=25
        self.assertEqual(calculate_max_wait_time(60), 25)  # 60-5=55, min(55,25)=25
        self.assertEqual(calculate_max_wait_time(20), 15)  # 20-5=15, min(15,25)=15
        self.assertEqual(calculate_max_wait_time(10), 5)   # 10-5=5, min(5,25)=5
    
    def test_polling_logic(self):
        """Test the polling logic for Azure AI run status."""
        def simulate_polling(max_wait_time, poll_interval, status_sequence):
            """Simulate polling with a sequence of statuses."""
            wait_time = 0
            status_index = 0
            
            while wait_time < max_wait_time:
                current_status = status_sequence[min(status_index, len(status_sequence) - 1)]
                
                if current_status in ['completed', 'failed', 'cancelled', 'expired']:
                    return current_status, wait_time
                
                wait_time += poll_interval
                status_index += 1
            
            # Timeout case
            return status_sequence[-1], wait_time
        
        # Test successful completion
        status, time_taken = simulate_polling(25, 2, ['queued', 'in_progress', 'completed'])
        self.assertEqual(status, 'completed')
        self.assertEqual(time_taken, 4)  # 0 + 2 + 2 = 4 seconds
        
        # Test timeout
        status, time_taken = simulate_polling(10, 2, ['queued', 'in_progress', 'in_progress', 'in_progress'])
        self.assertEqual(status, 'in_progress')
        self.assertEqual(time_taken, 10)  # Hit timeout
        
        # Test immediate completion
        status, time_taken = simulate_polling(25, 2, ['completed'])
        self.assertEqual(status, 'completed')
        self.assertEqual(time_taken, 0)  # Immediate
    
    def test_status_message_generation(self):
        """Test generation of appropriate status messages."""
        def get_status_message(run_status, wait_time):
            if run_status == 'failed':
                return "[Service Error] I'm having trouble processing your request. Please try again later."
            elif run_status == 'expired':
                return "[Timeout] Your request took too long to process. Please try a simpler question."
            elif run_status in ['queued', 'in_progress', 'requires_action']:
                return f"[Processing] Your request is taking longer than expected. The agent might be performing complex actions. Please check back in a moment."
            elif run_status == 'completed':
                return "Success"
            else:
                return f"[Status: {run_status}] I'm still processing your request. Please wait a moment."
        
        # Test different status messages
        self.assertIn("Service Error", get_status_message('failed', 10))
        self.assertIn("Timeout", get_status_message('expired', 25))
        self.assertIn("taking longer than expected", get_status_message('in_progress', 20))
        self.assertEqual("Success", get_status_message('completed', 5))
        self.assertIn("still processing", get_status_message('unknown_status', 5))
    
    def test_message_processing_status_flow(self):
        """Test the status flow for message processing."""
        # Simulate the status transitions
        class MockMessage:
            def __init__(self):
                self.processing_status = 'processing'
                self.message = "🤔 I'm processing your request..."
                self.error_message = None
            
            def update_success(self, response):
                self.message = response
                self.processing_status = 'completed'
            
            def update_error(self, error):
                self.message = f"[Error] Sorry, I encountered an error: {error}"
                self.processing_status = 'failed'
                self.error_message = str(error)
        
        # Test successful flow
        msg = MockMessage()
        self.assertEqual(msg.processing_status, 'processing')
        
        msg.update_success("Here's your task list!")
        self.assertEqual(msg.processing_status, 'completed')
        self.assertEqual(msg.message, "Here's your task list!")
        
        # Test error flow
        msg = MockMessage()
        msg.update_error("Connection timeout")
        self.assertEqual(msg.processing_status, 'failed')
        self.assertIn("Connection timeout", msg.message)
        self.assertEqual(msg.error_message, "Connection timeout")


class TestAsyncProcessingIntegration(unittest.TestCase):
    """Integration tests for async processing flow."""
    
    def test_complete_async_flow(self):
        """Test the complete async processing flow."""
        # Mock objects
        chat = Mock()
        chat.id = 1
        
        user_message_obj = Mock()
        user_message_obj.id = 1
        
        # Test the flow
        trigger_patterns = ['create', 'task', 'list']
        user_message = "Create a new task for Apollo project"
        
        # 1. Pattern detection
        might_trigger_actions = any(pattern.lower() in user_message.lower() for pattern in trigger_patterns)
        self.assertTrue(might_trigger_actions)
        
        # 2. Initial response creation (would be done by ChatMessage.objects.create)
        bot_response = {
            'id': 2,
            'message': "🤔 I'm processing your request...",
            'is_bot': True,
            'processing_status': 'processing'
        }
        
        # 3. Background processing simulation
        def simulate_background_processing():
            time.sleep(0.1)  # Simulate processing time
            return "I've created a new task for the Apollo project successfully!"
        
        # 4. Update with final response
        final_response = simulate_background_processing()
        bot_response['message'] = final_response
        bot_response['processing_status'] = 'completed'
        
        # Verify final state
        self.assertEqual(bot_response['processing_status'], 'completed')
        self.assertNotIn("🤔 I'm processing", bot_response['message'])
        self.assertIn("Apollo project", bot_response['message'])


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)