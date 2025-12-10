/**
 * Toast Component
 * Floating notifications for success, error, and info messages.
 * 
 * Usage:
 * Toast.show('Operation successful', 'success');
 * Toast.show('Something went wrong', 'error');
 */

const Toast = {
    container: null,

    init() {
        if (this.container) return;

        this.container = document.createElement('div');
        this.container.id = 'toast-container';
        this.container.style.cssText = `
            position: fixed;
            top: 1rem;
            right: 1rem;
            z-index: 9999;
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
            pointer-events: none;
        `;
        document.body.appendChild(this.container);
    },

    show(message, type = 'info', duration = 5000) {
        this.init();

        const toast = document.createElement('div');
        toast.className = `toast toast-${type} animate-slide-in-right`;

        // Tailwind classes for styling (pointer-events-auto needed as container is none)
        const baseClasses = 'pointer-events-auto flex items-center w-full max-w-sm p-4 rounded-lg shadow-lg border-l-4 transition-all transform ease-out duration-300 translate-x-full opacity-0';

        let typeClasses = '';
        let icon = '';

        switch (type) {
            case 'success':
                typeClasses = 'bg-white border-green-500 text-gray-800';
                icon = `<svg class="w-5 h-5 text-green-500 mr-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>`;
                break;
            case 'error':
                typeClasses = 'bg-white border-red-500 text-gray-800';
                icon = `<svg class="w-5 h-5 text-red-500 mr-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>`;
                break;
            default: // info
                typeClasses = 'bg-white border-blue-500 text-gray-800';
                icon = `<svg class="w-5 h-5 text-blue-500 mr-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>`;
        }

        toast.className = `${baseClasses} ${typeClasses}`;
        toast.innerHTML = `
            ${icon}
            <div class="flex-1 text-sm font-medium mr-2">${message}</div>
            <button onclick="this.parentElement.remove()" class="text-gray-400 hover:text-gray-600 focus:outline-none">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
            </button>
        `;

        this.container.appendChild(toast);

        // Animate in
        requestAnimationFrame(() => {
            toast.classList.remove('translate-x-full', 'opacity-0');
        });

        // Auto dismiss
        if (duration > 0) {
            setTimeout(() => {
                this.dismiss(toast);
            }, duration);
        }

        // Return toast element (useful for manual dismissal)
        return toast;
    },

    dismiss(toast) {
        toast.classList.add('translate-x-full', 'opacity-0');
        setTimeout(() => {
            if (toast.parentElement) {
                toast.remove();
            }
        }, 300); // Match transition duration
    }
};

// Export
window.Toast = Toast;
