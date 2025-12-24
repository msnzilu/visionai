const { chromium } = require('playwright');

/**
 * Check application status on a job portal
 * @param {string} url - The URL to check (either job posting or application dashboard)
 * @param {object} options - Optional selectors or platform hints
 * @returns {object} Status result
 */
async function checkStatus(url, options = {}) {
    let browser = null;
    try {
        console.log(`Checking status for: ${url}`);

        browser = await chromium.launch({
            headless: process.env.HEADLESS !== 'false',
            args: ['--no-sandbox', '--disable-setuid-sandbox']
        });

        const context = await browser.newContext({
            userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        });

        const page = await context.newPage();

        // Navigate with timeout
        await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
        await page.waitForTimeout(2000); // Wait for dynamic content

        // Get full page text for analysis
        const bodyText = await page.evaluate(() => document.body.innerText);
        const lowerText = bodyText.toLowerCase();

        // Keywords mapping (Status -> Keywords)
        const statusMap = {
            'rejected': ['no longer being considered', 'not selected', 'thank you for your interest', 'position has vary filled', 'candidate selected'],
            'interview': ['interview', 'schedule a time', 'availability'],
            'offer': ['offer', 'congratulations'],
            'in_review': ['under review', 'in review', 'application recieved', 'reviewing'],
            'applied': ['applied', 'submitted', 'application submitted']
        };

        let detectedStatus = 'unknown';
        let matchedKeyword = '';

        // Check keywords in priority order (Rejected > Offer > Interview > In Review > Applied)
        const priorityOrder = ['rejected', 'offer', 'interview', 'in_review', 'applied'];

        for (const status of priorityOrder) {
            const keywords = statusMap[status];
            for (const keyword of keywords) {
                if (lowerText.includes(keyword)) {
                    detectedStatus = status;
                    matchedKeyword = keyword;
                    break;
                }
            }
            if (detectedStatus !== 'unknown') break;
        }

        // Take a screenshot if status is interesting
        let screenshot = null;
        if (detectedStatus !== 'unknown' && detectedStatus !== 'applied') {
            screenshot = await page.screenshot({ encoding: 'base64' });
        }

        return {
            success: true,
            status: detectedStatus,
            matched_keyword: matchedKeyword,
            current_url: page.url(),
            screenshot_base64: screenshot
        };

    } catch (error) {
        console.error('Status check error:', error);
        return {
            success: false,
            error: error.message
        };
    } finally {
        if (browser) {
            await browser.close();
        }
    }
}

module.exports = { checkStatus };
