/**
 * CvUploader Component
 * Reusable component for handling CV file uploads with drag & drop support.
 * 
 * Usage:
 * const uploader = new CvUploader({
 *     dropZoneId: 'dropZone',
 *     fileInputId: 'fileInput',
 *     onSuccess: (result) => console.log('Upload success', result),
 *     onError: (error) => console.error('Upload error', error)
 * });
 * uploader.init();
 */

class CvUploader {
    constructor(config) {
        this.config = Object.assign({
            dropZoneId: 'dropZone',
            fileInputId: 'fileInput',
            loadingId: 'uploadLoading',
            apiPath: '/api/v1/documents/upload',
            maxSize: 10 * 1024 * 1024, // 10MB
            allowedTypes: [
                'application/pdf',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'application/msword',
                'text/plain'
            ],
            onSuccess: null,
            onError: null
        }, config);

        this.dropZone = document.getElementById(this.config.dropZoneId);
        this.fileInput = document.getElementById(this.config.fileInputId);
        this.loadingEl = document.getElementById(this.config.loadingId);

        // Ensure API base URL is available
        this.apiBaseUrl = (window.CONFIG && window.CONFIG.API_BASE_URL) || '';
    }

    init() {
        if (!this.dropZone || !this.fileInput) {
            console.error('CvUploader: Drop zone or file input not found');
            return;
        }

        this.setupEventListeners();
        console.log('✅ CvUploader initialized');
    }

    setupEventListeners() {
        // Drop Zone Click -> File Input Click
        this.dropZone.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.fileInput.click();
        });

        // File Input Change
        this.fileInput.addEventListener('change', (e) => {
            this.handleFileSelect(e);
        });

        // Drag & Drop Visuals
        ['dragenter', 'dragover'].forEach(eventName => {
            this.dropZone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.dropZone.classList.add('border-primary-500', 'bg-primary-50');
            }, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            this.dropZone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.dropZone.classList.remove('border-primary-500', 'bg-primary-50');
            }, false);
        });

        // Drop Action
        this.dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.dropZone.classList.remove('border-primary-500', 'bg-primary-50');

            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.fileInput.files = files; // Sync input
                this.processFile(files[0]);
            }
        });
    }

    handleFileSelect(e) {
        const file = e.target.files[0];
        if (file) {
            this.processFile(file);
        }
    }

    async processFile(file) {
        // Validate
        const validation = this.validateFile(file);
        if (!validation.valid) {
            this.handleError(validation.error);
            this.resetInput();
            return;
        }

        // Upload
        await this.uploadFile(file);
    }

    validateFile(file) {
        if (!this.config.allowedTypes.includes(file.type)) {
            return {
                valid: false,
                error: 'Invalid file type. Please upload PDF, DOCX, DOC, or TXT files.'
            };
        }

        if (file.size > this.config.maxSize) {
            return {
                valid: false,
                error: `File too large. Maximum size is ${this.config.maxSize / (1024 * 1024)}MB.`
            };
        }

        return { valid: true };
    }

    async uploadFile(file) {
        this.showLoading(true);

        try {
            const formData = new FormData();
            formData.append('file', file);

            const token = window.CVision ? CVision.Utils.getToken() : localStorage.getItem('access_token');
            const uploadUrl = `${this.apiBaseUrl}${this.config.apiPath}`;

            const response = await fetch(uploadUrl, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                },
                body: formData
            });

            if (!response.ok) {
                let errorMessage = `Upload failed (${response.status})`;
                try {
                    const errorData = await response.json();
                    errorMessage = errorData.detail || errorData.message || errorMessage;
                } catch (e) {
                    // Response was not JSON (likely HTML 504/500)
                    console.warn('Backend returned non-JSON error:', response.status);
                    if (response.status === 504) errorMessage = 'Server timed out. Please try again.';
                    else if (response.status === 413) errorMessage = 'File is too large.';
                }
                throw new Error(errorMessage);
            }

            const result = await response.json();

            // Success Callback
            if (this.config.onSuccess) {
                this.config.onSuccess(result);
            }

            this.resetInput();

        } catch (error) {
            console.error('CvUploader Error:', error);
            this.handleError(error.message);
        } finally {
            this.showLoading(false);
        }
    }

    handleError(message) {
        if (this.config.onError) {
            this.config.onError(message);
        } else if (window.CVision && CVision.Utils.showAlert) {
            CVision.Utils.showAlert(message, 'error');
        } else {
            alert(message);
        }
    }

    showLoading(isLoading) {
        if (!this.loadingEl) return;

        if (isLoading) {
            this.loadingEl.classList.remove('hidden');
        } else {
            this.loadingEl.classList.add('hidden');
        }
    }

    resetInput() {
        if (this.fileInput) {
            this.fileInput.value = '';
        }
    }
}

// Export to global scope
window.CvUploader = CvUploader;
