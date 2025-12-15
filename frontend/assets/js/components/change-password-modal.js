/**
 * Change Password Modal Component
 * Handles UI logic and API interaction for password updates
 */

const ChangePasswordModal = {
    modalId: 'changePasswordModal',
    formId: 'changePasswordForm',

    init() {
        // Event delegation if form doesn't exist yet? No, assuming init called after HTML injection.
        const form = document.getElementById(this.formId);
        if (form) {
            // Remove old listeners to be safe (though usually init called once)
            const newForm = form.cloneNode(true);
            form.parentNode.replaceChild(newForm, form);

            newForm.addEventListener('submit', this.handleSubmit.bind(this));
        } else {
            console.error('ChangePasswordModal: Form not found');
        }
    },

    open() {
        const modal = document.getElementById(this.modalId);
        if (modal) {
            modal.classList.remove('hidden');
        } else {
            console.error('ChangePasswordModal: Modal not found');
        }
    },

    close() {
        const modal = document.getElementById(this.modalId);
        const form = document.getElementById(this.formId);
        if (modal) {
            modal.classList.add('hidden');
        }
        if (form) {
            form.reset();
        }
    },

    async handleSubmit(e) {
        e.preventDefault();

        const currentPassword = document.getElementById('currentPassword').value;
        const newPassword = document.getElementById('newPassword').value;
        const confirmNewPassword = document.getElementById('confirmNewPassword').value;

        if (newPassword !== confirmNewPassword) {
            CVision.Utils.showAlert('New passwords do not match', 'error');
            return;
        }

        try {
            const response = await fetch(`${CONFIG.API_BASE_URL}${CONFIG.API_PREFIX}/auth/change-password`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${CVision.Utils.getToken()}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    current_password: currentPassword,
                    new_password: newPassword
                })
            });

            const data = await response.json();

            if (response.ok && data.success) {
                CVision.Utils.showAlert('Password updated successfully', 'success');
                this.close();
            } else {
                throw new Error(data.message || 'Failed to update password');
            }
        } catch (error) {
            console.error('Password change error:', error);
            CVision.Utils.showAlert(error.message, 'error');
        }
    }
};

// Expose to window
window.ChangePasswordModal = ChangePasswordModal;
