// browser-automation/src/automation/field-analyzer.js

const { FieldClassifier } = require('../ml/field-classifier');

/**
 * FieldAnalyzer
 * 
 * A reusable component that bridges the gap between FormDetector (Vision) and AutofillEngine (Action).
 * Use this to analyze forms and determine what data is missing before attempting to fill.
 */
class FieldAnalyzer {
    constructor() {
        this.classifier = new FieldClassifier();
    }

    /**
     * Analyze forms to find missing required fields
     * @param {Array} forms - Output from FormDetector
     * @param {Object} userData - User data object (cv_data, user, etc.)
     * @returns {Object} Analysis result { missingFields: [], complete: boolean }
     */
    analyzeMissingFields(forms, userData) {
        const missingFields = [];

        // Helper to check if we have data for a specific type
        const hasDataForType = (type) => {
            const dataMap = this._getDataMapping(userData);
            const value = dataMap[type];
            return value !== null && value !== undefined && value !== '';
        };

        forms.forEach((form, formIndex) => {
            if (!form.fields) return;

            form.fields.forEach(field => {
                // 1. Classify the field
                const type = this.classifier.classifyField(field);

                // 2. Check if it's required
                // We consider it required if:
                // - HTML 'required' attribute is present
                // - Label contains an asterisk (*)
                // - Label contains "required" (case insensitive)
                const isExplicitlyRequired = field.required;
                const labelIndicatesRequired = field.label && (field.label.includes('*') || /required/i.test(field.label));
                const isOptional = field.label && /optional/i.test(field.label);

                const isNeeded = (isExplicitlyRequired || labelIndicatesRequired) && !isOptional;

                // 3. Check if we have data
                if (isNeeded) {
                    if (!hasDataForType(type)) {
                        missingFields.push({
                            formIndex,
                            selector: field.selector,
                            label: field.label || 'Unknown Field',
                            detectedType: type,
                            reason: 'Required data missing in profile'
                        });
                    }
                }
            });
        });

        return {
            missingFields,
            complete: missingFields.length === 0
        };
    }

    /**
     * Map user data to field types
     */
    _getDataMapping(data) {
        return {
            'first_name': data.user?.first_name,
            'last_name': data.user?.last_name,
            'full_name': `${data.user?.first_name || ''} ${data.user?.last_name || ''}`.trim(),
            'email': data.user?.email,
            'phone': data.user?.phone,
            'address': data.user?.address,
            'city': data.user?.city,
            'state': data.user?.state,
            'zip_code': data.user?.zip_code,
            'country': data.user?.country,
            'linkedin': data.cv_data?.linkedin,
            'portfolio': data.cv_data?.portfolio,
            'github': data.cv_data?.github,
            'cover_letter': data.cover_letter,
            // Add future types here
            'resume': true // Assume resume is present if we are running automation (validated upstream)
        };
    }
}

module.exports = { FieldAnalyzer };
