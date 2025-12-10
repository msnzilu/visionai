// Global configuration
const CONFIG = {
    BASE_URL: window.location.origin,
    API_BASE_URL: window.location.origin,
    API_PREFIX: '/api/v1',
    TOKEN_KEY: 'access_token',
    REFRESH_TOKEN_KEY: 'refresh_token',
    USER_KEY: 'cvision_user'
};

// Make CONFIG globally accessible for other scripts
window.CONFIG = CONFIG;

// Utility functions
const Utils = {
    // Local storage management
    setToken(token) {
        localStorage.setItem(CONFIG.TOKEN_KEY, token);
    },

    getToken() {
        return localStorage.getItem(CONFIG.TOKEN_KEY);
    },

    removeToken() {
        localStorage.removeItem(CONFIG.TOKEN_KEY);
        localStorage.removeItem(CONFIG.REFRESH_TOKEN_KEY);
        localStorage.removeItem(CONFIG.USER_KEY);
    },

    setRefreshToken(token) {
        localStorage.setItem(CONFIG.REFRESH_TOKEN_KEY, token);
    },

    getRefreshToken() {
        return localStorage.getItem(CONFIG.REFRESH_TOKEN_KEY);
    },

    setUser(user) {
        localStorage.setItem(CONFIG.USER_KEY, JSON.stringify(user));
    },

    getUser() {
        const user = localStorage.getItem(CONFIG.USER_KEY);
        return user ? JSON.parse(user) : null;
    },

    // Check if user is authenticated
    isAuthenticated() {
        return !!this.getToken();
    },

    // Decode JWT token
    decodeToken(token) {
        try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            return payload;
        } catch (e) {
            console.error('Failed to decode token:', e);
            return null;
        }
    },

    // Check if token is expiring soon (within 5 minutes)
    isTokenExpiringSoon(token) {
        const payload = this.decodeToken(token);
        if (!payload || !payload.exp) return true;

        const now = Date.now() / 1000;
        const timeUntilExpiry = payload.exp - now;
        return timeUntilExpiry < 300; // 5 minutes
    },

    // Check if token is expired
    isTokenExpired(token) {
        const payload = this.decodeToken(token);
        if (!payload || !payload.exp) return true;

        const now = Date.now() / 1000;
        return payload.exp < now;
    },

    // Format date
    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    },

    // Format file size
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },

    // Show alert message (Uses Toast if available, falls back to DOM)
    showAlert(message, type = 'info') {
        if (window.Toast) {
            window.Toast.show(message, type);
            return;
        }

        // Fallback for when Toast isn't loaded
        const alert = document.createElement('div');
        alert.className = `alert alert-${type}`;
        alert.textContent = message;

        // Insert at top of main content area
        const main = document.querySelector('main') || document.body;
        main.insertBefore(alert, main.firstChild);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (alert.parentNode) {
                alert.parentNode.removeChild(alert);
            }
        }, 5000);
    },

    // Show loading state
    showLoading(element, text = 'Loading...') {
        const loading = document.createElement('div');
        loading.className = 'loading-overlay';
        loading.innerHTML = `
            <div class="loading"></div>
            <span>${text}</span>
        `;
        element.appendChild(loading);
    },

    hideLoading(element) {
        const loading = element.querySelector('.loading-overlay');
        if (loading) {
            loading.remove();
        }
    },

    // Get appropriate login URL based on current context
    getLoginUrl() {
        return window.location.pathname.includes('/admin/') ? '/admin/login.html' : '/login.html';
    }
};

// API client
const API = {
    // Make authenticated request
    async request(endpoint, options = {}) {
        const url = `${CONFIG.API_BASE_URL}${CONFIG.API_PREFIX}${endpoint}`;
        const token = Utils.getToken();

        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };

        // Add authorization header if token exists
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }

        try {
            const response = await fetch(url, config);

            // Handle backend errors (502/503) - redirect to login
            if (response.status === 502 || response.status === 503) {
                console.error('Backend is down or unavailable, redirecting to login...');
                Utils.removeToken();
                Utils.removeToken();
                window.location.href = Utils.getLoginUrl();
                return;
            }

            // Try to parse JSON response
            let data;
            try {
                data = await response.json();
            } catch (jsonError) {
                // If JSON parse fails, backend is likely returning HTML (error page)
                console.error('Backend returned invalid JSON, likely down. Redirecting to login...');
                Utils.removeToken();
                Utils.removeToken();
                window.location.href = Utils.getLoginUrl();
                return;
            }

            // If unauthorized and we have a refresh token, try to refresh
            if (response.status === 401 && Utils.getRefreshToken()) {
                const refreshed = await this.refreshAccessToken();
                if (refreshed) {
                    // Retry the original request with new token
                    config.headers.Authorization = `Bearer ${Utils.getToken()}`;
                    const retryResponse = await fetch(url, config);
                    return await retryResponse.json();
                } else {
                    // Refresh failed, redirect to login
                    console.error('Token refresh failed, redirecting to login...');
                    Utils.removeToken();
                    Utils.removeToken();
                    window.location.href = Utils.getLoginUrl();
                    return;
                }
            }

            // If still unauthorized after refresh attempt, redirect to login
            if (response.status === 401) {
                console.error('Unauthorized, redirecting to login...');
                Utils.removeToken();
                Utils.removeToken();
                window.location.href = Utils.getLoginUrl();
                return;
            }

            if (!response.ok) {
                throw new Error(data.detail || data.message || 'Request failed');
            }

            return data;
        } catch (error) {
            console.error('API Error:', error);

            // If it's a network error, backend is likely down
            if (error.message.includes('fetch') || error.name === 'TypeError') {
                console.error('Network error, backend may be down. Redirecting to login...');
                Utils.removeToken();
                Utils.removeToken();
                window.location.href = Utils.getLoginUrl();
                return;
            }

            throw error;
        }
    },

    // Auth endpoints - FROM ORIGINAL (WORKING)
    async register(userData) {
        return this.request('/auth/register', {
            method: 'POST',
            body: JSON.stringify(userData)
        });
    },

    async login(credentials) {
        return this.request('/auth/login', {
            method: 'POST',
            body: JSON.stringify(credentials)
        });
    },

    async logout() {
        return this.request('/auth/logout', {
            method: 'POST'
        });
    },

    async getProfile() {
        return this.request('/auth/me');
    },

    // Refresh access token
    async refreshAccessToken() {
        try {
            const refreshToken = Utils.getRefreshToken();
            if (!refreshToken) {
                return false;
            }

            const response = await fetch(`${CONFIG.API_BASE_URL}${CONFIG.API_PREFIX}/auth/refresh`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ refresh_token: refreshToken })
            });

            const data = await response.json();

            if (data.success && data.data.access_token) {
                Utils.setToken(data.data.access_token);
                return true;
            }

            // Refresh failed, clear tokens
            Utils.removeToken();
            return false;
        } catch (error) {
            console.error('Token refresh failed:', error);
            Utils.removeToken();
            return false;
        }
    },

    // Document endpoints
    async uploadDocument(file) {
        const formData = new FormData();
        formData.append('file', file);

        return this.request('/documents/upload', {
            method: 'POST',
            body: formData,
            headers: {} // Remove Content-Type to let browser set it for FormData
        });
    },

    async getDocuments() {
        return this.request('/documents/');
    },

    async getDocument(documentId) {
        return this.request(`/documents/${documentId}`);
    },

    async deleteDocument(documentId) {
        return this.request(`/documents/${documentId}`, {
            method: 'DELETE'
        });
    },

    async analyzeDocument(documentId) {
        return this.request(`/documents/${documentId}/analyze`, {
            method: 'POST'
        });
    }
};

// File upload component
class FileUpload {
    constructor(elementId, options = {}) {
        this.element = document.getElementById(elementId);
        this.options = {
            allowedTypes: ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain'],
            maxSize: 10 * 1024 * 1024, // 10MB
            onUpload: null,
            onProgress: null,
            onError: null,
            ...options
        };

        this.init();
    }

    init() {
        if (!this.element) return;

        // Create file input
        this.fileInput = document.createElement('input');
        this.fileInput.type = 'file';
        this.fileInput.style.display = 'none';
        this.fileInput.accept = '.pdf,.docx,.doc,.txt';

        this.element.appendChild(this.fileInput);

        // Add event listeners
        this.element.addEventListener('click', () => this.fileInput.click());
        this.element.addEventListener('dragover', this.handleDragOver.bind(this));
        this.element.addEventListener('dragleave', this.handleDragLeave.bind(this));
        this.element.addEventListener('drop', this.handleDrop.bind(this));
        this.fileInput.addEventListener('change', this.handleFileSelect.bind(this));
    }

    handleDragOver(e) {
        e.preventDefault();
        this.element.classList.add('dragover');
    }

    handleDragLeave(e) {
        e.preventDefault();
        this.element.classList.remove('dragover');
    }

    handleDrop(e) {
        e.preventDefault();
        this.element.classList.remove('dragover');

        const files = Array.from(e.dataTransfer.files);
        if (files.length > 0) {
            this.processFile(files[0]);
        }
    }

    handleFileSelect(e) {
        const files = Array.from(e.target.files);
        if (files.length > 0) {
            this.processFile(files[0]);
        }
    }

    processFile(file) {
        // Validate file
        if (!this.validateFile(file)) {
            return;
        }

        // Show progress
        this.showProgress();

        // Upload file
        this.uploadFile(file);
    }

    validateFile(file) {
        // Check file type
        if (!this.options.allowedTypes.includes(file.type)) {
            const error = 'Invalid file type. Please upload PDF, DOCX, or TXT files.';
            this.showError(error);
            return false;
        }

        // Check file size
        if (file.size > this.options.maxSize) {
            const error = `File size exceeds ${Utils.formatFileSize(this.options.maxSize)} limit.`;
            this.showError(error);
            return false;
        }

        return true;
    }

    async uploadFile(file) {
        try {
            const result = await API.uploadDocument(file);

            if (result.success) {
                this.showSuccess('CV uploaded and processed successfully!');
                if (this.options.onUpload) {
                    this.options.onUpload(result.data);
                }
            } else {
                throw new Error(result.message || 'Upload failed');
            }
        } catch (error) {
            this.showError(error.message);
            if (this.options.onError) {
                this.options.onError(error);
            }
        } finally {
            this.hideProgress();
        }
    }

    showProgress() {
        this.element.innerHTML = `
            <div class="file-upload-progress">
                <div class="loading"></div>
                <div class="file-upload-text">Processing your CV...</div>
                <div class="progress">
                    <div class="progress-bar" style="width: 100%"></div>
                </div>
            </div>
        `;
    }

    hideProgress() {
        this.resetUI();
    }

    showSuccess(message) {
        this.element.innerHTML = `
            <div class="file-upload-success">
                <div class="file-upload-icon">✅</div>
                <div class="file-upload-text">${message}</div>
            </div>
        `;

        // Reset after 3 seconds
        setTimeout(() => this.resetUI(), 3000);
    }

    showError(message) {
        this.element.innerHTML = `
            <div class="file-upload-error">
                <div class="file-upload-icon">❌</div>
                <div class="file-upload-text">Error: ${message}</div>
                <div class="file-upload-hint">Please try again</div>
            </div>
        `;

        // Reset after 5 seconds
        setTimeout(() => this.resetUI(), 5000);
    }

    resetUI() {
        this.element.innerHTML = `
            <div class="file-upload-icon">📄</div>
            <div class="file-upload-text">Drop your CV here or click to browse</div>
            <div class="file-upload-hint">Supports PDF, DOCX, and TXT files (max 10MB)</div>
        `;
    }
}

// Auth guard for protected pages
function requireAuth() {
    if (!Utils.isAuthenticated()) {
        window.location.href = 'login.html';
        return false;
    }
    return true;
}

// Initialize user info display
function initUserInfo() {
    const user = Utils.getUser();
    if (user) {
        const userElements = document.querySelectorAll('.user-name');
        userElements.forEach(el => {
            el.textContent = user.full_name || user.email;
        });
    }
}

// Logout functionality
function logout() {
    Utils.removeToken();
    window.location.href = Utils.getLoginUrl();
}

// Redirect authenticated users away from public pages
function redirectIfAuthenticated() {
    const publicPages = ['login.html', 'register.html'];
    const currentPage = window.location.pathname.split('/').pop();

    if (publicPages.includes(currentPage) && Utils.isAuthenticated()) {
        window.location.href = '/dashboard.html';
    }
}

// Auto-redirect on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', redirectIfAuthenticated);
} else {
    redirectIfAuthenticated();
}

// Global error handler
window.addEventListener('error', (e) => {
    console.error('Global error:', e.error);
});

// Global unhandled promise rejection handler
window.addEventListener('unhandledrejection', (e) => {
    console.error('Unhandled promise rejection:', e.reason);
});

// Load footer component
async function loadFooter() {
    const footerContainer = document.getElementById('footer-container');
    if (footerContainer) {
        try {
            const response = await fetch('/components/footer.html');
            if (response.ok) {
                const html = await response.text();
                footerContainer.innerHTML = html;
            }
        } catch (error) {
            console.error('Failed to load footer:', error);
        }
    }
}

// Load footer on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', loadFooter);
} else {
    loadFooter();
}

// Expose globals
window.CVision = {
    Utils,
    API,
    FileUpload,
    requireAuth,
    initUserInfo,
    logout,
    isAuthenticated: () => Utils.isAuthenticated(),
    getToken: () => Utils.getToken(),
    getUser: () => Utils.getUser(),
    setUser: (user) => Utils.setUser(user),
    setToken: (token) => Utils.setToken(token),
    showAlert: (message, type) => Utils.showAlert(message, type),
    showMessage: (message, type) => Utils.showAlert(message, type), // Alias for showAlert
    formatDate: (date) => Utils.formatDate(date),
    formatFileSize: (size) => Utils.formatFileSize(size)
};