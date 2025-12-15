// wrapper to avoid global scope pollution
(function (window) {
    const DeleteAccountModal = {
        init: function () {
            this.modal = document.getElementById('deleteAccountModal');
            this.form = document.getElementById('deleteAccountForm');
            this.confirmInput = document.getElementById('deleteConfirmation');
            this.deleteBtn = document.getElementById('confirmDeleteBtn');
            this.setupListeners();
            console.log('DeleteAccountModal initialized');
        },

        setupListeners: function () {
            // Confirmation input validation
            if (this.confirmInput) {
                this.confirmInput.addEventListener('input', (e) => {
                    const isValid = e.target.value === 'DELETE';
                    if (this.deleteBtn) {
                        this.deleteBtn.disabled = !isValid;
                    }
                });
            }

            // Form submission
            if (this.form) {
                this.form.addEventListener('submit', (e) => this.handleSubmit(e));
            }

            // Close when clicking outside
            if (this.modal) {
                this.modal.addEventListener('click', (e) => {
                    if (e.target === this.modal || e.target.querySelector('#deleteAccountModal > div.fixed')) {
                        // this.close(); // Optional: allow clicking outside to close
                    }
                });
            }
        },

        open: function () {
            if (this.modal) {
                this.modal.classList.remove('hidden');
                // Reset form
                if (this.form) this.form.reset();
                if (this.deleteBtn) this.deleteBtn.disabled = true;
                if (this.confirmInput) this.confirmInput.focus();
            } else {
                console.error('DeleteAccountModal not found in DOM');
            }
        },

        close: function () {
            if (this.modal) {
                this.modal.classList.add('hidden');
            }
        },

        handleSubmit: async function (e) {
            e.preventDefault();

            const reason = document.getElementById('deleteReason')?.value || '';
            const confirmVal = this.confirmInput?.value;

            if (confirmVal !== 'DELETE') {
                CVision.Utils.showAlert('Please type DELETE to confirm.', 'error');
                return;
            }

            // Show loading state
            const originalBtnText = this.deleteBtn.innerText;
            this.deleteBtn.disabled = true;
            this.deleteBtn.innerText = 'Deleting...';

            try {
                const token = CVision.Utils.getToken();
                const response = await fetch(`${CONFIG.API_BASE_URL}${CONFIG.API_PREFIX}/users/me/deactivate?reason=${encodeURIComponent(reason)}`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    }
                });

                if (response.ok) {
                    CVision.Utils.showAlert('Account deleted successfully.', 'success');
                    // Clear session and redirect
                    setTimeout(() => {
                        CVision.Utils.logout(); // This handles token clearing and redirect
                    }, 1500);
                } else {
                    const data = await response.json();
                    throw new Error(data.detail || 'Failed to delete account');
                }
            } catch (error) {
                console.error('Delete account error:', error);
                CVision.Utils.showAlert(error.message, 'error');

                // Reset button
                this.deleteBtn.disabled = false;
                this.deleteBtn.innerText = originalBtnText;
            }
        }
    };

    // Expose globally
    window.DeleteAccountModal = DeleteAccountModal;

})(window);
