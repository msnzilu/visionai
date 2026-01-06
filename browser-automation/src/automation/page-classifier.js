// browser-automation/src/automation/page-classifier.js

/**
 * PageClassifier
 * 
 * A reusable component to determine the "type" of the current page.
 * Helps the automation engine decide whether to:
 * - Login (if 'login')
 * - Fill Form (if 'application')
 * - Click Apply (if 'job_description')
 */
class PageClassifier {
    constructor(page) {
        this.page = page;
    }

    /**
     * Classify the current page based on DOM heuristics
     * @returns {Promise<string>} 'login' | 'application' | 'job_description' | 'unknown'
     */
    async classify() {
        return await this.page.evaluate(() => {
            const url = window.location.href.toLowerCase();
            const title = document.title.toLowerCase();
            const textRaw = document.body.innerText.toLowerCase();

            // 1. Check for Login/Register Pages (Auth Walls)
            // Heuristic: Password field + Keywords
            const hasPasswordField = !!document.querySelector('input[type="password"]');

            const loginKeywords = ['login', 'sign in', 'signin', 'log in'];
            const registerKeywords = ['register', 'sign up', 'signup', 'create account', 'join'];

            const isLoginUrl = loginKeywords.some(k => url.includes(k));
            const isLoginTitle = loginKeywords.some(k => title.includes(k));

            const isRegisterUrl = registerKeywords.some(k => url.includes(k));
            const isRegisterTitle = registerKeywords.some(k => title.includes(k));

            // Strong signal: Password field represents specific intent
            if (hasPasswordField) {
                if (isLoginUrl || isLoginTitle) return 'login';
                if (isRegisterUrl || isRegisterTitle) return 'register';

                // Even without URL/Title match, a sparse page with a password field is likely a login/auth wall
                if (textRaw.length < 2000) return 'login';
            }

            // 2. Check for Application Page
            // Heuristic: File upload or significant form density + Apply keywords
            const hasFileUpload = !!document.querySelector('input[type="file"]');
            const applyKeywords = ['apply', 'application', 'submit'];
            const isApplyUrl = applyKeywords.some(k => url.includes(k));

            const forms = document.querySelectorAll('form');
            // Count "substantive" forms (more than just a search bar)
            const niceFormCount = Array.from(forms).filter(f =>
                f.querySelectorAll('input:not([type="hidden"]), select, textarea').length > 3
            ).length;

            if (hasFileUpload) return 'application'; // File upload is a very strong signal for ATS
            if (isApplyUrl && niceFormCount > 0) return 'application';
            if (niceFormCount > 0 && title.includes('apply')) return 'application';

            // 3. Check for Job Description / Landing Page
            // Heuristic: "Apply" button exists but no substantive forms yet
            const applyButtonRegex = /apply|start application/i;
            const buttons = Array.from(document.querySelectorAll('button, a, input[type="button"], input[type="submit"]'));

            // Check visible buttons only
            const hasApplyButton = buttons.some(b => {
                const text = b.innerText || b.value || '';
                const style = window.getComputedStyle(b);
                return applyButtonRegex.test(text) && style.display !== 'none' && style.visibility !== 'hidden';
            });

            if (hasApplyButton && niceFormCount === 0) {
                return 'job_description';
            }

            // Default
            return 'unknown';
        });
    }
}

module.exports = { PageClassifier };
