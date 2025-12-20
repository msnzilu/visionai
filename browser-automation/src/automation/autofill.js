const { FieldClassifier } = require('../ml/field-classifier');

class AutofillEngine {
    constructor(page, siteHandler) {
        this.page = page;
        this.siteHandler = siteHandler;
        this.fieldClassifier = new FieldClassifier();
    }
    
    async fillForms(forms, autofillData) {
        const filledFields = [];
        
        for (const form of forms) {
            try {
                // Use site-specific handler if available
                if (this.siteHandler && this.siteHandler.fillForm) {
                    const result = await this.siteHandler.fillForm(
                        this.page,
                        form,
                        autofillData
                    );
                    filledFields.push(...result);
                } else {
                    // Use generic filling logic
                    const result = await this.fillFormGeneric(form, autofillData);
                    filledFields.push(...result);
                }
            } catch (error) {
                console.error('Error filling form:', error);
            }
        }
        
        return filledFields;
    }
    
    async fillFormGeneric(form, data) {
        const filledFields = [];
        
        for (const field of form.fields) {
            try {
                // Classify field type using ML
                const fieldType = this.fieldClassifier.classifyField(field);
                
                // Get appropriate value
                const value = this.getValueForField(fieldType, data);
                
                if (value) {
                    const filled = await this.fillField(field, value);
                    if (filled) {
                        filledFields.push({
                            selector: field.selector,
                            type: fieldType,
                            value: field.type === 'password' ? '***' : value
                        });
                    }
                }
            } catch (error) {
                console.error(`Error filling field ${field.selector}:`, error);
            }
        }
        
        return filledFields;
    }
    
    async fillField(field, value) {
        try {
            await this.page.waitForSelector(field.selector, { timeout: 5000 });
            
            if (field.type === 'select') {
                await this.page.select(field.selector, value);
            } else if (field.type === 'checkbox' || field.type === 'radio') {
                if (value) {
                    await this.page.click(field.selector);
                }
            } else if (field.type === 'file') {
                // Handle file uploads separately
                return false;
            } else {
                // Clear existing value
                await this.page.click(field.selector, { clickCount: 3 });
                await this.page.keyboard.press('Backspace');
                
                // Type new value with human-like delay
                await this.page.type(field.selector, String(value), { 
                    delay: Math.random() * 100 + 50 
                });
            }
            
            // Trigger change event
            await this.page.evaluate((selector) => {
                const element = document.querySelector(selector);
                if (element) {
                    element.dispatchEvent(new Event('change', { bubbles: true }));
                    element.dispatchEvent(new Event('blur', { bubbles: true }));
                }
            }, field.selector);
            
            return true;
        } catch (error) {
            console.error(`Failed to fill field ${field.selector}:`, error.message);
            return false;
        }
    }
    
    getValueForField(fieldType, data) {
        const mapping = {
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
            'cover_letter': data.cover_letter
        };
        
        return mapping[fieldType] || null;
    }
    
    async uploadFile(fileInputSelector, filePath) {
        try {
            const input = await this.page.$(fileInputSelector);
            if (input) {
                await input.uploadFile(filePath);
                return true;
            }
            return false;
        } catch (error) {
            console.error('File upload failed:', error);
            return false;
        }
    }
}

module.exports = { AutofillEngine };