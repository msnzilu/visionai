/**
 * ContactForm Component
 * Handles loading and initializing the reusable contact form.
 */
const ContactForm = (function () {
    /**
     * Loads the contact form HTML into a specified container.
     * @param {string} containerId - The ID of the container element.
     */
    async function load(containerId = 'contact-form-container') {
        const container = document.getElementById(containerId);
        if (!container) return;

        try {
            const response = await fetch('/components/contact-form.html');
            if (response.ok) {
                const html = await response.text();
                container.innerHTML = html;

                // Re-initialize the form handler to bind to the new form
                if (window.ContactFormHandler) {
                    ContactFormHandler.init();
                }
            } else {
                console.error('ContactForm: Failed to fetch form HTML');
            }
        } catch (error) {
            console.error('ContactForm: Error loading form:', error);
        }
    }

    /**
     * Automatically finds all elements with data-contact-component and loads the form.
     */
    function autoInit() {
        const containers = document.querySelectorAll('[data-contact-component]');
        containers.forEach(container => {
            const id = container.id || `contact-form-${Math.random().toString(36).substr(2, 9)}`;
            container.id = id;
            load(id);
        });
    }

    // Auto-init on page load
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', autoInit);
    } else {
        autoInit();
    }

    return {
        load,
        init: autoInit
    };
})();

// Expose to window
window.ContactForm = ContactForm;
