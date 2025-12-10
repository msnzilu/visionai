/**
 * Modal Component
 * Generic modal system for confirmations and content.
 * 
 * Usage:
 * Modal.confirm({
 *     title: 'Delete Document?',
 *     message: 'Are you sure you want to delete this file? This cannot be undone.',
 *     confirmText: 'Delete',
 *     confirmColor: 'red',
 *     onConfirm: () => { deleteLogic(); }
 * });
 */

const Modal = {
    // Ensure modal container exists
    init() {
        if (document.getElementById('modal-overlay')) return;

        const overlay = document.createElement('div');
        overlay.id = 'modal-overlay';
        overlay.className = 'fixed inset-0 z-50 bg-gray-900 bg-opacity-50 backdrop-blur-sm hidden flex items-center justify-center transition-opacity opacity-0';
        overlay.innerHTML = `
            <div id="modal-content" class="bg-white rounded-xl shadow-2xl w-full max-w-md p-6 transform transition-all scale-95 opacity-0">
                <div class="mb-4">
                    <h3 id="modal-title" class="text-lg font-bold text-gray-900"></h3>
                    <p id="modal-message" class="text-sm text-gray-600 mt-2"></p>
                </div>
                <div id="modal-actions" class="flex justify-end gap-3 mt-6">
                    <button id="modal-cancel" class="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg text-sm font-medium transition-colors">Cancel</button>
                    <button id="modal-confirm" class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition-colors shadow-sm">Confirm</button>
                </div>
            </div>
        `;
        document.body.appendChild(overlay);

        // Close on backdrop click
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) Modal.close();
        });

        // Close on Escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && !overlay.classList.contains('hidden')) {
                Modal.close();
            }
        });
    },

    confirm({ title, message, confirmText = 'Confirm', confirmColor = 'blue', onConfirm }) {
        this.init();

        const overlay = document.getElementById('modal-overlay');
        const content = document.getElementById('modal-content');
        const titleEl = document.getElementById('modal-title');
        const messageEl = document.getElementById('modal-message');
        const confirmBtn = document.getElementById('modal-confirm');
        const cancelBtn = document.getElementById('modal-cancel');

        titleEl.textContent = title;
        messageEl.textContent = message;
        confirmBtn.textContent = confirmText;

        // Reset classes
        confirmBtn.className = `px-4 py-2 text-white rounded-lg text-sm font-medium transition-colors shadow-sm`;

        // Apply color
        if (confirmColor === 'red') {
            confirmBtn.classList.add('bg-red-600', 'hover:bg-red-700');
        } else {
            confirmBtn.classList.add('bg-blue-600', 'hover:bg-blue-700');
        }

        // Handlers
        const handleConfirm = () => {
            onConfirm();
            Modal.close();
            cleanup();
        };

        const handleCancel = () => {
            Modal.close();
            cleanup();
        };

        const cleanup = () => {
            confirmBtn.onclick = null;
            cancelBtn.onclick = null;
        };

        confirmBtn.onclick = handleConfirm;
        cancelBtn.onclick = handleCancel;

        // Show
        overlay.classList.remove('hidden');
        // Trigger reflow for animation
        void overlay.offsetWidth;

        overlay.classList.remove('opacity-0');
        content.classList.remove('scale-95', 'opacity-0');
        content.classList.add('scale-100', 'opacity-100');
    },

    close() {
        const overlay = document.getElementById('modal-overlay');
        const content = document.getElementById('modal-content');

        if (overlay) {
            overlay.classList.add('opacity-0');
            if (content) {
                content.classList.remove('scale-100', 'opacity-100');
                content.classList.add('scale-95', 'opacity-0');
            }

            setTimeout(() => {
                overlay.classList.add('hidden');
            }, 300);
        }
    }
};

window.Modal = Modal;
