// frontend/assets/js/browser-automation.js

const BrowserAutomation = {
    API_BASE_URL: 'http://localhost:8000',
    
    /**
     * Start browser automation for a job application
     */
    async startAutofill(jobId, cvId = null, coverLetterId = null) {
        try {
            const token = CVision.Utils.getToken();
            if (!token) {
                throw new Error('Not authenticated');
            }
            
            // Show loading state
            CVision.Utils.showAlert('Starting browser automation...', 'info');
            
            const response = await fetch(`${this.API_BASE_URL}/api/v1/browser-automation/autofill/start`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    job_id: jobId,
                    cv_id: cvId,
                    cover_letter_id: coverLetterId
                })
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to start browser automation');
            }
            
            const result = await response.json();
            
            CVision.Utils.showAlert(
                'Browser window opened! Your information is being filled automatically.',
                'success'
            );
            
            // Poll for status updates
            this.pollAutofillStatus(result.session_id);
            
            return result;
            
        } catch (error) {
            console.error('Browser automation error:', error);
            CVision.Utils.showAlert(
                error.message || 'Failed to start browser automation',
                'error'
            );
            throw error;
        }
    },
    
    /**
     * Poll for autofill session status
     */
    async pollAutofillStatus(sessionId, maxAttempts = 30) {
        let attempts = 0;
        
        const checkStatus = async () => {
            try {
                const token = CVision.Utils.getToken();
                const response = await fetch(
                    `${this.API_BASE_URL}/api/v1/browser-automation/autofill/status/${sessionId}`,
                    {
                        headers: {
                            'Authorization': `Bearer ${token}`
                        }
                    }
                );
                
                if (response.ok) {
                    const status = await response.json();
                    
                    if (status.status === 'completed') {
                        CVision.Utils.showAlert(
                            `Successfully filled ${status.filled_fields.length} fields!`,
                            'success'
                        );
                        return true;
                    } else if (status.status === 'error') {
                        CVision.Utils.showAlert(
                            'Some fields could not be filled automatically. Please complete them manually.',
                            'warning'
                        );
                        return true;
                    }
                }
                
                attempts++;
                if (attempts < maxAttempts) {
                    setTimeout(checkStatus, 2000); // Check every 2 seconds
                }
                
            } catch (error) {
                console.error('Status check error:', error);
            }
        };
        
        checkStatus();
    },
    
    /**
     * Submit feedback for ML training
     */
    async submitFeedback(sessionId, corrections) {
        try {
            const token = CVision.Utils.getToken();
            const response = await fetch(
                `${this.API_BASE_URL}/api/v1/browser-automation/autofill/feedback/${sessionId}`,
                {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    },
                    body: JSON.stringify(corrections)
                }
            );
            
            if (response.ok) {
                CVision.Utils.showAlert('Feedback submitted successfully', 'success');
            }
            
        } catch (error) {
            console.error('Feedback submission error:', error);
        }
    }
};

// Make available globally
window.BrowserAutomation = BrowserAutomation;