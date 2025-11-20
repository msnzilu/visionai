/**
 * Auth Guard - Protects pages that require authentication
 * Add this script to any page that needs protection
 */

(function() {
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
            // Optionally verify token is valid
            verifyToken(token);
        }
    }

    // Optional: Verify token validity
    function verifyToken(token) {
        // You can add token expiration check here if needed
        try {
            // Decode JWT to check expiration
            const payload = JSON.parse(atob(token.split('.')[1]));
            const now = Date.now() / 1000;
            
            if (payload.exp && payload.exp < now) {
                console.log('Token expired. Redirecting to login...');
                localStorage.removeItem('access_token');
                localStorage.removeItem('cvision_user');
                window.location.href = '/login.html';
            }
        } catch (e) {
            console.error('Invalid token format:', e);
            // Don't redirect on parse error, let the API handle it
        }
    }
})();