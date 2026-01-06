// browser-automation/src/index.js
require('dotenv').config({ path: require('path').resolve(__dirname, '../../.env') });

const express = require('express');
const { chromium } = require('playwright');
const cors = require('cors');
const { AutofillEngine } = require('./automation/autofill');
const { FormDetector } = require('./automation/form-detector');
const { SiteHandlerFactory } = require('./automation/site-handlers/factory');

const app = express();
const PORT = process.env.PORT || 3001;
const AUTH_TOKEN = process.env.BROWSER_AUTOMATION_TOKEN || 'dev-automation-token';

app.use(cors());
app.use(express.json({ limit: '10mb' }));

// Store active browser sessions
const activeSessions = new Map();

// Authentication middleware
// const authenticate = (req, res, next) => {
//     const authHeader = req.headers.authorization;
//     if (!authHeader || !authHeader.startsWith('Bearer ')) {
//         return res.status(401).json({ error: 'Unauthorized' });
//     }

//     const token = authHeader.substring(7);
//     if (token !== AUTH_TOKEN) {
//         return res.status(401).json({ error: 'Invalid token' });
//     }

//     next();
// };
// Authentication middleware
const authenticate = (req, res, next) => {

    const authHeader = req.headers.authorization;
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
        return res.status(401).json({ error: 'Unauthorized' });
    }

    const token = authHeader.substring(7);

    if (token !== AUTH_TOKEN) {
        return res.status(401).json({ error: 'Invalid token' });
    }

    next();
};

// Health check
app.get('/health', (req, res) => {
    res.json({
        status: 'healthy',
        service: 'Browser Automation Service (Playwright)',
        active_sessions: activeSessions.size,
        version: '2.0.0'
    });
});

// Start automation session
app.post('/api/automation/start', authenticate, async (req, res) => {
    const { session_id, url, autofill_data, job_source } = req.body;

    if (!session_id || !url || !autofill_data) {
        return res.status(400).json({
            error: 'Missing required fields: session_id, url, autofill_data'
        });
    }

    try {
        console.log(`Starting browser automation for session: ${session_id}`);
        console.log(`Target URL: ${url}`);
        console.log(`Job source: ${job_source}`);

        // Launch browser with Playwright
        const headlessEnv = process.env.HEADLESS ? process.env.HEADLESS.toLowerCase().trim() : 'true';
        const isHeadless = headlessEnv !== 'false';

        console.log(`[Browser Config] HEADLESS env: "${process.env.HEADLESS}" -> Mode: ${isHeadless ? 'Headless (Background)' : 'Headful (Visible UI)'}`);

        // Force disable Playwright Inspector in ALL modes to prevent "Assistant" window
        delete process.env.PWDEBUG;
        process.env.DEBUG = '0';

        const browser = await chromium.launch({
            headless: isHeadless,
            devtools: false,
            args: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--disable-web-security',  // Helps with CORS issues
                '--disable-features=IsolateOrigins,site-per-process'
            ],
            // Playwright-specific options
            slowMo: 50, // Slow down by 50ms for better visibility
        });

        // Create a new context (like an incognito window)
        const context = await browser.newContext({
            viewport: null, // Use full window size
            userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ' +
                '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            // Additional Playwright features
            locale: 'en-US',
            timezoneId: 'America/New_York',
            permissions: ['geolocation', 'notifications'],
        });

        const page = await context.newPage();

        // Store session
        activeSessions.set(session_id, {
            browser,
            context,
            page,
            autofill_data,
            job_source,
            started_at: new Date(),
            status: 'initialized'
        });

        // Navigate and autofill in background
        performAutofill(session_id, url, autofill_data, job_source, page)
            .catch(err => {
                console.error(`Autofill error for session ${session_id}:`, err);
                updateSessionStatus(session_id, 'error', err.message);
            });

        res.json({
            browser_session_id: session_id,
            status: 'started',
            message: 'Browser automation started successfully'
        });

    } catch (error) {
        console.error('Failed to start browser automation:', error);
        res.status(500).json({
            error: 'Failed to start browser automation',
            details: error.message
        });
    }
});

// Get session status
app.get('/api/automation/status/:session_id', authenticate, (req, res) => {
    const { session_id } = req.params;
    const session = activeSessions.get(session_id);

    if (!session) {
        return res.status(404).json({ error: 'Session not found' });
    }

    res.json({
        session_id,
        status: session.status,
        started_at: session.started_at,
        filled_fields: session.filled_fields || [],
        errors: session.errors || []
    });
});

// Close session
app.post('/api/automation/close/:session_id', authenticate, async (req, res) => {
    const { session_id } = req.params;
    const session = activeSessions.get(session_id);

    if (!session) {
        return res.status(404).json({ error: 'Session not found' });
    }

    try {
        await session.context.close(); // Close context first
        await session.browser.close();
        activeSessions.delete(session_id);
        res.json({ message: 'Session closed successfully' });
    } catch (error) {
        res.status(500).json({ error: 'Failed to close session' });
    }
});

async function performAutofill(session_id, url, autofillData, jobSource, page) {
    console.log(`=== STARTING AUTOFILL FOR SESSION ${session_id} ===`);

    const session = activeSessions.get(session_id);
    if (!session) {
        console.error(`Session ${session_id} not found in activeSessions!`);
        return;
    }

    console.log(`Autofill data received:`, JSON.stringify(autofillData, null, 2));

    try {
        updateSessionStatus(session_id, 'navigating');

        console.log(`Navigating to: ${url}`);
        const response = await page.goto(url, {
            waitUntil: 'domcontentloaded',
            timeout: 60000
        });

        console.log(`Navigation response status: ${response?.status()}`);
        console.log(`Page loaded: ${await page.title()}`);

        await page.waitForLoadState('networkidle', { timeout: 10000 }).catch(() => {
            console.log('Network not idle after 10s, but continuing...');
        });

        await page.waitForTimeout(3000);

        updateSessionStatus(session_id, 'detecting_forms');

        const handler = SiteHandlerFactory.getHandler(url, jobSource);

        // Prepare page (e.g. click "Apply" buttons) - this may open a new tab
        let activePage = page;
        if (handler && typeof handler.preparePage === 'function') {
            try {
                const newPage = await handler.preparePage(page);
                if (newPage && newPage !== page) {
                    console.log('[Autofill] Handler returned new page (new tab detected). Switching context...');
                    activePage = newPage;

                    // Update session reference
                    if (session) session.page = activePage;

                    // Wait for the new page to stabilize
                    await activePage.waitForLoadState('domcontentloaded').catch(() => { });
                    await activePage.waitForTimeout(2000);

                    console.log(`[Autofill] New tab URL: ${activePage.url()}`);
                    console.log(`[Autofill] New tab title: ${await activePage.title()}`);
                }
            } catch (prepareError) {
                // Check if original page is still valid
                if (page.isClosed()) {
                    console.log('[Autofill] Original page closed. Checking for new tabs in context...');
                    // Try to find any open page in the context
                    const pages = session.context.pages();
                    const validPage = pages.find(p => !p.isClosed() && p.url() !== 'about:blank');
                    if (validPage) {
                        console.log(`[Autofill] Found valid page: ${validPage.url()}`);
                        activePage = validPage;
                        if (session) session.page = activePage;
                        await activePage.waitForLoadState('domcontentloaded').catch(() => { });
                    } else {
                        throw new Error('All pages in context are closed or invalid');
                    }
                } else {
                    console.warn('[Autofill] preparePage error but original page still valid:', prepareError.message);
                }
            }
        }

        // Ensure we have a valid page before continuing
        if (activePage.isClosed()) {
            throw new Error('[Autofill] Active page is closed. New tab might have closed prematurely.');
        }

        const formDetector = new FormDetector(activePage);
        const forms = await formDetector.detectForms();

        console.log(`[Autofill V2.1] Detected ${forms.length} total forms on ${activePage.url()}`);
        console.log(`Current page URL: ${activePage.url()}`);

        // Filter out non-application forms (search bars, filters, etc.)
        const excludePatterns = ['search', 'filter', 'subscribe', 'newsletter', 'login', 'signin'];
        const applicationForms = forms.filter(form => {
            const fieldNames = form.fields?.map(f =>
                (f.name || f.id || f.placeholder || f.label || '').toLowerCase()
            ).join(' ');

            // Skip if it looks like a search/nav form
            const isSearchForm = excludePatterns.some(p => fieldNames.includes(p));

            // Prefer forms with typical application fields
            const hasAppFields = form.fields?.some(f => {
                const combined = `${f.name} ${f.id} ${f.placeholder} ${f.label}`.toLowerCase();
                return combined.includes('email') ||
                    combined.includes('name') ||
                    combined.includes('phone') ||
                    combined.includes('resume') ||
                    combined.includes('cv') ||
                    combined.includes('cover');
            });

            if (isSearchForm && !hasAppFields) {
                console.log(`Skipping non-application form: ${fieldNames.substring(0, 50)}...`);
                return false;
            }
            return true;
        });

        console.log(`Filtered to ${applicationForms.length} application forms`);

        // Throw error if no application forms found
        if (applicationForms.length === 0) {
            throw new Error('No application form detected. This job might require manual application on the company\'s website or a search for an "Apply" button failed.');
        }

        // DIAGNOSTIC: If no forms found, dump page info
        if (applicationForms.length === 0) {
            console.warn('⚠️ DIAGNOSTIC: Zero application forms detected. Dumping page info...');
            const title = await activePage.title();
            const bodyText = await activePage.evaluate(() => document.body.innerText.substring(0, 500));
            console.log(`Page Title: ${title}`);
            console.log(`Body snippet: ${bodyText.substring(0, 300)}...`);

            // Check for common ATS indicators
            const hasFileInput = await activePage.$('input[type="file"]');
            const hasEmailInput = await activePage.$('input[type="email"]');
            console.log(`Has file input: ${!!hasFileInput}, Has email input: ${!!hasEmailInput}`);

            // Check if we're on a login page
            const currentUrl = activePage.url().toLowerCase();
            const pageTitle = title.toLowerCase();
            if (currentUrl.includes('login') || currentUrl.includes('signin') ||
                pageTitle.includes('login') || pageTitle.includes('sign in')) {
                console.warn('⚠️ LOGIN PAGE DETECTED - User may need to authenticate manually');
            }
        }

        // Log form details
        applicationForms.forEach((form, index) => {
            console.log(`Form ${index + 1}:`, {
                fields: form.fields?.length || 0,
                fieldNames: form.fields?.map(f => f.name || f.id || f.placeholder).filter(Boolean)
            });
        });

        updateSessionStatus(session_id, 'filling_forms');

        const autofillEngine = new AutofillEngine(activePage, handler);
        const filledFields = await autofillEngine.fillForms(applicationForms, autofillData);

        // Throw error if no fields were actually filled
        if (filledFields.length === 0) {
            throw new Error('Found an application form, but could not identify any fields to autofill using your profile data.');
        }

        session.filled_fields = filledFields;
        updateSessionStatus(session_id, 'completed', null, filledFields);

        console.log(`Autofill completed for session ${session_id}`);
        console.log(`Filled ${filledFields.length} fields`);

        if (filledFields.length > 0) {
            console.log('Filled fields:', filledFields);
        }

        await activePage.screenshot({ path: `/tmp/completed-${session_id}.png` }).catch(() => { });

    } catch (error) {
        console.error(`Autofill failed for session ${session_id}:`, error);

        if (error.message === 'LOGIN_REQUIRED') {
            updateSessionStatus(session_id, 'login_required', 'This job requires manual login or account creation on the job board.');

            // Allow some time for frontend to poll the status
            await page.waitForTimeout(5000).catch(() => { });

            // Close session specifically because of login wall
            try {
                if (session && session.browser) {
                    await session.browser.close();
                    console.log(`Browser closed for session ${session_id} due to login wall.`);
                }
            } catch (closeError) {
                console.error('Error closing browser after login wall:', closeError);
            }
        }

        try {
            if (activePage && !activePage.isClosed()) {
                await activePage.screenshot({ path: `/tmp/error-${session_id}.png` }).catch(() => { });
                console.log(`Error screenshot saved: /tmp/error-${session_id}.png`);
            }
        } catch (screenshotError) {
            console.error('Could not take error screenshot');
        }

        updateSessionStatus(session_id, 'error', error.message === 'LOGIN_REQUIRED' ? 'Manual login required' : error.message);
    }
}

function updateSessionStatus(session_id, status, error = null, filledFields = null) {
    const session = activeSessions.get(session_id);
    if (session) {
        session.status = status;
        session.updated_at = new Date();

        if (error) {
            session.errors = session.errors || [];
            session.errors.push({
                message: error,
                timestamp: new Date()
            });
        }

        if (filledFields) {
            session.filled_fields = filledFields;
        }
    }
}

// Cleanup inactive sessions (after 30 minutes)
setInterval(() => {
    const thirtyMinutesAgo = Date.now() - 30 * 60 * 1000;

    for (const [session_id, session] of activeSessions.entries()) {
        if (session.started_at.getTime() < thirtyMinutesAgo) {
            console.log(`Cleaning up inactive session: ${session_id}`);
            session.context.close().catch(console.error);
            session.browser.close().catch(console.error);
            activeSessions.delete(session_id);
        }
    }
}, 5 * 60 * 1000); // Check every 5 minutes

// Check Application Status Endpoint
app.post('/api/automation/check-status', async (req, res) => {
    try {
        const { url, options } = req.body;

        if (!url) {
            return res.status(400).json({ error: 'URL is required' });
        }

        console.log(`[${new Date().toISOString()}] Status check requested for: ${url}`);

        const { checkStatus } = require('./automation/status-checker');
        const result = await checkStatus(url, options || {});

        res.json(result);

    } catch (error) {
        console.error('Status check endpoint error:', error);
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Health check endpoint
app.get('/health', (req, res) => {
    res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

app.listen(PORT, () => {
    console.log(`Browser automation service running on port ${PORT}`);
    console.log(`Authentication token configured: ${AUTH_TOKEN ? 'Yes' : 'No'}`);
});

process.on('SIGTERM', async () => {
    console.log('Shutting down gracefully...');

    // Close all active browser sessions
    for (const [session_id, session] of activeSessions.entries()) {
        await session.context.close().catch(console.error);
        await session.browser.close().catch(console.error);
    }

    process.exit(0);
});