/**
 * InlineMessage.js - Simple inline message framework
 * Just include this file and use InlineMessage.success(), .error(), etc.
 */
class InlineMessage {
    static containers = new Map();
    static messageId = 0;
    static stylesAdded = false;

    static show(message, type = 'info', options = {}) {
        this.addStyles();
        
        const config = {
            autoHide: true,
            autoHideDelay: 5000,
            container: null,
            closeButton: false,
            ...options
        };

        const container = this.getContainer(config.container);
        const id = `msg-${++this.messageId}`;
        const messageEl = this.createElement(message, type, id, config);
        
        container.insertBefore(messageEl, container.firstChild);

        // Auto-hide success/info messages
        if (config.autoHide && (type === 'success' || type === 'info')) {
            setTimeout(() => this.hide(id), config.autoHideDelay);
        }

        return id;
    }

    static success(message, options = {}) {
        return this.show(message, 'success', options);
    }

    static error(message, options = {}) {
        return this.show(message, 'error', { autoHide: false, ...options });
    }

    static warning(message, options = {}) {
        return this.show(message, 'warning', options);
    }

    static info(message, options = {}) {
        return this.show(message, 'info', options);
    }

    static hide(messageId) {
        const el = document.getElementById(messageId);
        if (el) {
            el.style.opacity = '0';
            setTimeout(() => el.remove(), 300);
        }
    }

    static clear(containerSelector = null) {
        if (containerSelector) {
            const container = this.containers.get(containerSelector);
            if (container) container.innerHTML = '';
        } else {
            this.containers.forEach(container => container.innerHTML = '');
        }
    }

    static getContainer(selector) {
        if (!selector) {
            selector = document.querySelector('form') || document.body;
        }

        if (this.containers.has(selector)) {
            return this.containers.get(selector);
        }

        const targetEl = typeof selector === 'string' ? document.querySelector(selector) : selector;
        let container = targetEl.querySelector('.message-container');
        
        if (!container) {
            container = document.createElement('div');
            container.className = 'message-container';
            targetEl.insertBefore(container, targetEl.firstChild);
        }

        this.containers.set(selector, container);
        return container;
    }

    static createElement(message, type, id, config) {
        const el = document.createElement('div');
        el.id = id;
        el.className = `inline-message inline-message--${type}`;
        
        const icons = { success: '✓', error: '✕', warning: '⚠', info: 'ℹ' };
        
        el.innerHTML = `
            <span class="inline-message__icon">${icons[type]}</span>
            <span class="inline-message__text">${message}</span>
            ${config.closeButton ? `<button onclick="InlineMessage.hide('${id}')" class="inline-message__close">✕</button>` : ''}
        `;

        el.style.opacity = '0';
        el.style.transform = 'translateY(-10px)';
        
        setTimeout(() => {
            el.style.transition = 'all 0.3s ease';
            el.style.opacity = '1';
            el.style.transform = 'translateY(0)';
        }, 10);

        return el;
    }

    static addStyles() {
        if (this.stylesAdded) return;
        
        const style = document.createElement('style');
        style.textContent = `
            .message-container { margin: 16px 0; }
            .inline-message {
                display: flex;
                align-items: center;
                gap: 12px;
                padding: 14px 18px;
                margin-bottom: 10px;
                border-radius: 6px;
                border-left: 4px solid;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                font-size: 14px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }
            .inline-message__icon { font-weight: bold; font-size: 16px; }
            .inline-message__text { flex: 1; }
            .inline-message__close {
                background: none;
                border: none;
                font-size: 16px;
                cursor: pointer;
                opacity: 0.6;
                padding: 4px;
            }
            .inline-message__close:hover { opacity: 1; }
            .inline-message--success {
                background: #f0f9ff;
                border-color: #10b981;
                color: #065f46;
            }
            .inline-message--error {
                background: #fef2f2;
                border-color: #ef4444;
                color: #991b1b;
            }
            .inline-message--warning {
                background: #fffbeb;
                border-color: #f59e0b;
                color: #92400e;
            }
            .inline-message--info {
                background: #eff6ff;
                border-color: #3b82f6;
                color: #1e40af;
            }
            @media (max-width: 768px) {
                .inline-message { padding: 12px 14px; font-size: 13px; }
            }
        `;
        document.head.appendChild(style);
        this.stylesAdded = true;
    }
}

// Auto-add styles when DOM loads
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => InlineMessage.addStyles());
} else {
    InlineMessage.addStyles();
}

// Optional: Replace CVision.Utils.showAlert if it exists
if (typeof CVision !== 'undefined' && CVision.Utils) {
    CVision.Utils.showAlert = (message, type) => InlineMessage.show(message, type);
    CVision.Utils.showInlineMessage = (message, type, options) => InlineMessage.show(message, type, options);
}