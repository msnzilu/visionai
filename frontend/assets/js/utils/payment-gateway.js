/**
 * CVision Payment Gateway Abstraction Layer
 * 
 * This module provides a unified interface for payment gateways.
 * To switch payment providers, simply create a new adapter that implements
 * the PaymentGateway interface and register it.
 * 
 * Usage:
 *   // Initialize with a provider
 *   await CVision.Payment.init('paystack', { publicKey: 'pk_xxx' });
 *   
 *   // Process a payment
 *   const result = await CVision.Payment.checkout({
 *       email: 'user@example.com',
 *       amount: 2600,  // In base currency units (e.g., cents)
 *       currency: 'KES',
 *       planCode: 'PLN_xxx',  // For subscriptions
 *       metadata: { userId: '123' }
 *   });
 */

(function (global) {
    'use strict';

    // Current active provider
    let activeProvider = null;
    let providerConfig = {};

    /**
     * Base Payment Gateway Interface
     * All payment adapters must implement these methods
     */
    const PaymentGatewayInterface = {
        // Required methods that adapters must implement
        requiredMethods: [
            'init',           // Initialize the provider with config
            'checkout',       // Process a payment/subscription
            'verify',         // Verify a transaction (usually backend)
            'isReady',        // Check if provider is ready
            'getName'         // Get provider name
        ]
    };

    /**
     * Registry of available payment adapters
     */
    const adapters = {};

    /**
     * Payment Gateway Manager
     */
    const Payment = {
        /**
         * Register a payment adapter
         * @param {string} name Provider name (e.g., 'paystack', 'stripe', 'flutterwave')
         * @param {Object} adapter Adapter implementation
         */
        registerAdapter(name, adapter) {
            // Validate adapter implements required methods
            for (const method of PaymentGatewayInterface.requiredMethods) {
                if (typeof adapter[method] !== 'function') {
                    return false;
                }
            }
            adapters[name] = adapter;
            return true;
        },

        /**
         * Initialize a payment provider
         * @param {string} providerName Name of the provider to use
         * @param {Object} config Provider-specific configuration
         * @returns {Promise<boolean>} Success status
         */
        async init(providerName, config = {}) {
            const adapter = adapters[providerName];
            if (!adapter) {
                console.error(`[Payment] Unknown provider: ${providerName}`);
                console.log(`[Payment] Available providers: ${Object.keys(adapters).join(', ')}`);
                return false;
            }

            try {
                await adapter.init(config);
                activeProvider = adapter;
                providerConfig = config;
                return true;
            } catch (error) {
                return false;
            }
        },

        /**
         * Process a payment or subscription checkout
         * @param {Object} options Checkout options
         * @param {string} options.email Customer email
         * @param {number} options.amount Amount in smallest currency unit
         * @param {string} options.currency Currency code (e.g., 'KES', 'USD')
         * @param {string} [options.planCode] Subscription plan code (for recurring)
         * @param {string} [options.reference] Custom transaction reference
         * @param {Object} [options.metadata] Additional metadata
         * @param {Function} [options.onSuccess] Success callback
         * @param {Function} [options.onCancel] Cancel callback
         * @param {Function} [options.onError] Error callback
         * @returns {Promise<Object>} Transaction result
         */
        async checkout(options) {
            if (!activeProvider) {
                throw new Error('No payment provider initialized. Call Payment.init() first.');
            }

            if (!activeProvider.isReady()) {
                throw new Error('Payment provider not ready.');
            }

            // Generate reference if not provided
            if (!options.reference) {
                options.reference = this.generateReference();
            }

            console.log(`[Payment] Starting checkout with ${activeProvider.getName()}`, {
                email: options.email,
                amount: options.amount,
                currency: options.currency,
                reference: options.reference
            });

            return activeProvider.checkout(options);
        },

        /**
         * Verify a transaction (typically done on backend)
         * @param {string} reference Transaction reference
         * @returns {Promise<Object>} Verification result
         */
        async verify(reference) {
            if (!activeProvider) {
                throw new Error('No payment provider initialized.');
            }
            return activeProvider.verify(reference);
        },

        /**
         * Check if payment system is ready
         * @returns {boolean}
         */
        isReady() {
            return activeProvider !== null && activeProvider.isReady();
        },

        /**
         * Get current provider name
         * @returns {string|null}
         */
        getProviderName() {
            return activeProvider ? activeProvider.getName() : null;
        },

        /**
         * Get list of registered adapters
         * @returns {string[]}
         */
        getAvailableProviders() {
            return Object.keys(adapters);
        },

        /**
         * Generate a unique transaction reference
         * @param {string} [prefix] Optional prefix
         * @returns {string}
         */
        generateReference(prefix = 'TXN') {
            const timestamp = Date.now();
            const random = Math.random().toString(36).substring(2, 10).toUpperCase();
            return `${prefix}${timestamp}${random}`;
        },

        /**
         * Switch to a different payment provider
         * @param {string} providerName New provider name
         * @param {Object} config Provider configuration
         * @returns {Promise<boolean>}
         */
        async switchProvider(providerName, config = {}) {
            console.log(`[Payment] Switching from ${this.getProviderName()} to ${providerName}`);
            return this.init(providerName, config);
        }
    };

    // Expose to global CVision namespace
    global.CVision = global.CVision || {};
    global.CVision.Payment = Payment;
    global.CVision.PaymentGatewayInterface = PaymentGatewayInterface;

})(typeof window !== 'undefined' ? window : this);
