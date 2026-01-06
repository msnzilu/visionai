/**
 * ContactService - Handles sending emails via the internal Backend API
 */
const ContactService = {
    /**
     * Send email using the Backend API
     * @param {Object} data - Form data object (name, email, subject, category, message)
     * @returns {Promise} Resolves when backend accepts the request
     */
    async sendEmail(data) {
        try {
            const response = await fetch(`${window.CONFIG.API_BASE_URL}${window.CONFIG.API_PREFIX}/support/contact`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify({
                    name: data.name,
                    email: data.email,
                    subject: data.subject,
                    category: data.category || 'General',
                    message: data.message
                })
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.detail || result.message || 'Failed to send message via backend');
            }

            console.log('Contact form submitted successfully via backend');
            return result;
        } catch (error) {
            console.error('Backend Contact Error:', error);
            throw new Error(error.message || 'Failed to connect to the support service.');
        }
    }
};

window.ContactService = ContactService;
