let currentModel = '';

// Send message when Enter is pressed
document.getElementById('chat-input').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        sendMessage();
    }
});

async function sendMessage() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    
    if (!message) return;
    
    // Clear input
    input.value = '';
    
    // Add user message to chat
    addMessage(message, 'user');
    
    // Show loading indicator
    const { messageId, messageElement } = addMessage('', 'assistant', true);
    // Store raw markdown text for streaming
    messageElement.dataset.rawText = '';
    
    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                query: message,
                model: currentModel,
                stream: true
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.error || 'Server error');
        }
        
        // Read the streaming response
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let hasReceivedData = false;
        
        while (true) {
            const { done, value } = await reader.read();
            
            if (done) {
                // If we never received any data, there might be an issue
                if (!hasReceivedData) {
                    const currentContent = messageElement.dataset.rawText || messageElement.textContent || '';
                    if (!currentContent.trim()) {
                        messageElement.textContent = 'Error: No response received from server';
                        // Remove loading spinner if still present
                        const loadingSpinner = messageElement.querySelector('.loading');
                        if (loadingSpinner) {
                            loadingSpinner.remove();
                        }
                    }
                }
                break;
            }
            
            // Decode the chunk
            buffer += decoder.decode(value, { stream: true });
            
            // Process complete SSE messages (lines ending with \n\n)
            const lines = buffer.split('\n\n');
            buffer = lines.pop() || ''; // Keep incomplete line in buffer
            
            for (const line of lines) {
                if (line.trim() && line.startsWith('data: ')) {
                    try {
                        const jsonStr = line.slice(6); // Remove 'data: ' prefix
                        const data = JSON.parse(jsonStr);
                        hasReceivedData = true;
                        
                        // Remove loading spinner on first data
                        if (hasReceivedData) {
                            const loadingSpinner = messageElement.querySelector('.loading');
                            if (loadingSpinner) {
                                loadingSpinner.remove();
                            }
                        }
                        
                        if (data.error) {
                            // Remove loading spinner if present
                            const loadingSpinner = messageElement.querySelector('.loading');
                            if (loadingSpinner) {
                                loadingSpinner.remove();
                            }
                            messageElement.textContent = 'Error: ' + data.error;
                            console.error('Server error:', data.error);
                            break;
                        }
                        
                        if (data.chunk !== undefined && data.chunk !== null && data.chunk !== '') {
                            // Remove loading spinner if present
                            const loadingSpinner = messageElement.querySelector('.loading');
                            if (loadingSpinner) {
                                loadingSpinner.remove();
                            }
                            
                            // Accumulate raw markdown text
                            const currentText = messageElement.dataset.rawText || '';
                            const newText = currentText + data.chunk;
                            messageElement.dataset.rawText = newText;
                            
                            // Render markdown if marked is available
                            if (typeof marked !== 'undefined') {
                                messageElement.innerHTML = marked.parse(newText);
                            } else {
                                messageElement.textContent = newText;
                            }
                            
                            // Auto-scroll to bottom
                            const messagesContainer = document.getElementById('chat-messages');
                            messagesContainer.scrollTop = messagesContainer.scrollHeight;
                        }
                        
                        if (data.done) {
                            // Update current model if it changed
                            if (data.model && data.model !== currentModel) {
                                currentModel = data.model;
                                updateModelDisplay();
                            }
                            break;
                        }
                    } catch (e) {
                        console.error('Error parsing SSE data:', e, 'Line:', line);
                    }
                }
            }
        }
    } catch (error) {
        removeMessage(messageId);
        addMessage('Error: Could not connect to server', 'assistant');
        console.error('Error:', error);
    }
}

async function switchModel(modelName) {
    if (modelName === currentModel) return;
    
    try {
        const response = await fetch('/switch_model', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                model: modelName
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            currentModel = data.model;
            updateModelDisplay();
            addMessage(`Switched to model: ${data.model}`, 'system');
        } else {
            alert('Error: ' + (data.error || 'Could not switch model'));
        }
    } catch (error) {
        alert('Error: Could not switch model');
        console.error('Error:', error);
    }
}

function updateModelDisplay() {
    // Update current model name
    document.getElementById('current-model-name').textContent = currentModel.charAt(0).toUpperCase() + currentModel.slice(1);
    
    // Update active button
    document.querySelectorAll('.model-btn').forEach(btn => {
        if (btn.dataset.model === currentModel) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });
}

function addMessage(text, type, isLoading = false) {
    const messagesContainer = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    // Use a valid ID format (replace dots with dashes)
    const messageId = 'msg-' + Date.now() + '-' + Math.random().toString().replace('.', '-');
    messageDiv.id = messageId;
    messageDiv.className = `message ${type}`;
    
    // Use div for content to support markdown HTML rendering
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    if (text) {
        // Store raw text for markdown rendering
        if (type === 'assistant') {
            contentDiv.dataset.rawText = text;
        }
        
        // Render markdown for assistant messages, plain text for user messages
        if (type === 'assistant' && typeof marked !== 'undefined') {
            contentDiv.innerHTML = marked.parse(text);
        } else {
            contentDiv.textContent = text;
        }
    } else {
        // Initialize empty raw text for streaming
        if (type === 'assistant') {
            contentDiv.dataset.rawText = '';
        }
    }
    
    if (isLoading) {
        const loading = document.createElement('span');
        loading.className = 'loading';
        contentDiv.appendChild(loading);
    }
    
    messageDiv.appendChild(contentDiv);
    messagesContainer.appendChild(messageDiv);
    
    // Scroll to bottom
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    
    // Return both ID and the content element for easy access
    return { messageId: messageId, messageElement: contentDiv };
}

function removeMessage(messageId) {
    const message = document.getElementById(messageId);
    if (message) {
        message.remove();
    }
}

// Initialize: Get current model on page load
window.addEventListener('load', async function() {
    // Use initial model from server if available
    if (window.initialModel) {
        currentModel = window.initialModel;
        updateModelDisplay();
    } else {
        // Fallback: fetch from API
        try {
            const response = await fetch('/current_model');
            const data = await response.json();
            if (data.model) {
                currentModel = data.model;
                updateModelDisplay();
            }
        } catch (error) {
            console.error('Error fetching current model:', error);
        }
    }
});

