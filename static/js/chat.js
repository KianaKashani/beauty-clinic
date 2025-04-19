document.addEventListener('DOMContentLoaded', function() {
    const chatButton = document.querySelector('.chat-button');
    const chatContainer = document.querySelector('.chat-container');
    const chatClose = document.querySelector('.chat-close');
    const chatMessages = document.querySelector('.chat-messages');
    const chatInput = document.querySelector('.chat-input');
    const chatSend = document.querySelector('.chat-send');
    
    // Check if chat elements exist
    if (!chatButton || !chatContainer || !chatMessages || !chatInput || !chatSend) {
        return;
    }
    
    // Toggle chat widget
    chatButton.addEventListener('click', function() {
        chatContainer.style.display = 'flex';
        chatButton.style.display = 'none';
        chatInput.focus();
        
        // Scroll to bottom of messages
        chatMessages.scrollTop = chatMessages.scrollHeight;
    });
    
    chatClose.addEventListener('click', function() {
        chatContainer.style.display = 'none';
        chatButton.style.display = 'flex';
    });
    
    // Initial welcome message
    addBotMessage('سلام! من مشاور هوش مصنوعی کلینیک زیبایی هستم. چطور می‌توانم به شما کمک کنم؟');
    
    // Send message on button click
    chatSend.addEventListener('click', sendMessage);
    
    // Send message on Enter key
    chatInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            sendMessage();
        }
    });
    
    // Function to send message
    function sendMessage() {
        const message = chatInput.value.trim();
        
        if (message === '') {
            return;
        }
        
        // Add user message to chat
        addUserMessage(message);
        
        // Clear input
        chatInput.value = '';
        
        // Show typing indicator
        addTypingIndicator();
        
        // Send message to backend
        fetch('/ai_consultation', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams({
                'question': message
            })
        })
        .then(response => response.json())
        .then(data => {
            // Remove typing indicator
            removeTypingIndicator();
            
            if (data.error) {
                addBotMessage('متأسفانه مشکلی پیش آمد. لطفاً دوباره تلاش کنید.');
            } else {
                addBotMessage(data.response);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            removeTypingIndicator();
            addBotMessage('متأسفانه مشکلی در ارتباط با سرور پیش آمد. لطفاً دوباره تلاش کنید.');
        });
    }
    
    // Add user message to chat
    function addUserMessage(message) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', 'user-message');
        messageElement.textContent = message;
        
        chatMessages.appendChild(messageElement);
        
        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // Add bot message to chat
    function addBotMessage(message) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', 'bot-message');
        messageElement.innerHTML = message.replace(/\n/g, '<br>');
        
        chatMessages.appendChild(messageElement);
        
        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // Add typing indicator
    function addTypingIndicator() {
        const typingElement = document.createElement('div');
        typingElement.classList.add('message', 'bot-message', 'typing-indicator');
        typingElement.innerHTML = '<span></span><span></span><span></span>';
        typingElement.id = 'typing-indicator';
        
        chatMessages.appendChild(typingElement);
        
        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // Remove typing indicator
    function removeTypingIndicator() {
        const typingElement = document.getElementById('typing-indicator');
        if (typingElement) {
            typingElement.remove();
        }
    }
});
