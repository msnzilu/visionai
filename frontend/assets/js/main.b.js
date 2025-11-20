// Global configuration
const CONFIG = {
    API_BASE_URL: 'http://localhost:8000',
    API_PREFIX: '/api/v1',
    TOKEN_KEY: 'access_token',
    USER_KEY: 'cvision_user'
};

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
        localStorage.removeItem(CONFIG.USER_KEY);
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

    // Show alert message
    showAlert(message, type = 'info') {
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
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || data.message || 'Request failed');
            }

            return data;
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    },

    // Auth endpoints
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

// Document manager
class DocumentManager {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.documents = [];
    }

    async loadDocuments() {
        try {
            const response = await API.getDocuments();
            this.documents = response.data.documents;
            this.render();
        } catch (error) {
            Utils.showAlert(`Error loading documents: ${error.message}`, 'error');
        }
    }

    render() {
        if (!this.container) return;

        if (this.documents.length === 0) {
            this.container.innerHTML = `
                <div class="card text-center">
                    <div class="card-header">
                        <h3 class="card-title">No Documents Yet</h3>
                    </div>
                    <p>Upload your first CV to get started with CVision!</p>
                </div>
            `;
            return;
        }

        const documentsHtml = this.documents.map(doc => this.renderDocument(doc)).join('');
        this.container.innerHTML = `
            <div class="documents-grid">
                ${documentsHtml}
            </div>
        `;

        // Add event listeners
        this.addEventListeners();
    }

    renderDocument(doc) {
        const uploadDate = Utils.formatDate(doc.created_at);
        const fileSize = Utils.formatFileSize(doc.file_info.file_size);
        
        return `
            <div class="card document-card" data-document-id="${doc._id}">
                <div class="card-header">
                    <h4 class="card-title">${doc.file_info.filename}</h4>
                    <div class="card-subtitle">${uploadDate} • ${fileSize}</div>
                </div>
                <div class="document-info">
                    ${this.renderCVData(doc.cv_data)}
                </div>
                <div class="document-actions">
                    <button class="btn btn-secondary view-btn" data-action="view">
                        View Details
                    </button>
                    <button class="btn btn-primary analyze-btn" data-action="analyze">
                        Re-analyze
                    </button>
                    <button class="btn btn-danger delete-btn" data-action="delete">
                        Delete
                    </button>
                </div>
            </div>
        `;
    }

    renderCVData(cvData) {
        if (!cvData || cvData.error) {
            return `
                <div class="alert alert-warning">
                    <strong>Processing Error:</strong> ${cvData?.error || 'Failed to process CV'}
                </div>
            `;
        }

        const personalInfo = cvData.personal_info || {};
        const skills = cvData.skills || [];
        const experience = cvData.work_experience || [];

        return `
            <div class="cv-summary">
                <div class="cv-field">
                    <strong>Name:</strong> ${personalInfo.name || 'Not found'}
                </div>
                <div class="cv-field">
                    <strong>Email:</strong> ${personalInfo.email || 'Not found'}
                </div>
                <div class="cv-field">
                    <strong>Skills:</strong> 
                    ${Array.isArray(skills) ? skills.slice(0, 5).join(', ') : 'Not found'}
                    ${skills.length > 5 ? '...' : ''}
                </div>
                <div class="cv-field">
                    <strong>Experience:</strong> ${experience.length} positions
                </div>
            </div>
        `;
    }

    addEventListeners() {
        this.container.addEventListener('click', async (e) => {
            const action = e.target.dataset.action;
            const documentCard = e.target.closest('.document-card');
            const documentId = documentCard?.dataset.documentId;

            if (!documentId) return;

            switch (action) {
                case 'view':
                    await this.viewDocument(documentId);
                    break;
                case 'analyze':
                    await this.analyzeDocument(documentId);
                    break;
                case 'delete':
                    await this.deleteDocument(documentId);
                    break;
            }
        });
    }

    async viewDocument(documentId) {
        try {
            const response = await API.getDocument(documentId);
            const doc = response.data.document;
            
            // Show document details in modal or new page
            this.showDocumentModal(doc);
        } catch (error) {
            Utils.showAlert(`Error viewing document: ${error.message}`, 'error');
        }
    }

    async analyzeDocument(documentId) {
        try {
            Utils.showAlert('Re-analyzing document...', 'info');
            const response = await API.analyzeDocument(documentId);
            
            Utils.showAlert('Document re-analyzed successfully!', 'success');
            await this.loadDocuments(); // Refresh the list
        } catch (error) {
            Utils.showAlert(`Error analyzing document: ${error.message}`, 'error');
        }
    }

    async deleteDocument(documentId) {
        if (!confirm('Are you sure you want to delete this document?')) {
            return;
        }

        try {
            await API.deleteDocument(documentId);
            Utils.showAlert('Document deleted successfully!', 'success');
            await this.loadDocuments(); // Refresh the list
        } catch (error) {
            Utils.showAlert(`Error deleting document: ${error.message}`, 'error');
        }
    }

    showDocumentModal(doc) {
        // Create modal for document details
        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal">
                <div class="modal-header">
                    <h2>${doc.file_info.filename}</h2>
                    <button class="modal-close">&times;</button>
                </div>
                <div class="modal-body">
                    ${this.renderDetailedCVData(doc.cv_data)}
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        // Add close functionality
        modal.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal-overlay') || 
                e.target.classList.contains('modal-close')) {
                document.body.removeChild(modal);
            }
        });
    }

    renderDetailedCVData(cvData) {
        if (!cvData || cvData.error) {
            return `<div class="alert alert-error">Error: ${cvData?.error || 'Failed to process CV'}</div>`;
        }

        return `
            <div class="cv-details">
                <h3>Personal Information</h3>
                <pre>${JSON.stringify(cvData.personal_info || {}, null, 2)}</pre>
                
                <h3>Work Experience</h3>
                <pre>${JSON.stringify(cvData.work_experience || [], null, 2)}</pre>
                
                <h3>Education</h3>
                <pre>${JSON.stringify(cvData.education || [], null, 2)}</pre>
                
                <h3>Skills</h3>
                <pre>${JSON.stringify(cvData.skills || [], null, 2)}</pre>
            </div>
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
    window.location.href = 'login.html';
}

// Global error handler
window.addEventListener('error', (e) => {
    console.error('Global error:', e.error);
    Utils.showAlert('An unexpected error occurred', 'error');
});

// Global unhandled promise rejection handler
window.addEventListener('unhandledrejection', (e) => {
    console.error('Unhandled promise rejection:', e.reason);
    Utils.showAlert('An unexpected error occurred', 'error');
});

// Expose globals
window.CVision = {
    Utils,
    API,
    FileUpload,
    DocumentManager,
    requireAuth,
    initUserInfo,
    logout
};