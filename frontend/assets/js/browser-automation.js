const BrowserAutomation = {

    get API_BASE_URL() {
        return CONFIG.API_BASE_URL;
    },

    /**
     * Start browser automation for a job application
     */
    async startAutofill(jobId, cvId = null, coverLetterId = null) {
        console.group('🤖 Browser Automation Start');
        console.log('Job ID:', jobId);
        console.log('CV ID:', cvId);
        console.log('Cover Letter ID:', coverLetterId);
        console.log('API Base URL:', this.API_BASE_URL);

        try {
            const token = CVision.Utils.getToken();
            if (!token) {
                console.error('❌ No authentication token found');
                throw new Error('Not authenticated. Please login again.');
            }
            console.log('✅ Token found:', token.substring(0, 20) + '...');

            // Show loading state
            CVision.Utils.showAlert('Starting browser automation...', 'info');

            const url = `${this.API_BASE_URL}/api/v1/browser-automation/autofill/start`;
            const payload = {
                job_id: jobId,
                cv_id: cvId,
                cover_letter_id: coverLetterId
            };

            console.log('📤 Request URL:', url);
            console.log('📤 Request Payload:', payload);

            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(payload)
            });

            console.log('📥 Response Status:', response.status, response.statusText);
            console.log('📥 Response Headers:', Object.fromEntries(response.headers.entries()));

            // Try to get response body regardless of status
            let responseData;
            const contentType = response.headers.get('content-type');

            if (contentType && contentType.includes('application/json')) {
                responseData = await response.json();
                console.log('📥 Response Data:', responseData);
            } else {
                const text = await response.text();
                console.log('📥 Response Text:', text);
                responseData = { detail: text || 'Unknown error' };
            }

            if (!response.ok) {
                console.error('❌ Request failed:', response.status);
                console.error('❌ Error details:', responseData);

                // Provide more specific error messages
                let errorMessage = 'Failed to start browser automation';

                if (response.status === 401) {
                    errorMessage = 'Authentication failed. Please login again.';
                } else if (response.status === 404) {
                    errorMessage = 'Browser automation service not found. Please contact support.';
                } else if (response.status === 422) {
                    errorMessage = `Invalid data: ${responseData.detail || 'Please check your inputs'}`;
                } else if (response.status === 503) {
                    errorMessage = 'Browser automation service is unavailable. Please try again later.';
                } else if (responseData.detail) {
                    errorMessage = responseData.detail;
                }

                throw new Error(errorMessage);
            }

            console.log('✅ Automation started successfully');
            console.log('Session ID:', responseData.session_id);

            CVision.Utils.showAlert(
                'Browser window opened! Your information is being filled automatically.',
                'success'
            );

            // Poll for status updates
            if (responseData.session_id) {
                this.pollAutofillStatus(responseData.session_id);
            }

            console.groupEnd();
            return responseData;

        } catch (error) {
            console.error('💥 Browser automation error:', error);
            console.error('Error stack:', error.stack);
            console.groupEnd();

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
        console.log('🔄 Starting status polling for session:', sessionId);
        let attempts = 0;

        const checkStatus = async () => {
            try {
                const token = CVision.Utils.getToken();
                const url = `${this.API_BASE_URL}/api/v1/browser-automation/autofill/status/${sessionId}`;

                console.log(`📡 Status check ${attempts + 1}/${maxAttempts}:`, url);

                const response = await fetch(url, {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });

                if (response.ok) {
                    const status = await response.json();
                    console.log('📊 Status:', status);

                    if (status.status === 'completed') {
                        CVision.Utils.showAlert(
                            `Successfully filled ${status.filled_fields?.length || 0} fields!`,
                            'success'
                        );
                        console.log('✅ Automation completed');
                        return true;
                    } else if (status.status === 'error') {
                        CVision.Utils.showAlert(
                            'Some fields could not be filled automatically. Please complete them manually.',
                            'warning'
                        );
                        console.warn('⚠️ Automation completed with errors');
                        return true;
                    }
                }

                attempts++;
                if (attempts < maxAttempts) {
                    setTimeout(checkStatus, 2000); // Check every 2 seconds
                } else {
                    console.warn('⏱️ Status polling timeout');
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