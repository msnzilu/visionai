/**
 * PayPal Payment Adapter
 * 
 * Implementation of the PaymentGateway interface for PayPal.
 * Uses the PayPal JavaScript SDK.
 * 
 * Usage:
 *   await CVision.Payment.init('paypal', { clientId: 'sb-...' });
 *   
 *   await CVision.Payment.checkout({
 *       email: 'user@example.com',
 *       amount: 2000,  // In cents
 *       currency: 'USD',
 *       onSuccess: (result) => console.log('Paid!', result)
 *   });
 */

(function (global) {
    'use strict';

    let clientId = null;
    let isInitialized = false;

    /**
     * PayPal Adapter Implementation
     */
    const PayPalAdapter = {
        /**
         * Initialize PayPal with client ID
         * @param {Object} config Configuration object
         * @param {string} config.clientId PayPal Client ID
         * @param {string} [config.currency='USD'] Default currency
         */
        async init(config) {
            if (!config.clientId) {
                throw new Error('PayPal Client ID is required');
            }

            clientId = config.clientId;
            const currency = config.currency || 'USD';

            // Load PayPal SDK if not present
            if (typeof paypal === 'undefined') {
                await this._loadPayPalScript(clientId, currency);
            }

            if (typeof paypal !== 'undefined') {
                isInitialized = true;
                console.log('[PayPal] Initialized successfully');
            } else {
                throw new Error('Failed to load PayPal SDK');
            }
        },

        /**
         * Load PayPal script dynamically
         */
        async _loadPayPalScript(clientId, currency) {
            return new Promise((resolve, reject) => {
                if (typeof paypal !== 'undefined') {
                    resolve();
                    return;
                }

                const script = document.createElement('script');
                // Standard default configuration
                script.src = `https://www.paypal.com/sdk/js?client-id=${clientId}&currency=${currency}&intent=capture`;
                script.async = true;
                script.onload = () => {
                    console.log('[PayPal] Script loaded dynamically');
                    resolve();
                };
                script.onerror = () => reject(new Error('Failed to load PayPal script'));
                document.head.appendChild(script);
            });
        },

        /**
         * Process checkout using PayPal Buttons
         * NOTE: PayPal usually renders specific buttons.
         * For this abstraction, we might need to render a modal with the buttons,
         * or expect a container ID in options.metadata.containerId
         * 
         * @param {Object} options Checkout options
         */
        async checkout(options) {
            if (!isInitialized || typeof paypal === 'undefined') {
                throw new Error('PayPal not initialized');
            }

            const {
                amount,
                currency = 'USD',
                onSuccess,
                onCancel,
                onError,
                metadata = {}
            } = options;

            // PayPal amounts are usually in major units (e.g. 20.00), not cents
            // We need to convert from our system's "base unit" (cents) to major unit
            const majorAmount = (amount / 100).toFixed(2);

            console.log(`[PayPal] Starting checkout: ${currency} ${majorAmount}`);

            // If a container is provided, render buttons there
            if (metadata.containerId) {
                return this._renderButtons(metadata.containerId, majorAmount, currency, onSuccess, onCancel, onError);
            }

            // If no container, we must create a modal overlay
            return this._renderModal(majorAmount, currency, onSuccess, onCancel, onError);
        },

        /**
         * Render PayPal buttons into a container
         */
        async _renderButtons(containerId, amount, currency, onSuccess, onCancel, onError) {
            // Clear container
            const container = document.getElementById(containerId);
            if (!container) throw new Error(`Container #${containerId} not found`);
            container.innerHTML = '';

            try {
                await paypal.Buttons({
                    // Set up the transaction
                    createOrder: function (data, actions) {
                        return actions.order.create({
                            purchase_units: [{
                                amount: {
                                    value: amount,
                                    currency_code: currency
                                }
                            }]
                        });
                    },
                    // Finalize the transaction
                    onApprove: function (data, actions) {
                        return actions.order.capture().then(function (details) {
                            console.log('[PayPal] Transaction completed by ' + details.payer.name.given_name);
                            if (onSuccess) onSuccess({
                                success: true,
                                reference: data.orderID,
                                provider: 'paypal',
                                raw: details
                            });
                        });
                    },
                    onCancel: function (data) {
                        if (onCancel) onCancel(data);
                    },
                    onError: function (err) {
                        console.error('[PayPal] Error:', err);
                        if (onError) onError(err);
                    }
                }).render(`#${containerId}`);
            } catch (error) {
                if (onError) onError(error);
                throw error;
            }
        },

        /**
         * Render a modal overlay for the buttons (default behavior)
         */
        async _renderModal(amount, currency, onSuccess, onCancel, onError) {
            // Create modal DOM
            const modalId = 'cv-paypal-modal';
            let modal = document.getElementById(modalId);

            if (!modal) {
                modal = document.createElement('div');
                modal.id = modalId;
                modal.style.cssText = `
                    position: fixed; top: 0; left: 0; width: 100%; height: 100%;
                    background: rgba(0,0,0,0.5); z-index: 9999;
                    display: flex; align-items: center; justify-content: center;
                `;
                modal.innerHTML = `
                    <div style="background: white; padding: 20px; border-radius: 8px; width: 300px; position: relative;">
                        <button id="cv-paypal-close" style="position: absolute; top: 10px; right: 10px; border: none; background: none; font-size: 20px; cursor: pointer;">&times;</button>
                        <h3 style="margin-top: 0; margin-bottom: 20px; text-align: center;">Pay with PayPal</h3>
                        <div id="cv-paypal-buttons"></div>
                    </div>
                `;
                document.body.appendChild(modal);

                document.getElementById('cv-paypal-close').onclick = () => {
                    modal.style.display = 'none';
                    if (onCancel) onCancel({ reason: 'closed_modal' });
                };
            } else {
                modal.style.display = 'flex';
            }

            // Render buttons into the modal
            return this._renderButtons('cv-paypal-buttons', amount, currency,
                (result) => {
                    modal.style.display = 'none';
                    onSuccess(result);
                },
                (data) => {
                    modal.style.display = 'none';
                    onCancel(data);
                },
                (err) => {
                    modal.style.display = 'none';
                    onError(err);
                }
            );
        },

        /**
         * Verify transaction (placeholder)
         * @param {string} reference 
         */
        async verify(reference) {
            console.warn('[PayPal] Client-side verification is not secure. Use backend verification.');
            return {
                reference: reference,
                provider: 'paypal',
                message: 'Verification should be done on the backend'
            };
        },

        isReady() {
            return isInitialized && typeof paypal !== 'undefined';
        },

        getName() {
            return 'paypal';
        },

        getFeatures() {
            return {
                subscriptions: true,
                oneTimePayments: true,
                currencies: ['USD', 'GBP', 'EUR', 'AUD', 'CAD']
            };
        }
    };

    // Auto-register
    if (global.CVision && global.CVision.Payment) {
        global.CVision.Payment.registerAdapter('paypal', PayPalAdapter);
    } else {
        global._paypalAdapter = PayPalAdapter;
        const checkAndRegister = setInterval(() => {
            if (global.CVision && global.CVision.Payment) {
                global.CVision.Payment.registerAdapter('paypal', PayPalAdapter);
                delete global._paypalAdapter;
                clearInterval(checkAndRegister);
            }
        }, 100);
        setTimeout(() => clearInterval(checkAndRegister), 5000);
    }

    global.CVision = global.CVision || {};
    global.CVision.PayPalAdapter = PayPalAdapter;

})(typeof window !== 'undefined' ? window : this);
