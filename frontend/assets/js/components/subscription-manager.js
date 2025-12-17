/**
 * SubscriptionManager Component
 * Centralizes logic for handling subscription upgrades and backend verification after payment.
 * Dependencies: CVision.Utils
 */
class SubscriptionManagerService {
    constructor() {
        // Use global CONFIG if available, otherwise relative path
        this.apiBase = (typeof CONFIG !== 'undefined' && CONFIG.API_BASE_URL) ? CONFIG.API_BASE_URL : '';
    }

    /**
     * Verifies the payment/subscription with the backend.
     * @param {string} planId - The ID of the plan subscribed to.
     * @param {string} reference - The payment transaction reference.
     * @param {string} [referralCode] - Optional referral code.
     * @returns {Promise<Object>} - The backend response data.
     */
    async verifyUpgrade(planId, reference, referralCode) {
        const token = CVision.Utils.getToken();
        if (!token) {
            throw new Error('Authentication required');
        }

        const response = await fetch(`${this.apiBase}/api/v1/subscriptions/`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                plan_id: planId,
                reference: reference,
                referral_code: referralCode
            })
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: 'Subscription verification failed' }));
            throw new Error(error.detail || 'Subscription verification failed');
        }

        return await response.json();
    }

    /**
     * Handles the complete post-payment success flow: verification, notifications, and redirect.
     * @param {Object} paymentResult - Result object from Payment Gateway.
     * @param {Object} plan - The plan object (must have .id).
     * @param {string} [referralCode] - Optional referral code.
     * @param {Function} [onSuccess] - Optional callback to run after success (before reload).
     */
    async handlePaymentSuccess(paymentResult, plan, referralCode, onSuccess) {
        try {
            console.log('Verifying subscription upgrade...', { reference: paymentResult.reference, planId: plan.id });

            await this.verifyUpgrade(plan.id, paymentResult.reference, referralCode);

            // Refresh user data to ensure local storage has latest subscription tier
            if (window.CVision && window.CVision.API && window.CVision.Utils) {
                try {
                    // Force token refresh to get updated claims (tier)
                    console.log('Refreshing access token...');
                    await CVision.API.refreshAccessToken();

                    console.log('Refreshing user profile...');
                    const userProfile = await CVision.API.getProfile();
                    if (userProfile && userProfile.id) {
                        CVision.Utils.setUser(userProfile);
                        console.log('User profile updated in local storage', userProfile);
                    }
                } catch (profileError) {
                    console.warn('Failed to refresh user profile:', profileError);
                }
            }

            if (onSuccess) onSuccess();

            CVision.Utils.showAlert('Subscription successful! Upgrading your account...', 'success');

            // Short delay before reload to allow user to see success message
            setTimeout(() => {
                window.location.reload();
            }, 2000);

        } catch (error) {
            console.error('Backend verification failed:', error);
            CVision.Utils.showAlert(error.message || 'Verification failed. Please contact support.', 'error');
            throw error; // Re-throw to allow caller to handle button states if needed
        }
    }
}

// Expose globally
window.SubscriptionManager = new SubscriptionManagerService();
