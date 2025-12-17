// CVision Authentication JavaScript

document.addEventListener('DOMContentLoaded', function () {
    // Check if user is already authenticated
    if (CVision && CVision.Utils && CVision.Utils.isAuthenticated()) {
        window.location.href = 'dashboard.html';
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
                window.location.href = 'dashboard.html';
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
            window.location.href = `verification-pending.html?email=${encodeURIComponent(email)}`;
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

        const googleButton = document.getElementById('googleLogin') || document.getElementById('googleSignup');
        if (googleButton) {
            googleButton.disabled = false;
            googleButton.textContent = 'Continue with Google';
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

        const linkedinButton = document.getElementById('linkedinLogin') || document.getElementById('linkedinSignup');
        if (linkedinButton) {
            linkedinButton.disabled = false;
            linkedinButton.textContent = 'Continue with LinkedIn';
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