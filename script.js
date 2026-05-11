document.addEventListener('DOMContentLoaded', () => {
  // Initialize Lucide icons
  lucide.createIcons();

  // DOM Elements
  const chatHistory = document.getElementById('chatHistory');
  const chatForm = document.getElementById('chatForm');
  const userInput = document.getElementById('userInput');
  const sendBtn = document.getElementById('sendBtn');
  const typingIndicator = document.getElementById('typingIndicator');
  // Clear chat functionality
  document.querySelector('.header-action-btn').addEventListener('click', () => {
    if(confirm('Are you sure you want to clear the chat history?')) {
      chatHistory.innerHTML = '';
    }
  });

  // Event Listeners
  chatForm.addEventListener('submit', handleSend);
  userInput.addEventListener('input', toggleSendButton);
  


  function toggleSendButton() {
    sendBtn.disabled = userInput.value.trim() === '';
  }

  function handleSend(e) {
    e.preventDefault();
    const message = userInput.value.trim();
    if (message) {
      processMessage(message);
      userInput.value = '';
      toggleSendButton();
    }
  }

  async function processMessage(text) {
    // 1. Add User Message
    addUserMessage(text);
    
    // 2. Show Typing Indicator
    showTypingIndicator();
    
    // 3. Fetch from Backend API
    try {
      const response = await fetch('/api/process', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ text: text })
      });
      
      const data = await response.json();
      hideTypingIndicator();
      addBotMessage(data);
    } catch (error) {
      console.error("Error communicating with backend:", error);
      hideTypingIndicator();
      addBotMessage({ error: "Failed to connect to the server. Please ensure the backend is running." });
    }
  }

  function addUserMessage(text) {
    const msgDiv = document.createElement('div');
    msgDiv.className = 'message user-message';
    
    msgDiv.innerHTML = `
      <div class="message-content">
        <p>${escapeHTML(text)}</p>
        <span class="timestamp">${getCurrentTime()}</span>
      </div>
    `;
    
    chatHistory.appendChild(msgDiv);
    scrollToBottom();
  }

  function addBotMessage(data) {
    const msgDiv = document.createElement('div');
    msgDiv.className = 'message bot-message';
    
    // Format JSON output
    const jsonString = JSON.stringify(data, null, 2);
    
    msgDiv.innerHTML = `
      <img src="images/bot_avatar.png" alt="Bot" class="message-avatar">
      <div class="message-content">
        <pre>${escapeHTML(jsonString)}</pre>
        <span class="timestamp">${getCurrentTime()}</span>
      </div>
    `;
    
    chatHistory.appendChild(msgDiv);
    scrollToBottom();
  }

  function showTypingIndicator() {
    typingIndicator.style.display = 'flex';
    scrollToBottom();
  }

  function hideTypingIndicator() {
    typingIndicator.style.display = 'none';
  }

  function scrollToBottom() {
    // Small timeout to allow DOM to update before scrolling
    setTimeout(() => {
      chatHistory.scrollTop = chatHistory.scrollHeight;
    }, 50);
  }

  function getCurrentTime() {
    const now = new Date();
    let hours = now.getHours();
    let minutes = now.getMinutes();
    const ampm = hours >= 12 ? 'PM' : 'AM';
    
    hours = hours % 12;
    hours = hours ? hours : 12;
    minutes = minutes < 10 ? '0' + minutes : minutes;
    
    return `${hours}:${minutes} ${ampm}`;
  }

  // Utility to prevent XSS
  function escapeHTML(str) {
    return str.replace(/[&<>'"]/g, 
      tag => ({
          '&': '&amp;',
          '<': '&lt;',
          '>': '&gt;',
          "'": '&#39;',
          '"': '&quot;'
        }[tag])
    );
  }
});
