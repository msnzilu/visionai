// browser-automation/src/ml/field-classifier.js

class FieldClassifier {
    constructor() {
        // Field type patterns for classification
        this.patterns = {
            first_name: [
                /first[\s_-]?name/i,
                /fname/i,
                /given[\s_-]?name/i,
                /forename/i
            ],
            last_name: [
                /last[\s_-]?name/i,
                /lname/i,
                /surname/i,
                /family[\s_-]?name/i
            ],
            full_name: [
                /^name$/i,
                /full[\s_-]?name/i,
                /complete[\s_-]?name/i
            ],
            email: [
                /e?mail/i,
                /email[\s_-]?address/i,
                /contact[\s_-]?email/i
            ],
            phone: [
                /phone/i,
                /telephone/i,
                /mobile/i,
                /contact[\s_-]?number/i,
                /phone[\s_-]?number/i
            ],
            address: [
                /^address$/i,
                /street[\s_-]?address/i,
                /address[\s_-]?line/i,
                /home[\s_-]?address/i
            ],
            city: [
                /city/i,
                /town/i
            ],
            state: [
                /state/i,
                /province/i,
                /region/i
            ],
            zip_code: [
                /zip/i,
                /postal/i,
                /postcode/i,
                /zip[\s_-]?code/i
            ],
            country: [
                /country/i,
                /nation/i
            ],
            linkedin: [
                /linkedin/i,
                /linked[\s_-]?in/i
            ],
            portfolio: [
                /portfolio/i,
                /website/i,
                /personal[\s_-]?site/i
            ],
            github: [
                /github/i,
                /git[\s_-]?hub/i
            ],
            cover_letter: [
                /cover[\s_-]?letter/i,
                /motivation/i,
                /why[\s_-]?you/i,
                /about[\s_-]?yourself/i
            ],
            resume: [
                /resume/i,
                /cv/i,
                /curriculum/i
            ]
        };
    }
    
    classifyField(field) {
        // Extract features from field
        const features = this.extractFeatures(field);
        
        // Try to match based on patterns
        for (const [fieldType, patterns] of Object.entries(this.patterns)) {
            for (const pattern of patterns) {
                if (pattern.test(features.searchText)) {
                    return fieldType;
                }
            }
        }
        
        // Fallback: try autocomplete attribute
        if (field.autocomplete) {
            const autocompleteMap = {
                'given-name': 'first_name',
                'family-name': 'last_name',
                'name': 'full_name',
                'email': 'email',
                'tel': 'phone',
                'street-address': 'address',
                'address-line1': 'address',
                'address-level2': 'city',
                'address-level1': 'state',
                'postal-code': 'zip_code',
                'country': 'country'
            };
            
            if (autocompleteMap[field.autocomplete]) {
                return autocompleteMap[field.autocomplete];
            }
        }
        
        return 'unknown';
    }
    
    extractFeatures(field) {
        // Combine all text features for matching
        const searchText = [
            field.name,
            field.id,
            field.label,
            field.placeholder
        ].filter(Boolean).join(' ');
        
        return {
            searchText,
            type: field.type,
            required: field.required
        };
    }
}

module.exports = { FieldClassifier };