# Async Chatbot Processing

## Overview

This document describes the asynchronous processing implementation for Azure AI Foundry agent calls, designed to prevent Gunicorn worker timeouts in Kubernetes deployments.

## Problem

When Azure AI agents need to perform external actions (like creating tasks), the synchronous `create_and_process()` call can take much longer than the Gunicorn worker timeout (30-60 seconds). This causes:

1. **Worker timeouts**: Gunicorn kills workers waiting for Azure AI responses
2. **Deadlocks**: If the agent needs to make callbacks to the same application, it can't because workers are blocked
3. **Service unavailability**: The application becomes unresponsive during long agent operations

## Solution

### Async Processing Architecture

The solution implements intelligent request routing:

- **Simple questions**: Processed synchronously for immediate responses
- **Agent actions**: Processed asynchronously to prevent timeouts

### Pattern Detection

Messages are analyzed for patterns that typically trigger agent actions:

```python
trigger_patterns = [
    'create', 'add', 'make', 'new', 'task', 'projet', 'tâche', 'créer', 'ajouter',
    'list', 'show', 'get', 'find', 'voir', 'afficher', 'lister', 'chercher'
]
```

### Processing Flow

#### Synchronous (Simple Questions)
```
User Message → Immediate Azure AI Call → Response (< 25s)
```

#### Asynchronous (Agent Actions)
```
User Message → Immediate "Processing..." Response → Background Thread → Update Message
```

## Implementation Details

### Database Changes

New fields added to `ChatMessage` model:

```python
processing_status = models.CharField(
    max_length=20, 
    choices=[
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ],
    default='completed'
)
azure_run_id = models.CharField(max_length=128, null=True, blank=True)
error_message = models.TextField(null=True, blank=True)
```

### API Changes

#### New Endpoint: Check Processing Status
```
GET /api/chats/{chat_id}/status/
```

Returns processing messages and their current status.

#### Enhanced Message Response
Messages now include processing status:

```json
{
  "id": 123,
  "message": "🤔 I'm processing your request...",
  "is_bot": true,
  "processing_status": "processing",
  "azure_run_id": "run_abc123",
  "error_message": null,
  "created_at": "2025-01-01T12:00:00Z"
}
```

### Timeout Protection

Even synchronous calls now have timeout protection:

- **Polling interval**: 2 seconds
- **Max wait time**: 25 seconds (leaving 5s buffer for response processing)
- **Graceful degradation**: Returns timeout message if Azure AI takes too long

## Frontend Integration

### Polling for Updates

For async messages, the frontend should:

1. Display the initial "processing" message
2. Poll the status endpoint every 2-3 seconds
3. Update the UI when processing completes

```javascript
async function checkMessageStatus(chatId) {
  const response = await fetch(`/api/chats/${chatId}/status/`);
  const data = await response.json();
  
  if (data.has_processing) {
    // Update UI with current status
    updateProcessingMessages(data.messages);
    
    // Continue polling
    setTimeout(() => checkMessageStatus(chatId), 3000);
  }
}
```

### Message State Handling

- **processing**: Show spinner or "thinking" indicator
- **completed**: Display final response
- **failed**: Show error message with retry option

## Configuration

### Environment Variables

```bash
# Chatbot timeouts
CHATBOT_TIMEOUT=30              # Max time for sync operations
CHATBOT_MAX_RETRIES=3           # Retry attempts
CHATBOT_RETRY_DELAY=1.0         # Delay between retries

# Gunicorn settings
GUNICORN_TIMEOUT=60             # Increased from 30s
GUNICORN_WORKERS=2              # Multiple workers for parallel processing
```

### Kubernetes Deployment

Ensure multiple replicas for better handling of concurrent requests:

```yaml
spec:
  replicas: 2  # Minimum for async processing
```

## Monitoring

### Log Messages

Key log messages to monitor:

- `Using async processing for potentially long-running request`
- `Azure AI run timed out after Xs, status: Y`
- `Async processing completed for message`

### Metrics to Track

- Processing time distribution
- Async vs sync request ratio
- Timeout frequency
- Error rates by processing type

## Troubleshooting

### Common Issues

1. **Messages stuck in "processing"**
   - Check background thread errors in logs
   - Verify Azure AI connectivity
   - Check for memory/resource limits

2. **Still getting timeouts**
   - Increase `GUNICORN_TIMEOUT` if needed
   - Check if pattern detection is working correctly
   - Verify async processing is being triggered

3. **Performance issues**
   - Monitor worker count and adjust based on load
   - Consider using proper task queue (Celery) for production
   - Check database performance for status updates

### Debug Commands

```bash
# Check processing messages
kubectl logs -l app=demo-webapp | grep "async processing"

# Monitor worker status
kubectl logs -l app=demo-webapp | grep "WORKER TIMEOUT"

# Check pattern detection
kubectl logs -l app=demo-webapp | grep "Using async processing"
```

## Future Improvements

1. **Proper Task Queue**: Replace threading with Celery/Redis for production
2. **WebSocket Support**: Real-time updates instead of polling
3. **Progress Indicators**: More detailed status updates during processing
4. **Retry Logic**: Automatic retry for failed async operations
5. **Rate Limiting**: Per-user limits for async operations

## Testing

### Unit Tests

```python
# Test pattern detection
def test_message_pattern_detection():
    patterns = ['create', 'task', 'list']
    assert detect_agent_patterns("Create a new task") == True
    assert detect_agent_patterns("What is 2+2?") == False

# Test async processing
def test_async_message_processing():
    # Mock the background processing
    # Verify status transitions: processing → completed
```

### Integration Tests

```bash
# Test with actual messages
curl -X POST /api/chats/1/messages/ \
  -H "Content-Type: application/json" \
  -d '{"message": "Create a new task for Apollo project"}'

# Check status
curl /api/chats/1/status/
```

This implementation provides a robust solution for handling long-running Azure AI operations without blocking Gunicorn workers or causing service disruption.