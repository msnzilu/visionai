/**
 * CVision Currency Utility
 * Handles currency conversion, formatting, and display
 * 
 * Usage:
 *   CVision.Currency.setBaseCurrency('KES');
 *   CVision.Currency.setUserCurrency('USD');
 *   const formatted = CVision.Currency.format(260000);  // "$20.02"
 *   const converted = CVision.Currency.convert(260000); // 20.02
 */

(function (global) {
    'use strict';

    // Base currency (what prices are stored in)
    let baseCurrency = 'KES';

    // User's display currency
    let userCurrency = 'KES';

    // Exchange rates FROM base currency (KES)
    // In production, these should be fetched from an API
    const EXCHANGE_RATES = {
        // Base
        'KES': 1,

        // Major currencies (rates from KES)
        'USD': 0.0077,     // 1 KES ≈ $0.0077 (1 USD ≈ 130 KES)
        'EUR': 0.0071,     // 1 KES ≈ €0.0071
        'GBP': 0.0061,     // 1 KES ≈ £0.0061
        'CAD': 0.0105,     // 1 KES ≈ C$0.0105
        'AUD': 0.012,      // 1 KES ≈ A$0.012
        'CHF': 0.0068,     // 1 KES ≈ CHF0.0068

        // African currencies
        'NGN': 12.0,       // 1 KES ≈ ₦12
        'ZAR': 0.14,       // 1 KES ≈ R0.14
        'GHS': 0.095,      // 1 KES ≈ GH₵0.095
        'UGX': 28.5,       // 1 KES ≈ UGX28.5
        'TZS': 19.5,       // 1 KES ≈ TZS19.5
        'RWF': 9.8,        // 1 KES ≈ RWF9.8
        'ETB': 0.44,       // 1 KES ≈ ETB0.44
        'EGP': 0.38,       // 1 KES ≈ EGP0.38
        'MAD': 0.077,      // 1 KES ≈ MAD0.077

        // Asian currencies
        'INR': 0.64,       // 1 KES ≈ ₹0.64
        'CNY': 0.055,      // 1 KES ≈ ¥0.055
        'JPY': 1.15,       // 1 KES ≈ ¥1.15
        'KRW': 10.2,       // 1 KES ≈ ₩10.2
        'SGD': 0.0103,     // 1 KES ≈ S$0.0103
        'AED': 0.028,      // 1 KES ≈ AED0.028
        'SAR': 0.029,      // 1 KES ≈ SAR0.029
        'PKR': 2.15,       // 1 KES ≈ PKR2.15
        'BDT': 0.85,       // 1 KES ≈ BDT0.85
        'PHP': 0.43,       // 1 KES ≈ PHP0.43
        'IDR': 120,        // 1 KES ≈ IDR120
        'MYR': 0.036,      // 1 KES ≈ MYR0.036
        'THB': 0.27,       // 1 KES ≈ THB0.27
        'VND': 190,        // 1 KES ≈ VND190

        // European currencies
        'SEK': 0.08,       // 1 KES ≈ SEK0.08
        'NOK': 0.082,      // 1 KES ≈ NOK0.082
        'DKK': 0.053,      // 1 KES ≈ DKK0.053
        'PLN': 0.031,      // 1 KES ≈ PLN0.031

        // Americas
        'MXN': 0.13,       // 1 KES ≈ MXN0.13
        'BRL': 0.038,      // 1 KES ≈ BRL0.038

        // Oceania
        'NZD': 0.013       // 1 KES ≈ NZD0.013
    };

    // Currency symbols and formatting
    const CURRENCY_CONFIG = {
        'KES': { symbol: 'KES', position: 'before', space: true, decimals: 0 },
        'USD': { symbol: '$', position: 'before', space: false, decimals: 2 },
        'EUR': { symbol: '€', position: 'before', space: false, decimals: 2 },
        'GBP': { symbol: '£', position: 'before', space: false, decimals: 2 },
        'CAD': { symbol: 'C$', position: 'before', space: false, decimals: 2 },
        'AUD': { symbol: 'A$', position: 'before', space: false, decimals: 2 },
        'CHF': { symbol: 'CHF', position: 'before', space: true, decimals: 2 },
        'NGN': { symbol: '₦', position: 'before', space: false, decimals: 0 },
        'ZAR': { symbol: 'R', position: 'before', space: false, decimals: 2 },
        'GHS': { symbol: 'GH₵', position: 'before', space: false, decimals: 2 },
        'UGX': { symbol: 'UGX', position: 'before', space: true, decimals: 0 },
        'TZS': { symbol: 'TZS', position: 'before', space: true, decimals: 0 },
        'INR': { symbol: '₹', position: 'before', space: false, decimals: 0 },
        'CNY': { symbol: '¥', position: 'before', space: false, decimals: 2 },
        'JPY': { symbol: '¥', position: 'before', space: false, decimals: 0 },
        'KRW': { symbol: '₩', position: 'before', space: false, decimals: 0 },
        'SGD': { symbol: 'S$', position: 'before', space: false, decimals: 2 },
        'AED': { symbol: 'AED', position: 'before', space: true, decimals: 2 },
        'SAR': { symbol: 'SAR', position: 'before', space: true, decimals: 2 },
        'PKR': { symbol: 'Rs', position: 'before', space: true, decimals: 0 },
        'PHP': { symbol: '₱', position: 'before', space: false, decimals: 2 },
        'IDR': { symbol: 'Rp', position: 'before', space: true, decimals: 0 },
        'MYR': { symbol: 'RM', position: 'before', space: true, decimals: 2 },
        'THB': { symbol: '฿', position: 'before', space: false, decimals: 2 },
        'VND': { symbol: '₫', position: 'after', space: false, decimals: 0 },
        'SEK': { symbol: 'kr', position: 'after', space: true, decimals: 2 },
        'NOK': { symbol: 'kr', position: 'after', space: true, decimals: 2 },
        'DKK': { symbol: 'kr', position: 'after', space: true, decimals: 2 },
        'PLN': { symbol: 'zł', position: 'after', space: true, decimals: 2 },
        'MXN': { symbol: 'MX$', position: 'before', space: false, decimals: 2 },
        'BRL': { symbol: 'R$', position: 'before', space: false, decimals: 2 },
        'NZD': { symbol: 'NZ$', position: 'before', space: false, decimals: 2 },
        'RWF': { symbol: 'FRw', position: 'before', space: true, decimals: 0 },
        'ETB': { symbol: 'ETB', position: 'before', space: true, decimals: 2 },
        'EGP': { symbol: 'E£', position: 'before', space: false, decimals: 2 },
        'MAD': { symbol: 'MAD', position: 'before', space: true, decimals: 2 },
        'BDT': { symbol: '৳', position: 'before', space: false, decimals: 0 }
    };

    const Currency = {
        /**
         * Set the base currency (what prices are stored in)
         * @param {string} currency ISO 4217 currency code
         */
        setBaseCurrency(currency) {
            if (EXCHANGE_RATES[currency] !== undefined) {
                baseCurrency = currency;
            }
        },

        /**
         * Set the user's display currency
         * @param {string} currency ISO 4217 currency code
         */
        setUserCurrency(currency) {
            if (EXCHANGE_RATES[currency] !== undefined) {
                userCurrency = currency;
                console.log(`[Currency] User currency set to: ${currency}`);
            }
        },

        /**
         * Get the current user currency
         * @returns {string} Currency code
         */
        getUserCurrency() {
            return userCurrency;
        },

        /**
         * Get the base currency
         * @returns {string} Currency code
         */
        getBaseCurrency() {
            return baseCurrency;
        },

        /**
         * Convert amount from base currency to user currency
         * @param {number} amountInCents Amount in smallest currency unit (cents/kobo/etc)
         * @param {string} [toCurrency] Target currency (defaults to user currency)
         * @returns {number} Converted amount
         */
        convert(amountInCents, toCurrency = null) {
            const targetCurrency = toCurrency || userCurrency;
            const baseAmount = amountInCents / 100;  // Convert from cents
            const rate = EXCHANGE_RATES[targetCurrency] || 1;
            return baseAmount * rate;
        },

        /**
         * Format amount in user's currency with proper symbol
         * @param {number} amountInCents Amount in smallest currency unit
         * @param {string} [currency] Currency to format in (defaults to user currency)
         * @returns {string} Formatted price string
         */
        format(amountInCents, currency = null) {
            const targetCurrency = currency || userCurrency;
            const convertedAmount = this.convert(amountInCents, targetCurrency);
            const config = CURRENCY_CONFIG[targetCurrency] || {
                symbol: targetCurrency,
                position: 'before',
                space: true,
                decimals: 2
            };

            // Format the number
            let formattedNum;
            if (config.decimals === 0) {
                formattedNum = Math.round(convertedAmount).toLocaleString();
            } else {
                formattedNum = convertedAmount.toFixed(config.decimals);
                // Add thousand separators
                const parts = formattedNum.split('.');
                parts[0] = parseInt(parts[0]).toLocaleString();
                formattedNum = parts.join('.');
            }

            // Apply symbol
            const space = config.space ? ' ' : '';
            if (config.position === 'before') {
                return `${config.symbol}${space}${formattedNum}`;
            } else {
                return `${formattedNum}${space}${config.symbol}`;
            }
        },

        /**
         * Format amount in base currency (for showing original price)
         * @param {number} amountInCents Amount in smallest currency unit
         * @returns {string} Formatted price string
         */
        formatBase(amountInCents) {
            return this.format(amountInCents, baseCurrency);
        },

        /**
         * Get currency symbol
         * @param {string} [currency] Currency code (defaults to user currency)
         * @returns {string} Currency symbol
         */
        getSymbol(currency = null) {
            const targetCurrency = currency || userCurrency;
            return (CURRENCY_CONFIG[targetCurrency] || {}).symbol || targetCurrency;
        },

        /**
         * Check if currency is supported
         * @param {string} currency Currency code
         * @returns {boolean}
         */
        isSupported(currency) {
            return EXCHANGE_RATES[currency] !== undefined;
        },

        /**
         * Get list of supported currencies
         * @returns {string[]} Array of currency codes
         */
        getSupportedCurrencies() {
            return Object.keys(EXCHANGE_RATES);
        },

        /**
         * Update exchange rates (for fetching live rates)
         * @param {Object} rates Object with currency codes as keys and rates as values
         */
        updateRates(rates) {
            Object.assign(EXCHANGE_RATES, rates);
            console.log('[Currency] Exchange rates updated');
        },

        /**
         * Get current exchange rate for a currency
         * @param {string} currency Currency code
         * @returns {number} Exchange rate from base currency
         */
        getRate(currency) {
            return EXCHANGE_RATES[currency] || 1;
        },

        /**
         * Initialize currency from geolocation
         * Uses CVision.Geolocation if available
         */
        async initFromGeolocation() {
            if (global.CVision && global.CVision.Geolocation) {
                await global.CVision.Geolocation.detect();
                const detectedCurrency = global.CVision.Geolocation.getCurrency();
                if (this.isSupported(detectedCurrency)) {
                    this.setUserCurrency(detectedCurrency);
                }
            }
        }
    };

    // Expose to global CVision namespace
    global.CVision = global.CVision || {};
    global.CVision.Currency = Currency;

})(typeof window !== 'undefined' ? window : this);
