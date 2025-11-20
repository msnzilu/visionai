// browser-automation/src/index.js

const express = require('express');
const puppeteer = require('puppeteer');
const cors = require('cors');
const { AutofillEngine } = require('./automation/autofill');
const { FormDetector } = require('./automation/form-detector');
const { SiteHandlerFactory } = require('./automation/site-handlers/factory');

const app = express();
const PORT = process.env.PORT || 3001;
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
        service: 'Browser Automation Service',
        active_sessions: activeSessions.size
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
        
        // Launch browser
        const browser = await puppeteer.launch({
            headless: false, // Show browser to user
            args: [
                '--start-maximized',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-blink-features=AutomationControlled'
            ],
            defaultViewport: null
        });
        
        const page = await browser.newPage();
        
        // Set realistic user agent
        await page.setUserAgent(
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ' +
            '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        );
        
        // Remove webdriver flag
        await page.evaluateOnNewDocument(() => {
            Object.defineProperty(navigator, 'webdriver', {
                get: () => false,
            });
        });
        
        // Store session
        activeSessions.set(session_id, {
            browser,
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
        await session.browser.close();
        activeSessions.delete(session_id);
        res.json({ message: 'Session closed successfully' });
    } catch (error) {
        res.status(500).json({ error: 'Failed to close session' });
    }
});

async function performAutofill(session_id, url, autofillData, jobSource, page) {
    const session = activeSessions.get(session_id);
    if (!session) return;
    
    try {
        updateSessionStatus(session_id, 'navigating');
        
        // Navigate to application page
        await page.goto(url, { 
            waitUntil: 'networkidle0',
            timeout: 30000 
        });
        
        await page.waitForTimeout(2000); // Wait for page to stabilize
        
        updateSessionStatus(session_id, 'detecting_forms');
        
        // Get site-specific handler
        const handler = SiteHandlerFactory.getHandler(url, jobSource);
        
        // Detect forms on page
        const formDetector = new FormDetector(page);
        const forms = await formDetector.detectForms();
        
        console.log(`Detected ${forms.length} forms on page`);
        
        updateSessionStatus(session_id, 'filling_forms');
        
        // Initialize autofill engine
        const autofillEngine = new AutofillEngine(page, handler);
        
        // Perform autofill
        const filledFields = await autofillEngine.fillForms(
            forms,
            autofillData
        );
        
        session.filled_fields = filledFields;
        updateSessionStatus(session_id, 'completed', null, filledFields);
        
        console.log(`Autofill completed for session ${session_id}`);
        console.log(`Filled ${filledFields.length} fields`);
        
    } catch (error) {
        console.error(`Autofill failed for session ${session_id}:`, error);
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
            session.browser.close().catch(console.error);
            activeSessions.delete(session_id);
        }
    }
}, 5 * 60 * 1000); // Check every 5 minutes

app.listen(PORT, () => {
    console.log(`Browser Automation Service running on port ${PORT}`);
    console.log(`Active sessions will be cleaned up after 30 minutes of inactivity`);
});

process.on('SIGTERM', async () => {
    console.log('Shutting down gracefully...');
    
    // Close all active browser sessions
    for (const [session_id, session] of activeSessions.entries()) {
        await session.browser.close().catch(console.error);
    }
    
    process.exit(0);
});