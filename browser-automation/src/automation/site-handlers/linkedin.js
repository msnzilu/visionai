// browser-automation/src/automation/site-handlers/linkedin.js

const { GenericHandler } = require('./generic');

class LinkedInHandler extends GenericHandler {
    constructor() {
        super();
        this.name = 'LinkedIn';
    }

    // Add LinkedIn-specific logic here if needed
}

module.exports = { LinkedInHandler };
