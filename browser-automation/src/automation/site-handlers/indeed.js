// browser-automation/src/automation/site-handlers/indeed.js

const { GenericHandler } = require('./generic');

class IndeedHandler extends GenericHandler {
    constructor() {
        super();
        this.name = 'Indeed';
    }

    // Add Indeed-specific logic here if needed
}

module.exports = { IndeedHandler };
