// browser-automation/src/automation/site-handlers/factory.js

const { GenericHandler } = require('./generic');
const { IndeedHandler } = require('./indeed');
const { LinkedInHandler } = require('./linkedin');
const { RemoteOKHandler } = require('./remoteok');

class SiteHandlerFactory {
    static getHandler(url, jobSource) {
        const hostname = new URL(url).hostname.toLowerCase();

        // Match by hostname or job source
        if (hostname.includes('indeed.com') || jobSource === 'indeed') {
            console.log('Using Indeed handler');
            return new IndeedHandler();
        }

        if (hostname.includes('linkedin.com') || jobSource === 'linkedin') {
            console.log('Using LinkedIn handler');
            return new LinkedInHandler();
        }

        if (hostname.includes('remoteok.com') || hostname.includes('remoteok.io') || jobSource === 'remoteok') {
            console.log('Using RemoteOK handler');
            return new RemoteOKHandler();
        }

        // Add more site-specific handlers here
        // if (hostname.includes('greenhouse.io')) {
        //     return new GreenhouseHandler();
        // }

        console.log('Using generic handler');
        return new GenericHandler();
    }
}

module.exports = { SiteHandlerFactory };