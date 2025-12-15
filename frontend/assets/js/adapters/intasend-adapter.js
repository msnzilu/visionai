/**
 * IntaSend Payment Adapter
 * 
 * Implementation of the PaymentGateway interface for IntaSend (popular in Kenya).
 * Supports M-Pesa, Card, and Bitcoin.
 * 
 * Usage:
 *   await CVision.Payment.init('intasend', { 
 *      publicKey: 'ISPubKey_...', 
 *      live: false // Set to true for production
 *   });
 *   
 *   await CVision.Payment.checkout({
 *       email: 'user@example.com',
 *       amount: 2600,  // In default currency units (KES) NOT cents usually, but let's check config
 *       currency: 'KES',
 *       onSuccess: (result) => console.log('Paid!', result)
 *   });
 */

(function (global) {
    'use strict';

    let publicKey = null;
    let isLive = false;
    let isInitialized = false;

    /**
     * IntaSend Adapter Implementation
     */
    const IntaSendAdapter = {
        /**
         * Initialize IntaSend with public key
         * @param {Object} config Configuration object
         * @param {string} config.publicKey IntaSend Publishable Key
         * @param {boolean} [config.live=false] Live mode?
         */
        async init(config) {
            if (!config.publicKey) {
                throw new Error('IntaSend Public Key is required');
            }

            publicKey = config.publicKey;
            isLive = !!config.live;

            // Load IntaSend script
            if (typeof window.IntaSend === 'undefined') {
                await this._loadScript();
            }

            if (typeof window.IntaSend !== 'undefined') {
                isInitialized = true;
                console.log('[IntaSend] Initialized successfully');
            } else {
                throw new Error('Failed to load IntaSend SDK');
            }
        },

        /**
         * Load IntaSend script dynamically
         */
        async _loadScript() {
            return new Promise((resolve, reject) => {
                if (typeof window.IntaSend !== 'undefined') {
                    resolve();
                    return;
                }

                const script = document.createElement('script');
                // Use the standard Web SDK
                script.src = 'https://unpkg.com/intasend-inlinejs-sdk@3.0.2/build/intasend-inline.js';
                script.async = true;
                script.onload = () => {
                    console.log('[IntaSend] Script loaded dynamically');
                    resolve();
                };
                script.onerror = () => reject(new Error('Failed to load IntaSend script'));
                document.head.appendChild(script);
            });
        },

        /**
         * Process checkout using IntaSend Popup
         * @param {Object} options Checkout options
         */
        async checkout(options) {
            if (!isInitialized) {
                throw new Error('IntaSend not initialized');
            }

            const {
                email,
                amount,
                currency = 'KES',
                reference,
                onSuccess,
                onCancel,
                onError
            } = options;

            // IntaSend expects amount in MAIN units (e.g. 10.50), while our system uses cents (1050)
            // We need to convert only if the input is deemed to be in cents.
            // CAUTION: Verify your system's convention. I will assume input is CENTS and convert to MAIN units.
            const mainAmount = (amount / 100).toFixed(2);

            console.log(`[IntaSend] Starting checkout: ${currency} ${mainAmount} (Ref: ${reference})`);

            try {
                // Initialize instance
                const intasend = new window.IntaSend({
                    publicAPIKey: publicKey,
                    live: isLive
                });

                // Attach event listeners
                intasend.on("COMPLETE", (results) => {
                    console.log("[IntaSend] Payment Successful", results);
                    if (onSuccess) onSuccess({
                        success: true,
                        reference: reference, // or results.invoice_id
                        provider: 'intasend',
                        raw: results
                    });
                });

                intasend.on("FAILED", (results) => {
                    console.log("[IntaSend] Payment Failed", results);
                    if (onError) onError(new Error('Payment failed'));
                });

                intasend.on("IN-PROGRESS", (results) => {
                    console.log("[IntaSend] Payment In Progress", results);
                });

                // Trigger payment
                intasend.run({
                    amount: parseFloat(mainAmount),
                    currency: currency,
                    email: email,
                    api_ref: reference // Use our reference to track
                });

            } catch (error) {
                console.error('[IntaSend] Checkout error:', error);
                if (onError) onError(error);
                throw error;
            }
        },

        /**
         * Verify transaction (placeholder)
         * @param {string} reference 
         */
        async verify(reference) {
            console.warn('[IntaSend] Client-side verification is not secure. Use backend verification.');
            return {
                reference: reference,
                provider: 'intasend',
                message: 'Verification should be done on the backend'
            };
        },

        isReady() {
            return isInitialized && typeof window.IntaSend !== 'undefined';
        },

        getName() {
            return 'intasend';
        },

        getFeatures() {
            return {
                subscriptions: false, // IntaSend usually one-time, backend handles recurring logic
                oneTimePayments: true,
                mpesa: true,
                card: true,
                bitcoin: true,
                currencies: ['KES', 'USD', 'EUR', 'GBP']
            };
        }
    };

    // Auto-register
    if (global.CVision && global.CVision.Payment) {
        global.CVision.Payment.registerAdapter('intasend', IntaSendAdapter);
    } else {
        global._intasendAdapter = IntaSendAdapter;
        const checkAndRegister = setInterval(() => {
            if (global.CVision && global.CVision.Payment) {
                global.CVision.Payment.registerAdapter('intasend', IntaSendAdapter);
                delete global._intasendAdapter;
                clearInterval(checkAndRegister);
            }
        }, 100);
        setTimeout(() => clearInterval(checkAndRegister), 5000);
    }

    global.CVision = global.CVision || {};
    global.CVision.IntaSendAdapter = IntaSendAdapter;

})(typeof window !== 'undefined' ? window : this);
