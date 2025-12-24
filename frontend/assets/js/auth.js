// CVision Authentication JavaScript

document.addEventListener('DOMContentLoaded', function () {
    // Check if user is already authenticated
    if (CVision && CVision.Utils && CVision.Utils.isAuthenticated()) {
        window.location.href = '/dashboard';
        return;
    }

    // Initialize ForgotPasswordModal if available and needed
    const forgotPasswordLink = document.getElementById('forgotPasswordLink');
    if (forgotPasswordLink && typeof ForgotPasswordModal !== 'undefined') {
        const forgotPasswordModal = new ForgotPasswordModal();
        forgotPasswordLink.addEventListener('click', (e) => {
            e.preventDefault();
            forgotPasswordModal.open();
        });
    }

    // Initialize based on which form exists on the page
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');

    if (loginForm) {
        initializeLoginPage();
    }

    if (registerForm) {
        initializeRegisterPage();
    }

    // Initialize social login buttons (common to both pages)
    initializeSocialLogin();
});

function initializeLoginPage() {
    const form = document.getElementById('loginForm');
    const loginButton = document.getElementById('loginButton');
    const togglePassword = document.getElementById('togglePassword');

    // Check for URL parameters
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('verified') === 'true') {
        // Wait for modal to be initialized
        setTimeout(() => {
            if (window.GenericModal && window.GenericModal.instance) {
                window.GenericModal.instance.show({
                    title: 'Email Verified!',
                    message: 'Your email has been successfully verified. You can now sign in to your account.',
                    type: 'success',
                    buttonText: 'Got it'
                });
            } else {
                // Fallback if modal script not loaded yet
                InlineMessage.success('Email verified successfully! Please sign in.');
            }
        }, 300); // Small delay to ensure DOM is ready
    }

    // Password toggle functionality
    if (togglePassword) {
        const passwordInput = document.getElementById('password');
        if (passwordInput) {
            togglePassword.addEventListener('click', function () {
                const type = passwordInput.type === 'password' ? 'text' : 'password';
                passwordInput.type = type;
            });
        }
    }

    // Form submission handler
    if (form) {
        form.addEventListener('submit', async function (e) {
            e.preventDefault();
            await handleLogin();
        });
    }

    // Forgot password modal handler
    const forgotPasswordLink = document.getElementById('forgotPasswordLink');
    const forgotPasswordModal = document.getElementById('forgotPasswordModal');
    const closeForgotModal = document.getElementById('closeForgotModal');

    if (forgotPasswordLink && forgotPasswordModal) {
        forgotPasswordLink.addEventListener('click', function (e) {
            e.preventDefault();
            forgotPasswordModal.classList.remove('hidden');
        });
    }

    if (closeForgotModal && forgotPasswordModal) {
        closeForgotModal.addEventListener('click', function () {
            forgotPasswordModal.classList.add('hidden');
        });
    }
}

function initializeRegisterPage() {
    const form = document.getElementById('registerForm');
    const registerButton = document.getElementById('registerButton');
    const togglePassword = document.getElementById('togglePassword');

    // Password toggle functionality
    if (togglePassword) {
        const passwordInput = document.getElementById('password');
        if (passwordInput) {
            togglePassword.addEventListener('click', function () {
                const type = passwordInput.type === 'password' ? 'text' : 'password';
                passwordInput.type = type;
            });
        }
    }

    // Form submission handler
    if (form) {
        form.addEventListener('submit', async function (e) {
            e.preventDefault();
            await handleRegister();
        });
    }
}

function initializeSocialLogin() {
    const googleButton = document.getElementById('googleLogin') || document.getElementById('googleSignup');
    const linkedinButton = document.getElementById('linkedinLogin') || document.getElementById('linkedinSignup');

    if (googleButton) {
        googleButton.addEventListener('click', handleGoogleLogin);
    }

    if (linkedinButton) {
        linkedinButton.addEventListener('click', handleLinkedInLogin);
    }
}

async function handleLogin() {
    const emailInput = document.getElementById('email');
    const passwordInput = document.getElementById('password');
    const loginButton = document.getElementById('loginButton');

    if (!emailInput || !passwordInput) {
        return;
    }

    // Clear previous errors
    InlineMessage.clear();

    // Get form values
    const email = emailInput.value.trim();
    const password = passwordInput.value;
    const rememberMe = document.getElementById('rememberMe')?.checked || false;

    // Validate inputs
    if (!validateLoginForm(email, password)) {
        return;
    }

    try {
        // Show loading state
        if (loginButton) {
            setButtonLoading(loginButton, true);
        }

        // Detect location
        let location = null;
        try {
            // Check if CVision.Geolocation exists
            if (CVision.Geolocation) {
                const geoData = await CVision.Geolocation.detect();
                if (geoData && geoData.detected) {
                    location = {
                        code: geoData.countryCode,
                        name: geoData.countryName,
                        currency: geoData.currency
                    };
                }
            }
        } catch (err) {
            console.warn('Geolocation detection failed:', err);
        }

        // Make login request
        const response = await CVision.API.login({
            email: email,
            password: password,
            remember_me: rememberMe,
            location: location
        });

        if (response.success) {
            // Store tokens and user data
            CVision.Utils.setToken(response.data.access_token);
            if (response.data.refresh_token) {
                CVision.Utils.setRefreshToken(response.data.refresh_token);
            }
            CVision.Utils.setUser(response.data.user);

            // Start token refresh timer
            if (typeof CVision.startTokenRefreshTimer === 'function') {
                CVision.startTokenRefreshTimer();
            }

            InlineMessage.success('Logged In successfully! Redirecting to Dashboard...');

            // Redirect to dashboard
            setTimeout(() => {
                window.location.href = '/dashboard';
            }, 1000);
        } else {
            throw new Error(response.message || 'Login failed');
        }

    } catch (error) {
        console.error('Login error:', error);

        const errorMessage = error.message || 'Login failed. Please try again.';

        if (window.GenericModal && window.GenericModal.instance) {
            window.GenericModal.instance.show({
                title: 'Login Failed',
                message: errorMessage,
                type: 'error'
            });
        } else {
            InlineMessage.error(errorMessage);
        }

    } finally {
        if (loginButton) {
            setButtonLoading(loginButton, false);
        }
    }
}

async function handleRegister() {
    const emailInput = document.getElementById('email');
    const passwordInput = document.getElementById('password');
    const termsInput = document.getElementById('terms');
    const registerButton = document.getElementById('registerButton');

    if (!emailInput || !passwordInput) {
        console.error('Register form inputs not found');
        return;
    }

    // Clear previous errors
    InlineMessage.clear();

    // Get form values
    const email = emailInput.value.trim();
    const password = passwordInput.value;
    const termsAccepted = termsInput ? termsInput.checked : false;

    // Validate inputs
    if (!validateRegisterForm(email, password, termsAccepted)) {
        return;
    }

    try {
        // Show loading state
        if (registerButton) {
            setButtonLoading(registerButton, true);
        }

        // Make register request
        const response = await CVision.API.register({
            email: email,
            password: password
        });

        if (response.success) {
            // Redirect to verification pending page
            window.location.href = `/verification-pending?email=${encodeURIComponent(email)}`;
        } else {
            throw new Error(response.message || 'Registration failed');
        }


    } catch (error) {
        console.error('Registration error:', error);

        const errorMessage = error.message || 'Registration failed. Please try again.';

        if (window.GenericModal && window.GenericModal.instance) {
            window.GenericModal.instance.show({
                title: 'Registration Failed',
                message: errorMessage,
                type: 'error'
            });
        } else {
            InlineMessage.error(errorMessage);
        }

    } finally {
        if (registerButton) {
            setButtonLoading(registerButton, false);
        }
    }
}

function validateLoginForm(email, password) {
    let errors = [];

    // Validate email
    if (!email) {
        errors.push('Email is required');
    } else if (!isValidEmail(email)) {
        errors.push('Please enter a valid email address');
    }

    // Validate password
    if (!password) {
        errors.push('Password is required');
    }

    if (errors.length > 0) {
        if (window.GenericModal && window.GenericModal.instance) {
            window.GenericModal.instance.show({
                title: 'Validation Error',
                message: errors.join('\n'),
                type: 'error'
            });
        } else {
            InlineMessage.error(errors.join('. '));
        }
        return false;
    }

    return true;
}

function validateRegisterForm(email, password, termsAccepted) {
    let errors = [];

    // Validate email
    if (!email) {
        errors.push('Email is required');
    } else if (!isValidEmail(email)) {
        errors.push('Please enter a valid email address');
    }

    // Validate password
    if (!password) {
        errors.push('Password is required');
    } else if (password.length < 6) {
        errors.push('Password must be at least 6 characters long');
    }

    // Validate terms
    if (!termsAccepted) {
        errors.push('You must agree to the Terms of Service');
    }

    if (errors.length > 0) {
        if (window.GenericModal && window.GenericModal.instance) {
            window.GenericModal.instance.show({
                title: 'Validation Error',
                message: errors.join('\n'),
                type: 'error'
            });
        } else {
            InlineMessage.error(errors.join('. '));
        }
        return false;
    }

    return true;
}

function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

function setButtonLoading(button, loading) {
    if (!button) return;

    const textElement = button.querySelector('.button-text');
    const spinnerElement = button.querySelector('.loading-spinner');

    if (loading) {
        button.disabled = true;
        button.classList.add('opacity-75', 'cursor-not-allowed');
        if (textElement) textElement.classList.add('opacity-0');
        if (spinnerElement) spinnerElement.classList.remove('hidden');
    } else {
        button.disabled = false;
        button.classList.remove('opacity-75', 'cursor-not-allowed');
        if (textElement) textElement.classList.remove('opacity-0');
        if (spinnerElement) spinnerElement.classList.add('hidden');
    }
}

async function handleGoogleLogin() {
    try {
        const googleButton = document.getElementById('googleLogin') || document.getElementById('googleSignup');
        if (googleButton) {
            googleButton.disabled = true;
            googleButton.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Connecting...';
        }

        // Detect location before redirecting
        let locationParam = '';
        try {
            if (CVision.Geolocation) {
                const geoData = await CVision.Geolocation.detect();
                if (geoData && geoData.detected) {
                    const locationData = {
                        code: geoData.countryCode,
                        name: geoData.countryName,
                        currency: geoData.currency
                    };
                    locationParam = `?location=${encodeURIComponent(JSON.stringify(locationData))}`;
                }
            }
        } catch (err) {
            console.warn('Geolocation detection failed for Google login:', err);
        }

        // Use YOUR actual API structure
        const url = `${CONFIG.API_BASE_URL}${CONFIG.API_PREFIX}/auth/google/login${locationParam}`;
        const response = await fetch(url);
        const data = await response.json();

        if (data.success && data.auth_url) {
            window.location.href = data.auth_url;
        } else {
            throw new Error('Failed to initiate Google login');
        }

    } catch (error) {
        console.error('Google login error:', error);

        if (window.GenericModal && window.GenericModal.instance) {
            window.GenericModal.instance.show({
                title: 'Login Error',
                message: 'Google login failed. Please try again.',
                type: 'error'
            });
        } else {
            InlineMessage.error('Google login failed. Please try again.', {
                autoHide: true,
                autoHideDelay: 4000
            });
        }

        if (googleButton) {
            googleButton.disabled = false;
            googleButton.innerHTML = `
                <svg class="w-5 h-5 mr-3" viewBox="0 0 24 24">
                    <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                    <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                    <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
                    <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
                </svg>
                Continue with Google
            `;
        }
    }
}

async function handleLinkedInLogin() {
    try {
        const linkedinButton = document.getElementById('linkedinLogin') || document.getElementById('linkedinSignup');
        if (linkedinButton) {
            linkedinButton.disabled = true;
            linkedinButton.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Connecting...';
        }

        // Use YOUR actual API structure
        const url = `${CONFIG.API_BASE_URL}${CONFIG.API_PREFIX}/auth/linkedin/login`;
        const response = await fetch(url);
        const data = await response.json();

        if (data.success && data.auth_url) {
            window.location.href = data.auth_url;
        } else {
            throw new Error('Failed to initiate LinkedIn login');
        }

    } catch (error) {
        console.error('LinkedIn login error:', error);

        if (window.GenericModal && window.GenericModal.instance) {
            window.GenericModal.instance.show({
                title: 'Login Error',
                message: 'LinkedIn login failed. Please try again.',
                type: 'error'
            });
        } else {
            InlineMessage.error('LinkedIn login failed. Please try again.', {
                autoHide: true,
                autoHideDelay: 4000
            });
        }

        if (linkedinButton) {
            linkedinButton.disabled = false;
            linkedinButton.innerHTML = `
                <svg class="w-5 h-5 mr-3" viewBox="0 0 24 24">
                    <path fill="#0A66C2" d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" />
                </svg>
                Continue with LinkedIn
            `;
        }
    }
}

// Export functions for external use if needed
window.CVisionAuth = {
    handleLogin,
    handleRegister,
    handleGoogleLogin,
    handleLinkedInLogin,
    validateLoginForm,
    validateRegisterForm,
    setButtonLoading
};