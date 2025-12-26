/**
 * BrowserAutomationManager.js
 * 
 * Reusable component for handling Playwright-based browser automation.
 * Manages:
 * - Session initiation
 * - Real-time status polling
 * - User-facing log messages
 * - Error handling and recovery
 */
class BrowserAutomationManager {
    constructor() {
        this.activeSessions = new Map();
        this.pollIntervals = new Map();
    }

    get API_BASE_URL() {
        return `${window.CONFIG?.API_BASE_URL || ''}${window.CONFIG?.API_PREFIX || '/api/v1'}`;
    }

    /**
     * Start browser automation for a job application
     * @param {string} jobId - The ID of the job to apply for
     * @param {string} cvId - The ID of the CV to use
     * @param {string} coverLetterId - Optional cover letter ID
     */
    async startAutofill(jobId, cvId, coverLetterId = null) {
        console.group(`🤖 [Browser Automation] Starting for Job: ${jobId}`);
        console.log('Selected CV:', cvId);
        console.log('Selected CL:', coverLetterId);

        try {
            const token = CVision.Utils.getToken();
            if (!token) throw new Error('Authentication required.');

            // Notify user
            CVision.Utils.showAlert('Initiating automated application...', 'info');

            const url = `${this.API_BASE_URL}/browser-automation/autofill/start`;
            const payload = {
                job_id: jobId,
                cv_id: cvId,
                cover_letter_id: coverLetterId
            };

            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(payload)
            });

            const data = await response.json();

            if (!response.ok) {
                console.error('❌ Initiation failed:', data);
                throw new Error(data.detail || 'Failed to start automation');
            }

            console.log('✅ Automation started. Session ID:', data.session_id);

            CVision.Utils.showAlert(
                'Automation engine warmed up! Check the dashboard for progress.',
                'success'
            );

            // Start polling if we have a session ID
            if (data.session_id) {
                this.pollStatus(data.session_id);
            }

            console.groupEnd();
            return data;

        } catch (error) {
            console.error('💥 [Browser Automation] Error:', error);
            CVision.Utils.showAlert(error.message, 'error');
            console.groupEnd();
            throw error;
        }
    }

    /**
     * Poll the backend for automation status
     * @param {string} sessionId 
     */
    pollStatus(sessionId) {
        if (this.pollIntervals.has(sessionId)) return;

        console.log(`📡 [Browser Automation] Polling started for session: ${sessionId}`);

        const intervalId = setInterval(async () => {
            try {
                const token = CVision.Utils.getToken();
                const url = `${this.API_BASE_URL}/browser-automation/autofill/status/${sessionId}`;

                const response = await fetch(url, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });

                if (!response.ok) throw new Error('Status check failed');

                const statusData = await response.json();
                this._handleStatusUpdate(sessionId, statusData);

            } catch (error) {
                console.error(`📡 Polling error for ${sessionId}:`, error);
                this.stopPolling(sessionId);
            }
        }, 3000); // Poll every 3 seconds

        this.pollIntervals.set(sessionId, intervalId);
    }

    /**
     * Handle status updates and stop polling on completion/error
     */
    _handleStatusUpdate(sessionId, data) {
        const { status, filled_fields, error } = data;
        console.log(`📊 [Automation Status] ${sessionId}: ${status}`, data);

        // Update UI or provide feedback based on status
        if (status === 'navigating') {
            CVision.Utils.showAlert('Browser: Navigating to job page...', 'info');
        } else if (status === 'filling_forms') {
            CVision.Utils.showAlert(`Browser: Filling forms (${filled_fields?.length || 0} fields)...`, 'info');
        } else if (status === 'completed') {
            CVision.Utils.showAlert('Automated application ready! Please review and submit.', 'success');
            this.stopPolling(sessionId);
        } else if (status === 'failed') {
            CVision.Utils.showAlert(`Automation Error: ${error || 'Unknown error'}`, 'error');
            this.stopPolling(sessionId);
        }
    }

    stopPolling(sessionId) {
        const intervalId = this.pollIntervals.get(sessionId);
        if (intervalId) {
            clearInterval(intervalId);
            this.pollIntervals.delete(sessionId);
            console.log(`🛑 [Browser Automation] Polling stopped for ${sessionId}`);
        }
    }
}

// Global initialization
window.BrowserAutomation = new BrowserAutomationManager();
