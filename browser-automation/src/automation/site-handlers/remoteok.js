// browser-automation/src/automation/site-handlers/remoteok.js

const { GenericHandler } = require('./generic');
const { PageClassifier } = require('../page-classifier');

class RemoteOKHandler extends GenericHandler {
    constructor() {
        super();
        this.name = 'RemoteOK';
        this.version = '2.2';
    }

    // Override preparePage to click "Apply" button
    async preparePage(page) {
        console.log(`\n[RemoteOK V${this.version}] Handler engaged for ${page.url()}`);

        try {
            await page.waitForLoadState('domcontentloaded');

            // Classification check
            const classifier = new PageClassifier(page);
            const pageType = await classifier.classify();
            console.log(`[RemoteOK] Current page type: ${pageType}`);

            if (pageType === 'application') {
                console.log('[RemoteOK] Application form detected on current page.');
                return page;
            }

            console.log('[RemoteOK] Searching for Apply button...');

            // Scroll to ensure buttons load
            await page.evaluate(() => window.scrollTo(0, 500));
            await page.waitForTimeout(1000);

            const strategies = [
                async () => page.$('.apply_now'),
                async () => page.$('.action-apply'),
                async () => page.$('.apply_button'),
                async () => page.$('a[href*="/apply"]'),
                async () => page.$('a[href*="/l/"]'), // RemoteOK application redirect links
                async () => page.getByText(/^Apply now$/i).first(),
                async () => page.getByText(/^Apply for this job$/i).first(),
                async () => page.getByRole('button', { name: /apply/i }).first(),
                async () => page.getByRole('link', { name: /apply/i }).first(),
                async () => {
                    return await page.evaluateHandle(() => {
                        const all = document.querySelectorAll('a, button, [role="button"]');
                        for (const el of all) {
                            const text = (el.innerText || el.textContent || '').toLowerCase();
                            // Require "apply" in text and ensure it's not just a single letter (like company initials)
                            if (text.includes('apply') && text.length > 1 && el.offsetWidth > 0 && el.offsetHeight > 0) return el;
                        }
                        return null;
                    }).then(h => h.asElement());

                }
            ];

            const context = page.context();
            const pagesBefore = context.pages().length;

            for (const findStrategy of strategies) {
                try {
                    const element = await findStrategy();
                    if (element && await element.isVisible()) {
                        const text = await element.evaluate(el => (el.innerText || el.textContent || '').trim());
                        console.log(`[RemoteOK] Found button: "${text}". Clicking...`);

                        const newPagePromise = new Promise((resolve) => {
                            const timeout = setTimeout(() => resolve(null), 8000); // 8s timeout
                            context.once('page', (newPage) => {
                                clearTimeout(timeout);
                                resolve(newPage);
                            });
                        });

                        // Attempt click
                        try {
                            await element.click({ timeout: 5000 });
                        } catch (clickErr) {
                            console.log('[RemoteOK] Click failed, trying dispatchEvent.');
                            await element.dispatchEvent('click');
                        }

                        const newPage = await newPagePromise;
                        let pageToCheck = newPage || page;

                        if (newPage) {
                            console.log('[RemoteOK] New tab detected!');
                            await newPage.waitForLoadState('domcontentloaded').catch(() => { });
                        } else {
                            // Check fallback
                            await page.waitForTimeout(2000);
                            const pagesNow = context.pages();
                            if (pagesNow.length > pagesBefore) {
                                const newest = pagesNow.find(p => p !== page && !p.isClosed());
                                if (newest) {
                                    console.log('[RemoteOK] Found new tab via context fallback.');
                                    pageToCheck = newest;
                                    await newest.waitForLoadState('domcontentloaded').catch(() => { });
                                }
                            }
                        }

                        // CRITICAL: Check if we landed on a login/registration wall
                        console.log('[RemoteOK] Classifying resulting page...');
                        const resultClassifier = new PageClassifier(pageToCheck);
                        const resultType = await resultClassifier.classify();
                        console.log(`[RemoteOK] Resulting page type: ${resultType}`);

                        if (resultType === 'login' || resultType === 'register') {
                            console.warn('[RemoteOK] Login wall detected. Cancellation required.');
                            throw new Error('LOGIN_REQUIRED');
                        }

                        if (resultType === 'application') {
                            console.log('[RemoteOK] Application form detected!');
                            return pageToCheck;
                        }

                        console.log('[RemoteOK] Page type inconclusive, continuing search...');
                    }
                } catch (strategyErr) {
                    if (strategyErr.message === 'LOGIN_REQUIRED') throw strategyErr;
                    console.error(`[RemoteOK] Strategy failed: ${strategyErr.message}`);
                }
            }

            console.warn('[RemoteOK] No apply button succeeded.');
            return page;

        } catch (error) {
            console.error('[RemoteOK] prepPage error:', error.message);
            return page;
        }
    }

    async fillForm(page, form, autofillData) {
        console.log(`[RemoteOK V${this.version}] Filling form...`);
        return super.fillForm(page, form, autofillData);
    }
}

module.exports = { RemoteOKHandler };
