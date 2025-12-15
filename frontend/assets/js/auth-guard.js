/**
 * Auth Guard - Protects pages that require authentication
 * Add this script to any page that needs protection
 */

(function () {
    // Pages that DON'T require authentication
    const publicPages = [
        'index.html',
        'login.html',
        'register.html',
        'auth-callback.html',
        '/', // root
        ''   // empty (root)
    ];

    // Get current page
    const currentPage = window.location.pathname.split('/').pop() || 'index.html';

    // Check if current page is public
    const isPublicPage = publicPages.some(page =>
        currentPage === page || currentPage === '' || currentPage === '/'
    );

    // If not a public page, require authentication
    if (!isPublicPage) {
        // Check if user is authenticated
        const token = localStorage.getItem('access_token');

        if (!token) {
            // Not authenticated - redirect to login
            console.log('Authentication required. Redirecting to login...');
            window.location.href = '/login.html';
        } else {
            // Verify token is valid and attempt refresh if needed
            verifyAndRefreshToken(token);
        }
    }

    // Verify token validity and refresh if needed
    async function verifyAndRefreshToken(token) {
        try {
            // Decode JWT to check expiration
            const payload = JSON.parse(atob(token.split('.')[1]));
            const now = Date.now() / 1000;

            // If token is expired, try to refresh
            if (payload.exp && payload.exp < now) {
                console.log('Token expired. Attempting refresh...');
                const refreshToken = localStorage.getItem('refresh_token');

                if (refreshToken) {
                    // Attempt to refresh the token
                    const refreshed = await attemptTokenRefresh(refreshToken);
                    if (!refreshed) {
                        // Refresh failed, redirect to login
                        console.log('Token refresh failed. Redirecting to login...');
                        localStorage.removeItem('access_token');
                        localStorage.removeItem('refresh_token');
                        localStorage.removeItem('cvision_user');
                        window.location.href = '/login.html';
                    }
                } else {
                    // No refresh token, redirect to login
                    console.log('No refresh token available. Redirecting to login...');
                    localStorage.removeItem('access_token');
                    localStorage.removeItem('cvision_user');
                    window.location.href = '/login.html';
                }
            }
        } catch (e) {
            console.error('Token verification error:', e);
            // Critical auth error - redirect to login
            console.log('Critical auth error. Redirecting to login...');
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            localStorage.removeItem('cvision_user');
            window.location.href = '/login.html';
        }
    }

    // Attempt to refresh the access token
    async function attemptTokenRefresh(refreshToken) {
        try {
            // Get base URL - try window.CONFIG first, then CVision.config, then fallback to origin
            let baseUrl = window.location.origin;

            if (window.CONFIG && window.CONFIG.API_BASE_URL) {
                baseUrl = window.CONFIG.API_BASE_URL;
            } else if (window.CVision && window.CVision.config && window.CVision.config.API_BASE_URL) {
                baseUrl = window.CVision.config.API_BASE_URL;
            }

            // Remove trailing slash if present
            if (baseUrl.endsWith('/')) {
                baseUrl = baseUrl.slice(0, -1);
            }

            const response = await fetch(`${baseUrl}/api/v1/auth/refresh`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ refresh_token: refreshToken })
            });

            const data = await response.json();

            if (data.success && data.data.access_token) {
                localStorage.setItem('access_token', data.data.access_token);
                console.log('Token refreshed successfully');
                return true;
            }

            return false;
        } catch (error) {
            console.error('Token refresh error:', error);
            return false;
        }
    }
})();