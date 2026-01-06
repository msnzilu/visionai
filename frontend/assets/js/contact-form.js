/**
 * ContactFormHandler - Reusable controller for contact forms
 */
const ContactFormHandler = {
    init() {
        const contactForms = document.querySelectorAll('[data-contact-form]');
        contactForms.forEach(form => this.bindForm(form));
        console.log(`ContactFormHandler initialized for ${contactForms.length} forms`);
    },

    bindForm(form) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();

            const submitBtn = form.querySelector('button[type="submit"]');
            const originalBtnText = submitBtn.innerHTML;
            const successMsg = document.getElementById(form.getAttribute('data-success-id') || 'successMessage');

            // Get form data
            const formData = new FormData(form);
            const data = Object.fromEntries(formData.entries());

            // Validation (Basic)
            if (!data.name || !data.email || !data.message) {
                this.showAlert('Please fill in all required fields.', 'error');
                return;
            }

            try {
                // Set loading state
                this.setLoading(submitBtn, true, originalBtnText);

                // Send email
                await ContactService.sendEmail(data);

                // Handle success
                form.reset();
                if (successMsg) {
                    successMsg.classList.remove('hidden');
                    // Scroll to success message
                    successMsg.scrollIntoView({ behavior: 'smooth', block: 'center' });

                    // Hide after 10 seconds
                    setTimeout(() => {
                        successMsg.classList.add('hidden');
                    }, 10000);
                } else {
                    this.showAlert('Message sent successfully!', 'success');
                }

            } catch (error) {
                console.error('Form submission error:', error);
                this.showAlert(error.message || 'Failed to send message. Please try again.', 'error');
            } finally {
                this.setLoading(submitBtn, false, originalBtnText);
            }
        });
    },

    setLoading(button, isLoading, originalText) {
        if (isLoading) {
            button.disabled = true;
            button.innerHTML = `
                <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-white inline-block" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Sending...
            `;
        } else {
            button.disabled = false;
            button.innerHTML = originalText;
        }
    },

    showAlert(message, type) {
        if (window.CVision && window.CVision.showAlert) {
            window.CVision.showAlert(message, type);
        } else if (window.Toast) {
            window.Toast.show(message, type);
        } else {
            // Simplified custom toast fallback if nothing else is available
            const toast = document.createElement('div');
            toast.className = `fixed bottom-4 right-4 p-4 rounded-lg shadow-xl text-white z-50 transition-all ${type === 'error' ? 'bg-red-600' : 'bg-green-600'
                }`;
            toast.textContent = message;
            document.body.appendChild(toast);
            setTimeout(() => toast.remove(), 5000);
        }
    }
};

// Initialize after DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    ContactFormHandler.init();
});

window.ContactFormHandler = ContactFormHandler;
