/**
 * Stripe Payment Adapter
 * 
 * Implementation of the PaymentGateway interface for Stripe at CVision.
 * 
 * NOTE: This adapter uses Stripe Checkout (redirect flow), which differs
 * slightly from Paystack's popup flow. The abstraction handles this transparently.
 * 
 * Usage:
 *   await CVision.Payment.init('stripe', { publicKey: 'pk_test_...' });
 *   
 *   await CVision.Payment.checkout({
 *       email: 'user@example.com',
 *       amount: 2000,  // In cents
 *       currency: 'USD',
 *       onSuccess: (result) => console.log('Redirecting to Stripe...'),
 *       onCancel: () => console.log('Cancelled')
 *   });
 */

(function (global) {
    'use strict';

    let stripe = null;
    let publicKey = null;
    let isInitialized = false;

    /**
     * Stripe Adapter Implementation
     */
    const StripeAdapter = {
        /**
         * Initialize Stripe with public key
         * @param {Object} config Configuration object
         * @param {string} config.publicKey Stripe publishable key
         */
        async init(config) {
            if (!config.publicKey) {
                throw new Error('Stripe public key is required');
            }

            publicKey = config.publicKey;

            // Load Stripe.js if not present
            if (typeof Stripe === 'undefined') {
                await this._loadStripeScript();
            }

            // Initialize Stripe instance
            if (typeof Stripe !== 'undefined') {
                stripe = Stripe(publicKey);
                isInitialized = true;
                console.log('[Stripe] Initialized successfully');
            } else {
                throw new Error('Failed to initialize Stripe client');
            }
        },

        /**
         * Load Stripe.js script dynamically
         */
        async _loadStripeScript() {
            return new Promise((resolve, reject) => {
                if (typeof Stripe !== 'undefined') {
                    resolve();
                    return;
                }

                const script = document.createElement('script');
                script.src = 'https://js.stripe.com/v3/';
                script.async = true;
                script.onload = () => {
                    console.log('[Stripe] Script loaded dynamically');
                    resolve();
                };
                script.onerror = () => reject(new Error('Failed to load Stripe script'));
                document.head.appendChild(script);
            });
        },

        /**
         * Process checkout using Stripe Checkout (Redirect)
         * @param {Object} options Checkout options
         */
        async checkout(options) {
            if (!isInitialized || !stripe) {
                throw new Error('Stripe not initialized');
            }

            const {
                email,
                amount,
                currency = 'USD',
                planCode, // Typically a Price ID for Stripe (e.g., price_12345)
                reference,
                metadata = {},
                onSuccess,
                onError
            } = options;

            console.log('[Stripe] Initiating checkout redirect...', { email, amount, currency });

            try {
                // For Stripe, we typically need to create a Checkout Session on the backend first
                // However, for client-only demos or specific setups, we might redirect differently.
                // Assuming standard flow: Call backend to create session, then redirect.

                // NOTE: This part requires a backend endpoint compliant with Stripe's flow.
                // Replace '/api/v1/stripe/create-checkout-session' with your actual endpoint.
                const response = await fetch('/api/v1/stripe/create-checkout-session', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${CVision.Utils.getToken()}` // Assuming auth needed
                    },
                    body: JSON.stringify({
                        email,
                        priceId: planCode, // Stripe uses Price IDs for subscriptions
                        amount: amount,    // For one-time payments
                        currency: currency,
                        reference: reference, // Pass our internal ref
                        metadata
                    })
                });

                if (!response.ok) {
                    throw new Error('Failed to create Stripe checkout session');
                }

                const session = await response.json();

                // Redirect to Stripe Checkout
                const result = await stripe.redirectToCheckout({
                    sessionId: session.id
                });

                if (result.error) {
                    throw new Error(result.error.message);
                }

                // If successful, the user is redirected away, so onSuccess might not technically trigger here
                // unless we're using a specific embedded flow.
                // We'll call it just in case logic continues.
                if (onSuccess) onSuccess({ status: 'redirecting', provider: 'stripe' });

            } catch (error) {
                console.error('[Stripe] Checkout error:', error);
                if (onError) onError(error);
                throw error;
            }
        },

        /**
         * Verify transaction (Backend verification recommended)
         * @param {string} reference Transaction reference
         */
        async verify(reference) {
            // Stripe verification usually happens via Webhook or retrieving the session on success page
            return {
                reference: reference,
                provider: 'stripe',
                status: 'pending_verification'
            };
        },

        /**
         * Check if Stripe is ready
         * @returns {boolean}
         */
        isReady() {
            return isInitialized && stripe !== null;
        },

        /**
         * Get adapter name
         * @returns {string}
         */
        getName() {
            return 'stripe';
        },

        /**
         * Get features
         */
        getFeatures() {
            return {
                subscriptions: true,
                oneTimePayments: true,
                cards: true,
                currencies: ['USD', 'EUR', 'GBP', 'KES', 'ZAR', 'NGN']
                // Note: Stripe supports many currencies, but settlement might require conversion
            };
        }
    };

    // Auto-register if CVision.Payment exists, else wait
    if (global.CVision && global.CVision.Payment) {
        global.CVision.Payment.registerAdapter('stripe', StripeAdapter);
    } else {
        global._stripeAdapter = StripeAdapter;
        const checkAndRegister = setInterval(() => {
            if (global.CVision && global.CVision.Payment) {
                global.CVision.Payment.registerAdapter('stripe', StripeAdapter);
                delete global._stripeAdapter;
                clearInterval(checkAndRegister);
            }
        }, 100);
        setTimeout(() => clearInterval(checkAndRegister), 5000);
    }

    // Expose directly
    global.CVision = global.CVision || {};
    global.CVision.StripeAdapter = StripeAdapter;

})(typeof window !== 'undefined' ? window : this);
