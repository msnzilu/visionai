/**
 * Reusable Forgot Password Modal Component
 * Can be instantiated on any page.
 */
class ForgotPasswordModal {
    constructor() {
        this.modalId = 'forgotPasswordModal';
        this.apiUrl = '/api/v1/auth/forgot-password';
        this.init();
    }

    init() {
        // Check if modal already exists to prevent duplicates
        if (!document.getElementById(this.modalId)) {
            this.injectModal();
        }
        this.attachEventListeners();
    }

    injectModal() {
        const modalHtml = `
            <div id="${this.modalId}" class="fixed inset-0 z-50 hidden overflow-y-auto" aria-labelledby="modal-title" role="dialog" aria-modal="true">
                <div class="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
                    <!-- Background overlay -->
                    <div class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" aria-hidden="true" id="${this.modalId}-backdrop"></div>

                    <!-- Modal panel -->
                    <span class="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>
                    <div class="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
                        <div class="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                            <div class="sm:flex sm:items-start">
                                <div class="mx-auto flex-shrink-0 flex items-center justify-center h-12 w-12 rounded-full bg-blue-100 sm:mx-0 sm:h-10 sm:w-10">
                                    <svg class="h-6 w-6 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 15.5l-2.029-4.057-2.029 4.057-2.029-4.057-2.029 4.057A2 2 0 012 12V6a2 2 0 012-2h12zm0 0a2 2 0 012 2" />
                                    </svg>
                                </div>
                                <div class="mt-3 text-center sm:mt-0 sm:ml-4 sm:text-left w-full">
                                    <h3 class="text-lg leading-6 font-medium text-gray-900" id="modal-title">
                                        Reset Password
                                    </h3>
                                    <div class="mt-2">
                                        <p class="text-sm text-gray-500 mb-4">
                                            Enter your email address and we'll send you a link to reset your password.
                                        </p>
                                        <form id="${this.modalId}-form" class="space-y-4">
                                            <div>
                                                <label for="${this.modalId}-email" class="sr-only">Email address</label>
                                                <input type="email" name="email" id="${this.modalId}-email" required
                                                    class="appearance-none rounded-md relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                                                    placeholder="Email address">
                                            </div>
                                            <div id="${this.modalId}-message" class="text-sm hidden"></div>
                                        </form>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                            <button type="button" id="${this.modalId}-submit"
                                class="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-blue-600 text-base font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:ml-3 sm:w-auto sm:text-sm">
                                Send Reset Link
                            </button>
                            <button type="button" id="${this.modalId}-cancel"
                                class="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm">
                                Cancel
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        document.body.insertAdjacentHTML('beforeend', modalHtml);
    }

    attachEventListeners() {
        const backdrop = document.getElementById(`${this.modalId}-backdrop`);
        const cancelButton = document.getElementById(`${this.modalId}-cancel`);
        const submitButton = document.getElementById(`${this.modalId}-submit`);

        backdrop.addEventListener('click', () => this.close());
        cancelButton.addEventListener('click', () => this.close());
        submitButton.addEventListener('click', () => this.submit());
    }

    open() {
        document.getElementById(this.modalId).classList.remove('hidden');
    }

    close() {
        document.getElementById(this.modalId).classList.add('hidden');
        document.getElementById(`${this.modalId}-message`).classList.add('hidden');
        document.getElementById(`${this.modalId}-form`).reset();
    }

    async submit() {
        const emailInput = document.getElementById(`${this.modalId}-email`);
        const messageDiv = document.getElementById(`${this.modalId}-message`);
        const submitBtn = document.getElementById(`${this.modalId}-submit`);

        const email = emailInput.value;
        if (!email) {
            this.showMessage('Please enter your email address.', 'text-red-600');
            return;
        }

        // Loading state
        const originalText = submitBtn.innerText;
        submitBtn.disabled = true;
        submitBtn.innerText = 'Sending...';
        messageDiv.classList.add('hidden');

        try {
            const response = await fetch(this.apiUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email }),
            });

            const data = await response.json();

            if (data.success) {
                this.showMessage(data.message, 'text-green-600');
                // Optional: Close modal after a delay
                setTimeout(() => this.close(), 3000);
            } else {
                this.showMessage(data.message || 'An error occurred.', 'text-red-600');
            }
        } catch (error) {
            console.error('Forgot password error:', error);
            this.showMessage('Network error. Please try again.', 'text-red-600');
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerText = originalText;
        }
    }

    showMessage(text, colorClass) {
        const messageDiv = document.getElementById(`${this.modalId}-message`);
        messageDiv.innerText = text;
        messageDiv.className = `text-sm mt-2 ${colorClass}`;
        messageDiv.classList.remove('hidden');
    }
}

// Auto-initialize if desired, or let the page script do it.
// We'll attach it to window for easy access
window.ForgotPasswordModal = ForgotPasswordModal;
