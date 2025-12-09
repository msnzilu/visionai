const UpgradeModal = {
    init: async function (containerId = 'upgrade-modal-container') {
        const container = document.getElementById(containerId);
        if (!container) return; // Silent fail if container not found

        try {
            // Determine path based on current location (root or /pages/)
            const isPagesDir = window.location.pathname.includes('/pages/');
            const basePath = isPagesDir ? '../' : './';

            const response = await fetch(`${basePath}components/upgrade-modal.html`);
            if (response.ok) {
                const html = await response.text();
                container.innerHTML = html;
            }
        } catch (error) {
            console.error('Failed to load Upgrade Modal:', error);
        }
    },

    show: function (title, message) {
        const modal = document.getElementById('premiumModal');
        if (modal) {
            if (title) {
                const titleEl = document.getElementById('premiumModalTitle');
                if (titleEl) titleEl.textContent = title;
            }
            if (message) {
                const msgEl = document.getElementById('premiumModalDescription');
                if (msgEl) msgEl.textContent = message;
            }

            modal.style.display = 'flex';
            modal.style.pointerEvents = 'auto';
        } else {
            console.warn('Upgrade Modal not initialized');
        }
    },

    close: function () {
        const modal = document.getElementById('premiumModal');
        if (modal) {
            modal.style.display = 'none';
            modal.style.pointerEvents = 'none';
        }
    }
};

// Auto-init if container exists on load
document.addEventListener('DOMContentLoaded', () => {
    UpgradeModal.init();
});
