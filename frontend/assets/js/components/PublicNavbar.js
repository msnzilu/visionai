/**
 * PublicNavbar Component
 * Handles loading, toggling, and active state for the public-facing navbar.
 */
const PublicNavbar = (function () {
    let isInitialized = false;

    /**
     * Set up global event listeners for the navbar using delegation.
     */
    function setupEventListeners() {
        if (isInitialized) return;

        document.addEventListener('click', (e) => {
            // Mobile Menu Toggle
            const mobileBtn = e.target.closest('#mobile-menu-button');
            if (mobileBtn) {
                const mobileMenu = document.getElementById('mobile-menu');
                if (mobileMenu) {
                    mobileMenu.classList.toggle('hidden');
                }
            }
        });

        isInitialized = true;
    }

    /**
     * Highlights the active navigation link based on the current URL.
     */
    function setActiveLink() {
        // Get path and remove trailing slash if it exists
        let currentPage = window.location.pathname.replace(/\/$/, '');
        const navLinks = document.querySelectorAll('.nav-link');

        navLinks.forEach(link => {
            let linkHref = link.getAttribute('href');
            if (!linkHref) return;

            // Remove .html from link comparison if present
            let comparedHref = linkHref.replace(/\.html$/, '').replace(/\/$/, '');

            // Ensure absolute comparison
            if (!comparedHref.startsWith('/')) {
                comparedHref = '/' + comparedHref;
            }

            if (comparedHref === currentPage ||
                (currentPage === '' && comparedHref === '/') ||
                (currentPage === '/' && comparedHref === '/')) {
                link.classList.remove('text-gray-600');
                link.classList.add('text-primary-600', 'font-semibold');
            }
        });
    }

    /**
     * Loads the navbar HTML into a specified container.
     * @param {string} containerId - The ID of the container element.
     */
    async function load(containerId = 'public-navbar-container') {
        const container = document.getElementById(containerId);
        if (!container) return;

        try {
            const response = await fetch('/components/public-navbar.html');
            if (response.ok) {
                const html = await response.text();
                container.innerHTML = html;

                // Initialize functionality after loading
                setupEventListeners();
                setActiveLink();

                // Hide specific links on landing page
                // Hide specific links and add Upload CV button on landing page
                const path = window.location.pathname;
                if (path === '/' || path === '/index.html') {
                    const linksToHide = ['/features', '/how-it-works', '/pricing', '/info/help'];
                    linksToHide.forEach(href => {
                        const links = container.querySelectorAll(`a[href="${href}"]`);
                        links.forEach(link => link.classList.add('hidden'));
                    });

                    // Inject Upload CV button for Desktop
                    const navContainer = container.querySelector('.hidden.md\\:flex');
                    if (navContainer) {
                        const uploadBtn = document.createElement('button');
                        uploadBtn.id = 'nav-upload-btn';
                        uploadBtn.className = 'nav-link text-gray-600 hover:text-primary-600 transition-colors font-medium mr-4';
                        uploadBtn.innerHTML = `
                            <span class="flex items-center gap-2">
                                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"></path></svg>
                                Upload CV
                            </span>
                        `;

                        // Insert before Register (Get Started) button
                        const registerBtn = navContainer.querySelector('a[href="/register"]');
                        if (registerBtn) {
                            navContainer.insertBefore(uploadBtn, registerBtn);
                        }
                    }
                }
            } else {
                console.error('PublicNavbar: Failed to fetch navbar HTML');
            }
        } catch (error) {
            console.error('PublicNavbar: Error loading navbar:', error);
        }
    }

    // Initialize listeners immediately if script is loaded
    // This allows delegation to work even if the navbar hasn't been injected yet
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', setupEventListeners);
    } else {
        setupEventListeners();
    }

    return {
        load,
        init: setupEventListeners,
        setActiveLink
    };
})();

// Expose to window
window.PublicNavbar = PublicNavbar;
