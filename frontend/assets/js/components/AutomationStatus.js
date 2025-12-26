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
    }

    show() {
        if (this.isVisible) return;
        this.container.classList.add('active');
        this.isVisible = true;
        this.reset();
    }

    hide(delay = 3000) {
        setTimeout(() => {
            this.container.classList.remove('active');
            this.isVisible = false;
        }, delay);
    }

    updateStatus(status, message, progress = null) {
        if (!this.isVisible) this.show();

        // Sanitize technical messages for the user
        let displayMessage = message;
        if (message.includes('host.docker.internal')) {
            displayMessage = 'Cannot connect to the automation service. Please try again in a few moments.';
        }

        this.messageEl.textContent = displayMessage;
        this.statusBadge.textContent = status.toUpperCase();

        // Update styling based on status
        this.container.classList.remove('error', 'completed');
        this.statusBadge.classList.remove('status-active', 'status-completed', 'status-error');

        if (status === 'error' || status === 'failed') {
            this.container.classList.add('error');
            this.statusBadge.classList.add('status-error');
        } else if (status === 'completed' || status === 'success') {
            this.container.classList.add('completed');
            this.statusBadge.classList.add('status-completed');
            this.setProgress(100);
        } else {
            this.statusBadge.classList.add('status-active');
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
