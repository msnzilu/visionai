/**
 * AutomationStatus.js
 * 
 * A reusable UI component to show real-time progress of browser automation.
 */
class AutomationStatus {
    constructor() {
        this.container = null;
        this.progressBar = null;
        this.messageEl = null;
        this.statusBadge = null;
        this.logContainer = null;
        this.isVisible = false;
        this.hideTimer = null;

        this._injectStyles();
        this._createElements();
    }

    _injectStyles() {
        if (!document.getElementById('automation-status-styles')) {
            const link = document.createElement('link');
            link.id = 'automation-status-styles';
            link.rel = 'stylesheet';
            link.href = '/assets/css/components/automation-status.css';
            document.head.appendChild(link);
        }
    }

    _createElements() {
        const overlay = document.createElement('div');
        overlay.className = 'automation-status-overlay';
        overlay.innerHTML = `
            <div class="automation-header">
                <div class="automation-title">
                    <span class="automation-bot-icon">🤖</span>
                    <span>Automation Assistant</span>
                </div>
                <div class="automation-status-badge status-active">Active</div>
                <button class="automation-close-btn" aria-label="Close">&times;</button>
            </div>
            <div class="automation-message-container">
                <p class="automation-message">Initializing automation engine...</p>
            </div>
            <div class="automation-progress-container">
                <div class="automation-progress-bar"></div>
            </div>
            <div class="automation-logs"></div>
        `;

        document.body.appendChild(overlay);

        this.container = overlay;
        this.progressBar = overlay.querySelector('.automation-progress-bar');
        this.messageEl = overlay.querySelector('.automation-message');
        this.statusBadge = overlay.querySelector('.automation-status-badge');
        this.logContainer = overlay.querySelector('.automation-logs');

        // Close button handler
        overlay.querySelector('.automation-close-btn').addEventListener('click', () => this.hide(0));
    }

    show() {
        this.reset();
        if (this.isVisible) return;
        this.container.classList.add('active');
        this.isVisible = true;
    }

    hide(delay = 3000) {
        if (this.hideTimer) clearTimeout(this.hideTimer);
        this.hideTimer = setTimeout(() => {
            this.container.classList.remove('active');
            this.isVisible = false;
            this.hideTimer = null;
        }, delay);
    }

    updateStatus(status, message, progress = null) {
        if (!this.isVisible) this.show();

        const lowerStatus = status.toLowerCase();

        // Sanitize technical messages for the user
        let displayMessage = message;

        // Map technical errors to user-friendly messages
        if (message.includes('No application form detected')) {
            displayMessage = '⚠️ No application form found on this page. This job may require applying directly on the company website.';
        } else if (message.includes('host.docker.internal') || message.includes('Cannot connect')) {
            displayMessage = '🔌 Cannot connect to the automation service. Please try again in a few moments.';
        } else if (message.includes('Target page, context or browser has been closed')) {
            displayMessage = '🔄 The page was closed or navigated away. Please try applying again.';
        } else if (message.includes('Timeout') || message.includes('timeout')) {
            displayMessage = '⏱️ The page took too long to respond. Please try again.';
        } else if (message.includes('rate limit') || message.includes('429')) {
            displayMessage = '⏳ Too many requests. Please wait a moment and try again.';
        } else if (message.includes('login') || message.includes('sign in') || message.includes('account required')) {
            displayMessage = '🔐 This job requires creating an account. We\'re working on automating this!';
        }

        this.messageEl.textContent = displayMessage;
        this.statusBadge.textContent = status.toUpperCase();

        // Update styling based on status
        this.container.classList.remove('error', 'completed');
        this.statusBadge.classList.remove('status-active', 'status-completed', 'status-error');

        if (lowerStatus === 'error' || lowerStatus === 'failed') {
            this.container.classList.add('error');
            this.statusBadge.classList.add('status-error');
            this.hide(6000); // Hide after 6 seconds on error
        } else if (lowerStatus === 'completed' || lowerStatus === 'success') {
            this.container.classList.add('completed');
            this.statusBadge.classList.add('status-completed');
            this.setProgress(100);
            this.hide(4000); // Hide after 4 seconds on success
        } else {
            this.statusBadge.classList.add('status-active');
            if (this.hideTimer) {
                clearTimeout(this.hideTimer);
                this.hideTimer = null;
            }
        }

        if (progress !== null) {
            this.setProgress(progress);
        }

        this.addLog(message, status === 'error' ? 'error' : 'info');
    }

    setProgress(percent) {
        this.progressBar.style.width = `${percent}%`;
    }

    addLog(message, type = 'info') {
        // Skip technical or redundant logs to keep the UI clean
        if (message.includes('host.docker.internal') || message.includes('warmed up')) {
            return;
        }

        const entry = document.createElement('div');
        entry.className = `log-entry ${type}`;
        entry.textContent = `[${new Date().toLocaleTimeString([], { hour12: false })}] ${message}`;
        this.logContainer.prepend(entry);

        // Keep only last 10 logs
        while (this.logContainer.children.length > 10) {
            this.logContainer.lastChild.remove();
        }
    }

    reset() {
        this.progressBar.style.width = '0%';
        this.logContainer.innerHTML = '';
        this.container.classList.remove('error', 'completed');
    }
}

// Global initialization
window.AutomationUI = new AutomationStatus();
