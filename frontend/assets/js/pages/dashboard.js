const API_BASE_URL = `${CONFIG.API_BASE_URL}`;


document.addEventListener('DOMContentLoaded', function () {

    if (!CVision.Utils.isAuthenticated()) {
        window.location.href = 'login.html';
        return;
    }

    initializeDashboard();
});

async function initializeDashboard() {
    CVision.initUserInfo();

    // Check if Gmail was just connected
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('gmail_connected') === 'true') {
        CVision.Utils.showAlert('Gmail connected successfully! Email agent is now active.', 'success');
        // Clean up URL
        window.history.replaceState({}, document.title, window.location.pathname);
    } else if (urlParams.get('error')) {
        const error = urlParams.get('error');
        CVision.Utils.showAlert(`Gmail connection failed: ${error}`, 'error');
        window.history.replaceState({}, document.title, window.location.pathname);
    }

    await loadUserProfile();
    await loadDocuments();
    await loadSavedJobs();
    setupFileUpload();
}

function setupFileUpload() {

    const fileInput = document.getElementById('fileInput');
    const dropZone = document.getElementById('dropZone');

    if (!fileInput) {
        return;
    }

    if (!dropZone) {
        return;
    }


    // Click handler for drop zone
    dropZone.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        fileInput.click();
    });

    // File input change handler
    fileInput.addEventListener('change', (e) => {
        handleFileUpload(e);
    });

    // Drag over handler
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropZone.classList.add('border-primary-500', 'bg-primary-50');
    });

    // Drag leave handler
    dropZone.addEventListener('dragleave', (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropZone.classList.remove('border-primary-500', 'bg-primary-50');
    });

    // Drop handler
    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropZone.classList.remove('border-primary-500', 'bg-primary-50');

        const files = e.dataTransfer.files;

        if (files.length > 0) {
            // Set the files to the input element
            fileInput.files = files;
            // Trigger the change event manually
            const event = new Event('change', { bubbles: true });
            fileInput.dispatchEvent(event);
        }
    });
}

async function handleFileUpload(event) {
    const file = event.target.files[0];

    if (!file) {
        return;
    }

    // Validate file type
    const allowedTypes = [
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/msword',
        'text/plain'
    ];

    if (!allowedTypes.includes(file.type)) {
        CVision.Utils.showAlert('Invalid file type. Please upload PDF, DOCX, DOC, or TXT files.', 'error');
        event.target.value = '';
        return;
    }

    // Validate file size (10MB max)
    const maxSize = 10 * 1024 * 1024;
    if (file.size > maxSize) {
        CVision.Utils.showAlert('File too large. Maximum size is 10MB.', 'error');
        event.target.value = '';
        return;
    }


    // Show upload progress
    const uploadLoading = document.getElementById('uploadLoading');
    uploadLoading.classList.remove('hidden');

    try {
        const formData = new FormData();
        formData.append('file', file);

        const uploadUrl = `${API_BASE_URL}/api/v1/documents/upload`;

        const response = await fetch(uploadUrl, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${CVision.Utils.getToken()}`
            },
            body: formData
        });

        if (!response.ok) {
            const errorData = await response.json();
            console.error('❌ Upload error:', errorData);
            throw new Error(errorData.detail || 'Upload failed');
        }

        const result = await response.json();

        CVision.Utils.showAlert('CV uploaded successfully! Processing...', 'success');

        // Reload documents
        setTimeout(async () => {
            await loadDocuments();
        }, 1000);

        // Clear the file input
        event.target.value = '';

    } catch (error) {
        CVision.Utils.showAlert(`Upload failed: ${error.message}`, 'error');
    } finally {
        uploadLoading.classList.add('hidden');
    }
}

async function loadUserProfile() {
    try {
        const response = await CVision.API.getProfile();
        if (response.success) {
            const user = response.data.user;

            const userTierEl = document.getElementById('userTier');
            if (userTierEl) {
                userTierEl.textContent = user.subscription_tier.charAt(0).toUpperCase() + user.subscription_tier.slice(1);
            }

            if (user.usage_stats) {
                document.getElementById('searchesUsed').textContent = user.usage_stats.monthly_searches || 0;
                document.getElementById('applicationsCount').textContent = user.usage_stats.total_applications || 0;
            }

            // Check Gmail connection status
            if (!user.gmail_connected) {
                showGmailConnectAlert();
            }
        }
    } catch (error) {
        console.error('Error loading user profile:');
    }
}


// async function loadUserProfile() {
//     try {
//         const response = await CVision.API.getProfile();
//         if (response.success) {
//             const user = response.data.user;
//             document.getElementById('userTier').textContent = 
//                 `${user.subscription_tier.charAt(0).toUpperCase() + user.subscription_tier.slice(1)}`;


//             if (user.usage_stats) {
//                 document.getElementById('searchesUsed').textContent = user.usage_stats.monthly_searches || 0;
//                 document.getElementById('applicationsCount').textContent = user.usage_stats.total_applications || 0;
//             }
//         }
//     } catch (error) {
//         console.error('Error loading user profile:', error);
//     }
// }

async function loadDocuments() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/documents/`, {
            headers: {
                'Authorization': `Bearer ${CVision.Utils.getToken()}`
            }
        });

        if (!response.ok) {
            throw new Error(`Failed to load documents`);
        }

        const data = await response.json();
        const documents = data.documents || data || [];

        displayDocuments(documents);
        document.getElementById('documentsCount').textContent = documents.length;
        document.getElementById('documentsCountText').textContent =
            `${documents.length} doc${documents.length !== 1 ? 's' : ''}`;

    } catch (error) {
        CVision.Utils.showAlert('Failed to load documents', 'error');
    }
}

function displayDocuments(documents) {
    const documentsList = document.getElementById('documentsList');

    if (documents.length === 0) {
        documentsList.innerHTML = `
                    <div class="text-center py-8 text-gray-500">
                        <svg class="w-10 h-10 sm:w-12 sm:h-12 mx-auto mb-3 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                        </svg>
                        <p class="text-sm sm:text-base">No documents yet</p>
                        <p class="text-xs sm:text-sm mt-1">Upload your CV to start</p>
                    </div>
                `;
        return;
    }

    documentsList.innerHTML = documents.map(doc => {
        const filename = doc.filename || (doc.file_info && doc.file_info.original_filename) || 'Unknown file';
        const fileSize = doc.file_size || (doc.file_info && doc.file_info.file_size) || 0;
        const uploadDate = doc.upload_date || doc.created_at || new Date().toISOString();
        const hasValidData = doc.cv_data && Object.keys(doc.cv_data).length > 0 && !doc.cv_data.error;

        return `
                    <div class="border border-gray-200 rounded-lg p-3 sm:p-4 hover:shadow-md transition-shadow min-w-0">
                        <div class="flex items-start justify-between gap-2 sm:gap-3">
                            <div class="flex-1 min-w-0 overflow-hidden">
                                <div class="flex items-center space-x-2 mb-2">
                                    <svg class="w-4 h-4 sm:w-5 sm:h-5 text-gray-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                                    </svg>
                                    <h3 class="text-sm sm:text-base font-medium text-gray-900 truncate" title="${filename}">${filename}</h3>
                                </div>
                                <div class="text-xs sm:text-sm text-gray-500 space-y-1 break-words">
                                    <p class="truncate">${CVision.Utils.formatFileSize(fileSize)} • ${CVision.Utils.formatDate(uploadDate)}</p>
                                    ${hasValidData ? `
                                        <p class="text-green-600 text-xs">✓ Processed</p>
                                    ` : `
                                        <p class="text-yellow-600 text-xs">⚠ Needs processing</p>
                                    `}
                                </div>
                            </div>
                            <div class="flex flex-col space-y-1.5 flex-shrink-0">
                                <button onclick="analyzeDocument('${doc.id || doc._id}')" 
                                    class="px-2 sm:px-3 py-1 text-xs font-medium text-blue-600 bg-blue-100 hover:bg-blue-200 rounded-md transition-colors whitespace-nowrap">
                                    ${hasValidData ? 'Re-analyze' : 'Analyze'}
                                </button>
                                <button onclick="deleteDocument('${doc.id || doc._id}')" 
                                    class="px-2 sm:px-3 py-1 text-xs font-medium text-red-600 bg-red-100 hover:bg-red-200 rounded-md transition-colors">
                                    Delete
                                </button>
                            </div>
                        </div>
                    </div>
                `;
    }).join('');
}

async function analyzeDocument(documentId) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/documents/${documentId}/reparse`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${CVision.Utils.getToken()}`
            }
        });

        if (!response.ok) throw new Error('Analysis failed');

        const result = await response.json();

        if (result.success) {
            CVision.Utils.showAlert('Document analyzed successfully!', 'success');
            await loadDocuments();
        } else {
            throw new Error(result.message || 'Analysis failed');
        }
    } catch (error) {
        console.error('Analyze error:', error);
        CVision.Utils.showAlert(`Failed to analyze: ${error.message}`, 'error');
    }
}

async function deleteDocument(documentId) {
    if (!confirm('Delete this document?')) return;

    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/documents/${documentId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${CVision.Utils.getToken()}`
            }
        });

        if (!response.ok) throw new Error('Delete failed');

        CVision.Utils.showAlert('Document deleted', 'success');
        await loadDocuments();

    } catch (error) {
        console.error('Delete error:', error);
        CVision.Utils.showAlert(`Failed to delete: ${error.message}`, 'error');
    }
}

function searchJobs() {
    window.location.href = 'pages/jobs.html';
}

function viewApplications() {
    window.location.href = 'pages/applications.html';
}

function upgradeAccount() {
    window.location.href = 'pages/subscription.html';
}

function viewProfile() {
    window.location.href = 'pages/profile.html';
}

function logout() {
    CVision.logout();
}

async function loadSavedJobs() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/jobs/saved/me?page=1&size=3`, {
            headers: {
                'Authorization': `Bearer ${CVision.Utils.getToken()}`
            }
        });

        if (!response.ok) throw new Error('Failed to load saved jobs');

        const data = await response.json();
        const jobs = data.jobs || data || [];
        displaySavedJobs(jobs);
    } catch (error) {
        console.error('Error loading saved jobs:', error);
    }
}

function displaySavedJobs(jobs) {
    const container = document.getElementById('savedJobsList');

    if (!jobs || jobs.length === 0) {
        container.innerHTML = `
                    <div class="text-center py-8 text-gray-500">
                        <svg class="w-10 h-10 sm:w-12 sm:h-12 mx-auto mb-3 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"></path>
                        </svg>
                        <p class="text-sm sm:text-base">No saved jobs</p>
                        <p class="text-xs sm:text-sm mt-1">Save jobs while searching to view them here</p>
                    </div>
                `;
        return;
    }

    container.innerHTML = jobs.map(job => `
                <div class="border border-gray-200 rounded-lg p-3 sm:p-4 hover:shadow-md transition-shadow">
                    <div class="flex items-start justify-between gap-2">
                        <div class="flex-1 min-w-0">
                            <h3 class="text-sm sm:text-base font-medium text-gray-900 truncate">${job.title}</h3>
                            <p class="text-xs sm:text-sm text-gray-600 mt-1">${job.company_name}</p>
                            <p class="text-xs text-gray-500 mt-1">${job.location}</p>
                            ${job.match_score ? `
                                <div class="mt-2 flex items-center gap-2">
                                    <span class="text-xs font-medium text-green-600">${Math.round(job.match_score * 100)}% Match</span>
                                </div>
                            ` : ''}
                        </div>
                        <div class="flex flex-col gap-1.5">
                            <button onclick="viewJobDetails('${job.id}')" 
                                class="px-2 sm:px-3 py-1 text-xs font-medium text-primary-600 bg-primary-100 hover:bg-primary-200 rounded-md transition-colors whitespace-nowrap">
                                View
                            </button>
                            <button onclick="unsaveJob('${job.id}')" 
                                class="px-2 sm:px-3 py-1 text-xs font-medium text-red-600 bg-red-100 hover:bg-red-200 rounded-md transition-colors">
                                Remove
                            </button>
                        </div>
                    </div>
                </div>
            `).join('');
}

function viewJobDetails(jobId) {
    window.location.href = `pages/jobs.html?job=${jobId}`;
}

async function unsaveJob(jobId) {
    if (!confirm('Remove this job from saved?')) return;

    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/jobs/save/${jobId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${CVision.Utils.getToken()}`
            }
        });

        if (!response.ok) throw new Error('Failed to unsave job');

        CVision.Utils.showAlert('Job removed from saved', 'success');
        await loadSavedJobs();
    } catch (error) {
        console.error('Error unsaving job:', error);
        CVision.Utils.showAlert('Failed to remove job', 'error');
    }
}

function showGmailConnectAlert() {
    const alertsContainer = document.getElementById('alerts');
    if (!alertsContainer) return;

    alertsContainer.innerHTML = `
        <div class="bg-blue-50 border-l-4 border-blue-500 p-4 mb-4 rounded-r shadow-sm">
            <div class="flex items-start justify-between">
                <div class="flex">
                    <div class="flex-shrink-0">
                        <svg class="h-5 w-5 text-blue-500" viewBox="0 0 20 20" fill="currentColor">
                            <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd" />
                        </svg>
                    </div>
                    <div class="ml-3">
                        <h3 class="text-sm font-medium text-blue-800">Connect your Gmail account</h3>
                        <div class="mt-2 text-sm text-blue-700">
                            <p>Enable the Email Agent to automatically track applications and apply via email.</p>
                        </div>
                        <div class="mt-4">
                            <button onclick="connectGmail()" class="text-sm font-medium text-blue-600 hover:text-blue-500 bg-white px-3 py-1.5 rounded border border-blue-200 shadow-sm transition-colors">
                                Connect Gmail
                            </button>
                        </div>
                    </div>
                </div>
                <button onclick="this.parentElement.parentElement.parentElement.remove()" class="text-blue-400 hover:text-blue-500">
                    <span class="sr-only">Dismiss</span>
                    <svg class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                        <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
                    </svg>
                </button>
            </div>
        </div>
    `;
}

async function connectGmail() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/auth/gmail/connect`, {
            headers: {
                'Authorization': `Bearer ${CVision.Utils.getToken()}`
            }
        });

        if (!response.ok) throw new Error('Failed to initiate connection');

        const data = await response.json();
        if (data.success && data.data.auth_url) {
            window.location.href = data.data.auth_url;
        }
    } catch (error) {
        console.error('Gmail connect error:', error);
        CVision.Utils.showAlert('Failed to connect Gmail', 'error');
    }
}
