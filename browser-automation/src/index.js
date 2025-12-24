// browser-automation/src/index.js

const express = require('express');
const { chromium } = require('playwright');
const cors = require('cors');
const { AutofillEngine } = require('./automation/autofill');
const { FormDetector } = require('./automation/form-detector');
const { SiteHandlerFactory } = require('./automation/site-handlers/factory');

const app = express();
const PORT = process.env.PORT || 3000;
const AUTH_TOKEN = process.env.AUTH_TOKEN || 'dev-automation-token';

app.use(cors());
app.use(express.json({ limit: '10mb' }));

// Store active browser sessions
const activeSessions = new Map();

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
        const browser = await chromium.launch({
            headless: false,
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

        const formDetector = new FormDetector(page);
        const forms = await formDetector.detectForms();

        console.log(`Detected ${forms.length} forms on page`);

        // Log form details
        forms.forEach((form, index) => {
            console.log(`Form ${index + 1}:`, {
                fields: form.fields?.length || 0,
                fieldNames: form.fields?.map(f => f.name || f.id || f.placeholder).filter(Boolean)
            });
        });

        updateSessionStatus(session_id, 'filling_forms');

        const autofillEngine = new AutofillEngine(page, handler);
        const filledFields = await autofillEngine.fillForms(forms, autofillData);

        session.filled_fields = filledFields;
        updateSessionStatus(session_id, 'completed', null, filledFields);

        console.log(`Autofill completed for session ${session_id}`);
        console.log(`Filled ${filledFields.length} fields`);

        if (filledFields.length > 0) {
            console.log('Filled fields:', filledFields);
        }

        await page.screenshot({ path: `/tmp/completed-${session_id}.png` }).catch(() => { });

    } catch (error) {
        console.error(`Autofill failed for session ${session_id}:`, error);

        try {
            await page.screenshot({ path: `/tmp/error-${session_id}.png` });
            console.log(`Error screenshot saved: /tmp/error-${session_id}.png`);
        } catch (screenshotError) {
            console.error('Could not take error screenshot');
        }

        updateSessionStatus(session_id, 'error', error.message);
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