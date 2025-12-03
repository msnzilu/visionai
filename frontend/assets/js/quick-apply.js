// frontend/assets/js/quick-apply.js
/**
 * Quick Apply Form - Email Agent Integration
 * Handles form prefilling, validation, and submission via email
 */

class QuickApplyManager {
    constructor() {
        this.API_BASE_URL = window.location.origin;
        this.currentJobId = null;
        this.currentJobData = null;
    }

    /**
     * Open quick apply form for a job
     */
    async openQuickApplyForm(jobId) {
        try {
            this.currentJobId = jobId;

            // Show modal
            const modal = document.getElementById('quickApplyModal');
            if (!modal) {
                throw new Error('Quick apply form not loaded. Please refresh the page.');
            }
            modal.classList.remove('hidden');

            // Load prefill data
            await this.loadPrefillData(jobId);

            // Load user documents
            await this.loadUserDocuments();

        } catch (error) {
            console.error('Error opening quick apply form:', error);
            this.showError('Failed to load application form. Please try again.');
            this.closeQuickApplyForm();
        }
    }

    /**
     * Load and prefill form data from backend
     */
    async loadPrefillData(jobId) {
        try {
            const token = localStorage.getItem('access_token');

            const response = await fetch(
                `${this.API_BASE_URL}/api/v1/browser-automation/quick-apply/prefill?job_id=${jobId}`,
                {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    }
                }
            );

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to load form data');
            }

            const data = await response.json();
            this.currentJobData = data;

            // Update job title in modal
            document.getElementById('quickApplyJobTitle').textContent =
                `${data.job_title} at ${data.company_name}`;

            // Set job ID
            document.getElementById('quickApplyJobId').value = jobId;

            // Prefill form fields
            const form = document.getElementById('quickApplyForm');
            const formData = data.form_data;

            Object.keys(formData).forEach(key => {
                const input = form.querySelector(`[name="${key}"]`);
                if (input && formData[key]) {
                    input.value = formData[key];
                }
            });

            // Set recipient email if available
            if (data.recipient_email) {
                form.querySelector('[name="recipient_email"]').value = data.recipient_email;
            }

        } catch (error) {
            console.error('Error loading prefill data:', error);
            throw error;
        }
    }

    /**
     * Load user's documents for selection
     */
    async loadUserDocuments() {
        try {
            const token = localStorage.getItem('access_token');

            const response = await fetch(
                `${this.API_BASE_URL}/api/v1/documents/`,
                {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                }
            );

            if (!response.ok) {
                throw new Error('Failed to load documents');
            }

            const data = await response.json();
            const documents = data.documents || data || [];

            // Populate CV dropdown
            const cvSelect = document.querySelector('[name="cv_document_id"]');
            const clSelect = document.querySelector('[name="cover_letter_document_id"]');

            cvSelect.innerHTML = '<option value="">Select your CV...</option>';
            clSelect.innerHTML = '<option value="">None</option>';

            documents.forEach(doc => {
                const option = document.createElement('option');
                option.value = doc._id || doc.id;
                option.textContent = doc.filename || doc.original_filename;

                if (doc.document_type === 'cv') {
                    cvSelect.appendChild(option.cloneNode(true));
                } else if (doc.document_type === 'cover_letter') {
                    clSelect.appendChild(option.cloneNode(true));
                }
            });

            // Auto-select first CV if available
            if (cvSelect.options.length > 1) {
                cvSelect.selectedIndex = 1;
            }

        } catch (error) {
            console.error('Error loading documents:', error);
        }
    }

    /**
     * Submit quick apply form
     */
    async submitApplication(event) {
        event.preventDefault();

        try {
            const form = event.target;
            const submitBtn = document.getElementById('quickApplySubmitBtn');
            const loading = document.getElementById('quickApplyLoading');

            // Validate form
            if (!form.checkValidity()) {
                form.reportValidity();
                return;
            }

            // Show loading state
            submitBtn.disabled = true;
            loading.classList.remove('hidden');

            // Collect form data
            const formData = new FormData(form);
            const submission = {
                job_id: formData.get('job_id'),
                recipient_email: formData.get('recipient_email'),
                cv_document_id: formData.get('cv_document_id'),
                cover_letter_document_id: formData.get('cover_letter_document_id') || null,
                additional_message: formData.get('cover_letter') || null,
                form_data: {
                    first_name: formData.get('first_name'),
                    last_name: formData.get('last_name'),
                    email: formData.get('email'),
                    phone: formData.get('phone') || null,
                    address: formData.get('address') || null,
                    city: formData.get('city') || null,
                    state: formData.get('state') || null,
                    postal_code: formData.get('postal_code') || null,
                    linkedin_url: formData.get('linkedin_url') || null,
                    portfolio_url: formData.get('portfolio_url') || null,
                    github_url: formData.get('github_url') || null,
                    cover_letter: formData.get('cover_letter') || null
                }
            };

            // Submit to backend
            const token = localStorage.getItem('access_token');

            const response = await fetch(
                `${this.API_BASE_URL}/api/v1/browser-automation/quick-apply/submit`,
                {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(submission)
                }
            );

            // Check for HTTP errors
            if (!response.ok) {
                if (response.status === 401) {
                    throw new Error('Your session has expired. Please refresh the page and try again.');
                } else if (response.status === 400) {
                    const error = await response.json();
                    throw new Error(error.detail || 'Invalid application data. Please check your inputs.');
                } else if (response.status === 404) {
                    throw new Error('Job not found. It may have been removed.');
                } else {
                    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
                    throw new Error(error.detail || `Server error (${response.status}). Please try again.`);
                }
            }

            const result = await response.json();

            if (result.success) {
                this.showSuccess('Application sent successfully! Check your Gmail sent folder.');
                this.closeQuickApplyForm();

                // Redirect to applications page to track the application
                setTimeout(() => {
                    window.location.href = '/pages/applications.html';
                }, 1500);
            } else {
                throw new Error(result.error || result.message || 'Failed to send application');
            }

        } catch (error) {
            console.error('Error submitting application:', error);
            this.showError(error.message || 'Failed to send application. Please try again.');
        } finally {
            const submitBtn = document.getElementById('quickApplySubmitBtn');
            const loading = document.getElementById('quickApplyLoading');
            submitBtn.disabled = false;
            loading.classList.add('hidden');
        }
    }

    /**
     * Close quick apply form
     */
    closeQuickApplyForm() {
        const modal = document.getElementById('quickApplyModal');
        modal.classList.add('hidden');

        // Reset form
        document.getElementById('quickApplyForm').reset();
        this.currentJobId = null;
        this.currentJobData = null;
    }

    /**
     * Show success message
     */
    showSuccess(message) {
        // Use existing notification system if available
        if (typeof showNotification === 'function') {
            showNotification(message, 'success');
        } else {
            alert(message);
        }
    }

    /**
     * Show error message
     */
    showError(message) {
        // Use existing notification system if available
        if (typeof showNotification === 'function') {
            showNotification(message, 'error');
        } else {
            alert(message);
        }
    }
}

// Initialize manager
const quickApplyManager = new QuickApplyManager();

// Global functions for HTML onclick handlers
function openQuickApplyForm(jobId) {
    quickApplyManager.openQuickApplyForm(jobId);
}

function closeQuickApplyForm() {
    quickApplyManager.closeQuickApplyForm();
}

// Form submission handler
document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('quickApplyForm');
    if (form) {
        form.addEventListener('submit', (e) => quickApplyManager.submitApplication(e));
    }
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = QuickApplyManager;
}
