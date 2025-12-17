/**
 * PremiumGuard Utility
 * Centralizes logic for checking user subscription tiers and restricting access to features.
 * Dependencies: CVision.Utils (for user data), UpgradeModal (for UI)
 */
const PremiumGuard = {
    // Feature Definitions and their minimum required tiers
    FEATURES: {
        AUTO_APPLY: 'basic',        // Basic or Premium
        UNLIMITED_MSGS: 'premium',  // Premium only
        CV_CUSTOMIZATION: 'basic',  // Basic or Premium
        ADVANCED_ANALYTICS: 'premium',
        RUN_TEST: 'basic'           // Basic or Premium (with 1 free trial)
    },

    /**
     * Checks if the current user has access to a specific feature.
     * @param {string} feature - The feature key from PremiumGuard.FEATURES
     * @returns {boolean} - True if allowed, false otherwise
     */
    hasAccess: function (feature) {
        const user = CVision.Utils.getUser();
        const userTier = (user?.subscription_tier || 'free').toLowerCase();

        // Define tier levels for comparison
        const tierLevels = {
            'free': 0,
            'basic': 1,
            'premium': 2
        };

        const requiredTier = this.FEATURES[feature] || 'premium'; // Default to highest if unknown

        return tierLevels[userTier] >= tierLevels[requiredTier];
    },

    /**
     * Enforces premium access. If user has access, returns true.
     * If not, shows the UpgradeModal and returns false.
     * @param {string} feature - The feature key from PremiumGuard.FEATURES
     * @param {string} [customTitle] - Optional title for the modal
     * @param {string} [customMessage] - Optional message for the modal
     * @returns {boolean} - True if proceeded (access granted), False if blocked (modal shown)
     */
    enforce: function (feature, customTitle, customMessage) {
        if (this.hasAccess(feature)) {
            return true;
        }

        // Access denied - Show Modal
        if (typeof UpgradeModal !== 'undefined') {
            const requiredTier = this.FEATURES[feature] || 'premium';
            const title = customTitle || 'Premium Feature';
            const message = customMessage || `This feature requires a ${requiredTier.charAt(0).toUpperCase() + requiredTier.slice(1)} subscription. Upgrade now to unlock it!`;

            UpgradeModal.show(title, message);
        } else {
            console.warn('UpgradeModal not loaded, using fallback alert');
            alert('This feature requires a premium subscription.');
        }

        return false;
    }
};

// Expose globally
window.PremiumGuard = PremiumGuard;
