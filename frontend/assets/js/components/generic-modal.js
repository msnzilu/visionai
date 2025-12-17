/**
 * Reusable Generic Modal Component
 * For displaying success/error/info messages.
 */
class GenericModal {
    constructor() {
        this.modalId = 'generic-modal';
        this.init();
    }

    init() {
        if (!document.getElementById(this.modalId)) {
            this.injectModal();
        }
    }

    injectModal() {
        const modalHtml = `
            <div id="${this.modalId}" class="fixed inset-0 z-50 hidden overflow-y-auto" aria-labelledby="modal-title" role="dialog" aria-modal="true">
                <div class="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
                    <div class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" aria-hidden="true" onclick="GenericModal.instance.close()"></div>
                    <span class="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>
                    <div class="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
                        <div class="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                            <div class="sm:flex sm:items-start">
                                <div id="${this.modalId}-icon-bg" class="mx-auto flex-shrink-0 flex items-center justify-center h-12 w-12 rounded-full sm:mx-0 sm:h-10 sm:w-10">
                                    <svg id="${this.modalId}-icon" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <!-- Icon injected dynamically -->
                                    </svg>
                                </div>
                                <div class="mt-3 text-center sm:mt-0 sm:ml-4 sm:text-left w-full">
                                    <h3 class="text-lg leading-6 font-medium text-gray-900" id="${this.modalId}-title">
                                        <!-- Title -->
                                    </h3>
                                    <div class="mt-2">
                                        <p class="text-sm text-gray-500" id="${this.modalId}-message">
                                            <!-- Message -->
                                        </p>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                            <button type="button" id="${this.modalId}-primary-btn" onclick="GenericModal.instance.close()"
                                class="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 text-base font-medium text-white focus:outline-none focus:ring-2 focus:ring-offset-2 sm:ml-3 sm:w-auto sm:text-sm">
                                OK
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        document.body.insertAdjacentHTML('beforeend', modalHtml);
    }

    show({ title, message, type = 'info', buttonText = 'OK', onConfirm = null }) {
        const modal = document.getElementById(this.modalId);
        const titleEl = document.getElementById(`${this.modalId}-title`);
        const messageEl = document.getElementById(`${this.modalId}-message`);
        const iconBg = document.getElementById(`${this.modalId}-icon-bg`);
        const icon = document.getElementById(`${this.modalId}-icon`);
        const button = document.getElementById(`${this.modalId}-primary-btn`);

        titleEl.textContent = title;
        messageEl.textContent = message;
        button.textContent = buttonText;

        // Reset onclick to default close, or custom action
        button.onclick = () => {
            if (onConfirm) onConfirm();
            this.close();
        };

        // Styling based on type
        // Styling based on type
        if (type === 'success') {
            iconBg.className = 'mx-auto flex-shrink-0 flex items-center justify-center h-12 w-12 rounded-full bg-green-100 sm:mx-0 sm:h-10 sm:w-10';
            icon.setAttribute('class', 'h-6 w-6 text-green-600');
            icon.innerHTML = '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />';
            button.className = 'w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-green-600 text-base font-medium text-white hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 sm:ml-3 sm:w-auto sm:text-sm';
        } else if (type === 'error') {
            iconBg.className = 'mx-auto flex-shrink-0 flex items-center justify-center h-12 w-12 rounded-full bg-red-100 sm:mx-0 sm:h-10 sm:w-10';
            icon.setAttribute('class', 'h-6 w-6 text-red-600');
            icon.innerHTML = '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />';
            button.className = 'w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-red-600 text-base font-medium text-white hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 sm:ml-3 sm:w-auto sm:text-sm';
        } else {
            // Info
            iconBg.className = 'mx-auto flex-shrink-0 flex items-center justify-center h-12 w-12 rounded-full bg-blue-100 sm:mx-0 sm:h-10 sm:w-10';
            icon.setAttribute('class', 'h-6 w-6 text-blue-600');
            icon.innerHTML = '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />';
            button.className = 'w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-blue-600 text-base font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:ml-3 sm:w-auto sm:text-sm';
        }

        modal.classList.remove('hidden');
    }

    close() {
        document.getElementById(this.modalId).classList.add('hidden');
    }
}

// Global instance
window.GenericModal = GenericModal;
// Initialize immediately so it's ready
window.addEventListener('load', () => {
    window.GenericModal.instance = new GenericModal();
});
