const API_BASE_URL = `${CONFIG.API_BASE_URL}`;

document.addEventListener('DOMContentLoaded', function () {

    if (!CVision.Utils.isAuthenticated()) {
        window.location.href = 'login.html';
        return;
    }

    initializeDashboard();
});

// Automation State
let automationEnabled = false;

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

    // Initialize automation status
    await loadAutomationStatus();

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

            // Sync latest user data to local storage
            CVision.Utils.setUser(user);

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
            } else {
                showGmailConnectedAlert(user);
            }
        }
    } catch (error) {
        console.error('Error loading user profile:');
    }
}

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

function viewCVAnalysis() {
    window.location.href = 'pages/cv-analysis.html';
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

function showGmailConnectedAlert(user) {
    const alertsContainer = document.getElementById('alerts');
    if (!alertsContainer) return;

    const gmailEmail = user.email || 'your Gmail account';

    // Toggle button HTML (responsive with Tailwind)
    const toggleHTML = `
        <div class="flex items-center gap-3 p-3 sm:px-4 sm:py-2 bg-white rounded-lg border border-gray-200 cursor-pointer w-full sm:w-auto ml-0 sm:ml-auto hover:shadow-md transition-all shadow-sm" onclick="toggleAutomation()">
            <div class="flex-1 sm:flex-initial">
                <div class="font-bold text-sm text-gray-800">Automate Applications</div>
                <div class="text-xs text-gray-500" id="automationStatus">Click to enable</div>
                <div id="automationStatsText" class="text-xs text-green-500 font-medium h-3" style="display:none"></div>
            </div>
            <!-- Toggle Switch (Keep inline styles for JS compatibility with updateAutomationUI) -->
            <div id="automationToggle" style="position: relative; width: 40px; height: 22px; background: rgba(0,0,0,0.1); border-radius: 11px; transition: all 0.3s; flex-shrink: 0;">
                <div id="automationSlider" style="position: absolute; top: 2px; left: 2px; width: 18px; height: 18px; background: white; border-radius: 50%; transition: all 0.3s; box-shadow: 0 1px 3px rgba(0,0,0,0.2);"></div>
            </div>
        </div>
    `;

    alertsContainer.innerHTML = `
        <div class="bg-green-50 border-l-4 border-green-500 p-4 mb-4 rounded-r shadow-sm">
            <div class="flex flex-col sm:flex-row items-center gap-4">
                <div class="flex items-center w-full sm:flex-1">
                    <div class="flex-shrink-0">
                        <svg class="h-5 w-5 text-green-500" viewBox="0 0 20 20" fill="currentColor">
                            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
                        </svg>
                    </div>
                    <div class="ml-3">
                        <h3 class="text-sm font-medium text-green-800">Gmail Connected - Email Agent Active</h3>
                        <div class="text-sm text-green-700">
                            <p>Tracking: <strong>${gmailEmail}</strong></p>
                        </div>
                    </div>
                </div>
                ${toggleHTML}
            </div>
        </div>
    `;

    // Re-apply automation status visual state if it was loaded
    updateAutomationUI();
}

// ============================================================================
// Automation Logic (Ported from cv-analysis.js)
// ============================================================================

async function toggleAutomation() {
    // consistently check from storage instead of scraping DOM
    const user = CVision.Utils.getUser();
    const userTier = user?.subscription_tier?.toLowerCase() || 'free';

    const panel = document.getElementById('automationPanel');

    // Allow free users to open panel to see Test Run
    // if (userTier.includes('free') && !automationEnabled) { ... } -> Removed to allow access



    if (!automationEnabled) {
        // Opening settings to enable
        if (panel) panel.style.display = 'flex';
    } else {
        // Disabling - direct action
        // Use confirm dialog or just disable
        if (confirm('Disable auto-apply automation?')) {
            await disableAutomation();
        }
    }
}

function closeAutomationPanel() {
    const panel = document.getElementById('automationPanel');
    if (panel) panel.style.display = 'none';
}

function updateAutomationUI() {
    const toggle = document.getElementById('automationToggle');
    const slider = document.getElementById('automationSlider');
    const status = document.getElementById('automationStatus');
    const statsText = document.getElementById('automationStatsText');

    if (!toggle || !slider || !status) return;

    if (automationEnabled) {
        toggle.style.background = '#10b981';
        slider.style.left = '20px'; // Adjusted for 40px width
        status.textContent = 'Automated';
        if (statsText) statsText.style.display = 'block';
    } else {
        toggle.style.background = 'rgba(0,0,0,0.1)';
        slider.style.left = '2px';
        status.textContent = 'Click to enable';
        if (statsText) statsText.style.display = 'none';
    }
}

async function loadAutomationStatus() {
    try {
        const [statusResponse, statsResponse] = await Promise.all([
            fetch(`${API_BASE_URL}/api/v1/auto-apply/status`, {
                headers: { 'Authorization': `Bearer ${CVision.Utils.getToken()}` }
            }),
            fetch(`${API_BASE_URL}/api/v1/auto-apply/stats`, {
                headers: { 'Authorization': `Bearer ${CVision.Utils.getToken()}` }
            })
        ]);

        if (statusResponse.ok) {
            const data = await statusResponse.json();
            automationEnabled = data.enabled;

            // Update UI State
            updateAutomationUI();

            if (data) {
                const maxSlider = document.getElementById('maxAppsSlider');
                const minSlider = document.getElementById('minScoreSlider');
                // ... sliders logic
                if (maxSlider && data.max_daily_applications) {
                    maxSlider.value = data.max_daily_applications;
                    document.getElementById('maxAppsValue').textContent = data.max_daily_applications;
                }
                if (minSlider && data.min_match_score) {
                    minSlider.value = Math.round(data.min_match_score * 100);
                    document.getElementById('minScoreValue').textContent = Math.round(data.min_match_score * 100);
                }
            }
        }

        if (statsResponse.ok) {
            const stats = await statsResponse.json();
            const statsText = document.getElementById('automationStatsText');
            if (statsText && automationEnabled) {
                statsText.textContent = `Applied: ${stats.today_applications || 0} today`;
            }
        }

    } catch (error) {
        console.log('Could not load automation status:', error.message);
    }
}

async function saveAutomationSettings() {
    const maxApps = parseInt(document.getElementById('maxAppsSlider').value);
    const minScore = parseInt(document.getElementById('minScoreSlider').value) / 100;

    // Check tier for Save
    const user = CVision.Utils.getUser();
    const userTier = user?.subscription_tier?.toLowerCase() || 'free';

    // Free users cannot save settings
    if (userTier === 'free' || userTier === 'freemium') {
        showPremiumModal(
            'Premium Feature',
            'Saving automation settings is available for Basic and Premium users. Upgrade to unlock full automation control.'
        );
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/auto-apply/enable`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${CVision.Utils.getToken()}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                max_daily_applications: maxApps,
                min_match_score: minScore
            })
        });

        if (response.ok) {
            CVision.Utils.showAlert('Automation Enabled! System is now working.', 'success');
            automationEnabled = true;
            closeAutomationPanel(); // Close panel on success
            updateAutomationUI();

            // Refresh stats immediately
            loadAutomationStatus();

            // Scroll to top to see alert
            window.scrollTo({ top: 0, behavior: 'smooth' });
        } else {
            const error = await response.json();
            CVision.Utils.showAlert('Error: ' + (error.detail || 'Failed to enable'), 'error');
        }
    } catch (error) {
        console.error('Error saving settings:', error);
        CVision.Utils.showAlert('Error saving settings', 'error');
    }
}

async function runTestAutomation() {
    const btn = document.getElementById('testRunBtn');
    if (!btn) return;

    // Check tier and limits
    const user = CVision.Utils.getUser();
    const userTier = user?.subscription_tier?.toLowerCase() || 'free';

    if (userTier === 'free' || userTier === 'freemium') {
        const hasRunTest = localStorage.getItem(`has_run_test_${user.id || 'anon'}`);
        if (hasRunTest) {
            showPremiumModal(
                'Test Run Limit Reached',
                'You have used your 1 free test run. Upgrade to Premium for unlimited test runs and full automation capabilities.'
            );
            return;
        }
        // Mark as run (optimistic)
        localStorage.setItem(`has_run_test_${user.id || 'anon'}`, 'true');
    }

    // UI Elements
    const progressBar = document.getElementById('testProgressBar');
    const progressFill = document.getElementById('testProgressFill');
    const progressStatus = document.getElementById('testProgressStatus');
    const progressPercent = document.getElementById('testProgressPercent');

    // Save original state
    const originalText = btn.innerHTML;
    btn.innerHTML = `
        <svg class="animate-spin h-4 w-4 text-gray-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        <span>Starting...</span>
    `;
    btn.disabled = true;

    if (progressBar) {
        progressBar.classList.remove('hidden');
        progressFill.style.width = '0%';
        progressStatus.textContent = 'Initializing...';
        progressPercent.textContent = '0%';
    }

    // Clear previous results
    const resultContainer = document.getElementById('testRunResult');
    if (resultContainer) {
        resultContainer.classList.add('hidden');
        resultContainer.innerHTML = '';
        resultContainer.className = "hidden mt-3 text-sm p-3 rounded-md border text-center";
    }

    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/auto-apply/test`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${CVision.Utils.getToken()}`
            }
        });

        if (!response.ok) throw new Error('Test failed to start');

        const data = await response.json();
        const taskId = data.task_id;

        // Poll for status
        const pollInterval = setInterval(async () => {
            try {
                const statusRes = await fetch(`${API_BASE_URL}/api/v1/auto-apply/test/status/${taskId}`, {
                    headers: { 'Authorization': `Bearer ${CVision.Utils.getToken()}` }
                });

                if (statusRes.ok) {
                    const statusData = await statusRes.json();

                    // Update Progress UI
                    if (progressBar) {
                        const pct = Math.round((statusData.current / statusData.total) * 100);
                        progressFill.style.width = `${pct}%`;
                        progressStatus.textContent = statusData.status || 'Processing...';
                        progressPercent.textContent = `${pct}%`;
                    }

                    if (statusData.state === 'SUCCESS' || statusData.state === 'FAILURE') {
                        clearInterval(pollInterval);

                        // Final result handling
                        if (statusData.state === 'SUCCESS') {
                            // Show specific result message with stats
                            const appsSent = statusData.applications_sent || 0;
                            const msg = statusData.message || "Test run completed";
                            const stats = statusData.stats || {};

                            let detail = "";
                            if (stats.jobs_found !== undefined) {
                                detail = `Scanned: ${stats.jobs_found} | Analyzed: ${stats.jobs_analyzed} | Matched: ${stats.matches_found}`;
                            }

                            const resultContainer = document.getElementById('testRunResult');
                            if (resultContainer) {
                                resultContainer.classList.remove('hidden');
                                if (appsSent > 0) {
                                    resultContainer.className = "mt-3 text-sm p-3 rounded-md border text-center bg-green-50 border-green-200 text-green-700";
                                    resultContainer.innerHTML = `<strong>Success! ${appsSent} applications sent.</strong><br><span class="text-xs mt-1 block">${detail}</span>`;
                                } else {
                                    resultContainer.className = "mt-3 text-sm p-3 rounded-md border text-center bg-blue-50 border-blue-200 text-blue-700";
                                    resultContainer.innerHTML = `<strong>${msg}</strong><br><span class="text-xs mt-1 block">${detail}</span>`;
                                }
                            }

                            CVision.Utils.showAlert('success', 'Test Run Finished');

                            await loadAutomationStatus(); // Refresh stats
                        } else {
                            const resultContainer = document.getElementById('testRunResult');
                            if (resultContainer) {
                                resultContainer.classList.remove('hidden');
                                resultContainer.className = "mt-3 text-sm p-3 rounded-md border text-center bg-red-50 border-red-200 text-red-700";
                                resultContainer.innerText = `Test Failed: ${statusData.error}`;
                            }
                            CVision.Utils.showAlert(`Test Failed`, 'error');
                        }

                        // Reset UI after delay
                        setTimeout(() => {
                            btn.innerHTML = originalText;
                            btn.disabled = false;
                            if (progressBar) progressBar.classList.add('hidden');
                        }, 5000); // Keep result visible longer
                    }
                }
            } catch (err) {
                console.error('Polling error', err);
                // Don't clear interval immediately on one network glip, but maybe safe to stop if repeated
            }
        }, 1500); // Check every 1.5s

    } catch (error) {
        console.error('Test run error:', error);
        CVision.Utils.showAlert('Test run failed to start', 'error');
        btn.innerHTML = originalText;
        btn.disabled = false;
        if (progressBar) progressBar.classList.add('hidden');
    }
}

async function disableAutomation() {
    try {
        await fetch(`${API_BASE_URL}/api/v1/auto-apply/disable`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${CVision.Utils.getToken()}` }
        });

        automationEnabled = false;
        updateAutomationUI();
        CVision.Utils.showAlert('Automation disabled', 'info');
    } catch (error) {
        console.error('Error disabling automation:', error);
    }
}

function updateSliderValue(type, value) {
    if (type === 'maxApps') {
        const el = document.getElementById('maxAppsValue');
        if (el) el.textContent = value;
    } else if (type === 'minScore') {
        const el = document.getElementById('minScoreValue');
        if (el) el.textContent = value;
    }
}

// Premium Modal Functions
function showPremiumModal(title, message) {
    const modal = document.getElementById('premiumModal');
    if (modal) {
        // Update content if provided
        if (title) {
            const titleEl = document.getElementById('premiumModalTitle');
            if (titleEl) titleEl.textContent = title;
        }

        if (message) {
            const msgEl = document.getElementById('premiumModalDescription');
            if (msgEl) msgEl.textContent = message;
        }

        modal.style.display = 'flex';
        modal.style.pointerEvents = 'auto';
    }
}

function closePremiumModal() {
    const modal = document.getElementById('premiumModal');
    if (modal) {
        modal.style.display = 'none';
        modal.style.pointerEvents = 'none';
    }
}

function upgradeNow() {
    window.location.href = 'pages/subscription.html';
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
