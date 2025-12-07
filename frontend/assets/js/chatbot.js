/**
 * CVision AI Chatbot
 * Smart chatbot with keyword-based responses and human support escalation
 */

const CVisionChatbot = {
    isOpen: false,
    messages: [],
    escalationTriggered: false,
    failedAttempts: 0,

    // Knowledge base for AI responses
    knowledgeBase: {
        greeting: {
            keywords: ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening'],
            responses: [
                "Hi there! 👋 I'm the CVision AI assistant. How can I help you today?",
                "Hello! Welcome to CVision. What can I assist you with?",
                "Hey! I'm here to help. What would you like to know about CVision?"
            ]
        },
        account: {
            keywords: ['account', 'sign up', 'register', 'login', 'password', 'reset', 'forgot'],
            responses: [
                "For account-related questions:\n\n• To create an account, click 'Get Started' in the top right\n• Forgot password? Use the 'Forgot Password' link on the login page\n• You can sign up with email, Google, or LinkedIn\n\nNeed more help with your account?"
            ]
        },
        features: {
            keywords: ['features', 'what can', 'capabilities', 'ai', 'cv analysis', 'job matching', 'auto-apply'],
            responses: [
                "CVision offers powerful AI features:\n\n🤖 AI CV Analysis - Instant resume optimization\n🎯 Smart Job Matching - Find perfect opportunities\n📝 Custom CV Generation - Tailored for each job\n✉️ AI Cover Letters - Personalized applications\n🚀 One-Click Apply - Save hours every week\n📊 Application Tracking - Monitor all applications\n\nWant to learn more about any specific feature?"
            ]
        },
        pricing: {
            keywords: ['price', 'cost', 'plan', 'subscription', 'free', 'premium', 'basic', 'upgrade'],
            responses: [
                "We have 3 pricing plans:\n\n💚 Free - $0/month\n• 1 search/month, 3 jobs per search\n\n⭐ Basic - $20/month (Most Popular)\n• 150 searches/month, premium templates\n\n🚀 Premium - $49/month\n• 200 searches/month, full automation\n\nAll plans include a 14-day money-back guarantee. Want to see detailed pricing?"
            ]
        },
        howItWorks: {
            keywords: ['how', 'work', 'process', 'steps', 'start', 'use'],
            responses: [
                "Getting started with CVision is easy:\n\n1️⃣ Upload Your CV - We analyze your skills instantly\n2️⃣ Find Jobs - AI matches you with perfect opportunities\n3️⃣ Customize - Generate tailored CVs and cover letters\n4️⃣ Apply - One-click application or full automation\n\nReady to get started? Click 'Get Started' to begin!"
            ]
        },
        technical: {
            keywords: ['error', 'bug', 'not working', 'broken', 'issue', 'problem', 'upload', 'file'],
            responses: [
                "I can help with technical issues:\n\n• Supported file formats: PDF, DOCX, TXT\n• Max file size: 10MB\n• Clear your browser cache if experiencing issues\n• Try a different browser (Chrome recommended)\n\nStill having problems? I can connect you with our technical support team."
            ]
        },
        billing: {
            keywords: ['cancel', 'refund', 'payment', 'charge', 'invoice', 'billing'],
            responses: [
                "Billing information:\n\n• Cancel anytime from account settings\n• 14-day money-back guarantee\n• We accept Visa, Mastercard, Amex, PayPal\n• Upgrade/downgrade anytime (prorated)\n\nNeed help with a specific billing issue?"
            ]
        },
        contact: {
            keywords: ['contact', 'support', 'email', 'phone', 'human', 'agent', 'representative'],
            responses: [
                "You can reach our support team:\n\n📧 Email: support@cvision.com (24hr response)\n💬 Live Chat: Available Mon-Fri, 9am-5pm EST\n📝 Contact Form: Available 24/7\n\nWould you like me to connect you with a human agent now?"
            ]
        }
    },

    quickActions: [
        "How does CVision work?",
        "What are the pricing plans?",
        "How do I upload my CV?",
        "Talk to a human"
    ],

    init() {
        this.createChatWidget();
        this.attachEventListeners();
        this.sendWelcomeMessage();
    },

    createChatWidget() {
        const chatHTML = `
            <!-- Chat Button -->
            <button class="chat-button" id="chatButton" aria-label="Open chat">
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                        d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"></path>
                </svg>
                <span class="notification-badge" id="chatBadge" style="display: none;">1</span>
            </button>

            <!-- Chat Window -->
            <div class="chat-window" id="chatWindow">
                <!-- Header -->
                <div class="chat-header">
                    <div class="chat-header-info">
                        <div class="chat-avatar">🤖</div>
                        <div class="chat-header-text">
                            <h3>CVision AI Assistant</h3>
                            <p>Typically replies instantly</p>
                        </div>
                    </div>
                    <div class="chat-header-actions">
                        <button class="chat-header-btn" id="chatMinimize" aria-label="Minimize chat">
                            <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
                            </svg>
                        </button>
                    </div>
                </div>

                <!-- Messages -->
                <div class="chat-messages" id="chatMessages"></div>

                <!-- Quick Actions -->
                <div class="quick-actions" id="quickActions"></div>

                <!-- Input Area -->
                <div class="chat-input-area">
                    <div class="chat-input-wrapper">
                        <input type="text" class="chat-input" id="chatInput" placeholder="Type your message..." />
                        <button class="chat-send-btn" id="chatSend" aria-label="Send message">
                            <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"></path>
                            </svg>
                        </button>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', chatHTML);
    },

    attachEventListeners() {
        const chatButton = document.getElementById('chatButton');
        const chatWindow = document.getElementById('chatWindow');
        const chatMinimize = document.getElementById('chatMinimize');
        const chatInput = document.getElementById('chatInput');
        const chatSend = document.getElementById('chatSend');

        chatButton.addEventListener('click', () => this.toggleChat());
        chatMinimize.addEventListener('click', () => this.toggleChat());
        chatSend.addEventListener('click', () => this.sendMessage());
        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.sendMessage();
        });
    },

    toggleChat() {
        this.isOpen = !this.isOpen;
        const chatWindow = document.getElementById('chatWindow');
        const chatBadge = document.getElementById('chatBadge');

        if (this.isOpen) {
            chatWindow.classList.add('active');
            chatBadge.style.display = 'none';
        } else {
            chatWindow.classList.remove('active');
        }
    },

    sendWelcomeMessage() {
        setTimeout(() => {
            this.addMessage('bot', "👋 Hi! I'm your CVision AI assistant. I can help you with questions about our features, pricing, and how to get started. How can I help you today?");
            this.showQuickActions();
            document.getElementById('chatBadge').style.display = 'flex';
        }, 1000);
    },

    showQuickActions() {
        const quickActionsContainer = document.getElementById('quickActions');
        quickActionsContainer.innerHTML = this.quickActions.map(action =>
            `<button class="quick-action-btn" onclick="CVisionChatbot.handleQuickAction('${action}')">${action}</button>`
        ).join('');
    },

    handleQuickAction(action) {
        document.getElementById('chatInput').value = action;
        this.sendMessage();
    },

    sendMessage() {
        const input = document.getElementById('chatInput');
        const message = input.value.trim();

        if (!message) return;

        this.addMessage('user', message);
        input.value = '';

        // Show typing indicator
        this.showTypingIndicator();

        // Process message and respond
        setTimeout(() => {
            this.hideTypingIndicator();
            this.processMessage(message);
        }, 1000 + Math.random() * 1000);
    },

    addMessage(sender, text) {
        const messagesContainer = document.getElementById('chatMessages');
        const time = new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });

        const messageHTML = `
            <div class="chat-message ${sender}">
                <div class="message-avatar">${sender === 'bot' ? '🤖' : '👤'}</div>
                <div class="message-content">
                    <div class="message-bubble">${text.replace(/\n/g, '<br>')}</div>
                    <div class="message-time">${time}</div>
                </div>
            </div>
        `;

        messagesContainer.insertAdjacentHTML('beforeend', messageHTML);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        this.messages.push({ sender, text, time });
    },

    showTypingIndicator() {
        const messagesContainer = document.getElementById('chatMessages');
        const typingHTML = `
            <div class="chat-message bot" id="typingIndicator">
                <div class="message-avatar">🤖</div>
                <div class="message-content">
                    <div class="typing-indicator">
                        <div class="typing-dot"></div>
                        <div class="typing-dot"></div>
                        <div class="typing-dot"></div>
                    </div>
                </div>
            </div>
        `;
        messagesContainer.insertAdjacentHTML('beforeend', typingHTML);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    },

    hideTypingIndicator() {
        const indicator = document.getElementById('typingIndicator');
        if (indicator) indicator.remove();
    },

    processMessage(message) {
        const lowerMessage = message.toLowerCase();

        // Check for escalation keywords
        if (lowerMessage.includes('human') || lowerMessage.includes('agent') || lowerMessage.includes('representative')) {
            this.triggerEscalation();
            return;
        }

        // Find matching category
        let response = null;
        for (const [category, data] of Object.entries(this.knowledgeBase)) {
            if (data.keywords.some(keyword => lowerMessage.includes(keyword))) {
                response = Array.isArray(data.responses)
                    ? data.responses[Math.floor(Math.random() * data.responses.length)]
                    : data.responses[0];
                this.failedAttempts = 0;
                break;
            }
        }

        // If no match found
        if (!response) {
            this.failedAttempts++;
            if (this.failedAttempts >= 2) {
                response = "I'm not sure I understand. Would you like me to connect you with a human support agent who can better assist you?";
                this.showEscalationOptions();
            } else {
                response = "I'm not sure I understand that question. Could you rephrase it? You can also try:\n\n• How does CVision work?\n• What are the pricing plans?\n• How do I upload my CV?\n• Talk to a human";
            }
        }

        this.addMessage('bot', response);
    },

    showEscalationOptions() {
        const messagesContainer = document.getElementById('chatMessages');
        const escalationHTML = `
            <div class="escalation-notice">
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                        d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
                <p>Having trouble? Our support team is here to help!</p>
            </div>
            <div class="escalation-actions">
                <button class="escalation-btn primary" onclick="CVisionChatbot.triggerEscalation()">Talk to Human</button>
                <button class="escalation-btn secondary" onclick="CVisionChatbot.continueWithBot()">Continue with AI</button>
            </div>
        `;
        messagesContainer.insertAdjacentHTML('beforeend', escalationHTML);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    },

    continueWithBot() {
        this.failedAttempts = 0;
        this.addMessage('bot', "No problem! I'm here to help. What else would you like to know?");
        this.showQuickActions();
    },

    triggerEscalation() {
        if (this.escalationTriggered) return;
        this.escalationTriggered = true;

        this.addMessage('bot', "I'm connecting you with our support team. This will take just a moment...");

        setTimeout(() => {
            this.addMessage('bot', "I've created a support ticket for you. Our team typically responds within 24 hours via email at support@cvision.com.\n\nYou can also:\n• Fill out our contact form for immediate assistance\n• Email us directly at support@cvision.com\n\nWould you like me to open the contact form?");

            const messagesContainer = document.getElementById('chatMessages');
            const contactHTML = `
                <div class="escalation-actions">
                    <button class="escalation-btn primary" onclick="window.location.href='contact.html'">Open Contact Form</button>
                    <button class="escalation-btn secondary" onclick="CVisionChatbot.continueWithBot()">Continue Chatting</button>
                </div>
            `;
            messagesContainer.insertAdjacentHTML('beforeend', contactHTML);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }, 1500);
    }
};

// Initialize chatbot when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    CVisionChatbot.init();
});

// Make openLiveChat function available globally (for help.html)
function openLiveChat() {
    if (!CVisionChatbot.isOpen) {
        CVisionChatbot.toggleChat();
    }
}
