// browser-automation/src/automation/site-handlers/generic.js

class GenericHandler {
    constructor() {
        this.name = 'Generic';
    }

    /**
     * Extract and flatten autofill data from nested structure
     */
    extractAutofillData(autofillData) {
        // Handle nested structure
        const user = autofillData.user || {};
        const cvData = autofillData.cv_data || {};
        const job = autofillData.job || {};

        return {
            // Personal Information
            firstName: user.first_name || cvData.first_name || '',
            lastName: user.last_name || cvData.last_name || '',
            fullName: user.full_name || cvData.full_name || `${user.first_name || ''} ${user.last_name || ''}`.trim(),
            email: user.email || cvData.email || '',
            phone: user.phone || cvData.phone || '',

            // Location
            address: user.address || cvData.address || '',
            city: user.city || cvData.city || '',
            state: user.state || cvData.state || '',
            zip: user.zip_code || cvData.zip_code || '',
            country: user.country || cvData.country || '',

            // Professional
            linkedin: cvData.linkedin || user.linkedin || '',
            github: cvData.github || user.github || '',
            portfolio: cvData.portfolio || user.portfolio || '',

            // Resume/Cover Letter
            resume: cvData.resume_path || '',
            coverLetter: autofillData.cover_letter || '',

            // Job Info (for reference)
            jobTitle: job.title || '',
            company: job.company || '',
        };
    }

    getFieldMapping() {
        return {
            // Personal Information
            firstName: ['firstname', 'first-name', 'first_name', 'fname', 'givenname', 'given-name'],
            lastName: ['lastname', 'last-name', 'last_name', 'lname', 'surname', 'familyname', 'family-name'],
            fullName: ['fullname', 'full-name', 'full_name', 'name'],
            email: ['email', 'e-mail', 'email-address', 'emailaddress', 'mail'],
            phone: ['phone', 'telephone', 'mobile', 'phonenumber', 'phone-number', 'tel'],

            // Location
            address: ['address', 'street', 'streetaddress', 'street-address', 'address1'],
            address2: ['address2', 'address-2', 'apt', 'suite', 'unit'],
            city: ['city', 'town', 'locality'],
            state: ['state', 'province', 'region', 'county'],
            zip: ['zip', 'zipcode', 'postal', 'postcode', 'postalcode', 'postal-code'],
            country: ['country', 'nation'],

            // Professional
            linkedin: ['linkedin', 'linkedin-url', 'linkedinurl', 'linkedin-profile'],
            github: ['github', 'github-url', 'githuburl', 'github-profile'],
            portfolio: ['portfolio', 'website', 'personal-website', 'portfoliourl'],

            // Work Authorization
            authorized: ['authorized', 'work-authorized', 'eligible', 'authorization'],
            sponsorship: ['sponsorship', 'visa-sponsorship', 'require-sponsorship'],

            // Resume/Cover Letter
            resume: ['resume', 'cv', 'curriculum-vitae'],
            coverLetter: ['cover-letter', 'coverletter', 'cover_letter', 'letter'],
        };
    }

    matchField(fieldName, fieldType, flattenedData) {
        const mapping = this.getFieldMapping();
        const normalizedName = fieldName.toLowerCase().replace(/[_\s-]/g, '');

        console.log(`Trying to match field: ${fieldName} (normalized: ${normalizedName})`);

        // Try to find a match
        for (const [dataKey, patterns] of Object.entries(mapping)) {
            for (const pattern of patterns) {
                const normalizedPattern = pattern.replace(/[_\s-]/g, '');
                if (normalizedName.includes(normalizedPattern)) {
                    const value = flattenedData[dataKey];
                    if (value) {
                        console.log(`✓ Matched ${fieldName} to ${dataKey} = ${value}`);
                        return value;
                    }
                }
            }
        }

        console.log(`✗ No match found for ${fieldName}`);
        return null;
    }

    async fillForm(page, form, autofillData) {
        // Extract and flatten the data first
        const flattenedData = this.extractAutofillData(autofillData);

        console.log(`Generic handler filling form with ${form.fields?.length || 0} fields`);
        console.log(`Flattened data:`, flattenedData);

        const filledFields = [];

        if (!form.fields || form.fields.length === 0) {
            console.log('No fields to fill in this form');
            return filledFields;
        }

        for (const field of form.fields) {
            try {
                const fieldIdentifier = field.name || field.id || field.placeholder || '';
                console.log(`Processing field: ${fieldIdentifier} (type: ${field.type})`);

                const value = this.matchField(
                    fieldIdentifier,
                    field.type,
                    flattenedData
                );

                if (value) {
                    await this.fillField(page, field, value);
                    filledFields.push({
                        field: fieldIdentifier,
                        value: value,
                        type: field.type
                    });
                    console.log(`✓ Filled field: ${fieldIdentifier} with value: ${value}`);
                } else {
                    console.log(`✗ No value to fill for field: ${fieldIdentifier}`);
                }
            } catch (error) {
                console.error(`Error filling field ${field.name || field.id}:`, error.message);
            }
        }

        return filledFields;
    }

    async fillField(page, field, value) {
        const selector = field.selector;

        if (!selector) {
            console.log('No selector for field');
            return;
        }

        try {
            // Wait for the field to be available
            await page.waitForSelector(selector, { timeout: 5000 });

            // Handle different field types
            switch (field.type) {
                case 'checkbox':
                    if (value) {
                        await page.check(selector);
                    }
                    break;

                case 'radio':
                    await page.check(selector);
                    break;

                case 'select':
                    await page.selectOption(selector, value);
                    break;

                case 'file':
                    console.log('File upload field detected - skipping for now');
                    break;

                default:
                    // Text inputs, textareas, etc.
                    await page.fill(selector, String(value));
                    break;
            }
        } catch (error) {
            console.error(`Failed to fill field ${selector}:`, error.message);
        }
    }
}

module.exports = { GenericHandler };