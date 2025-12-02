const API_BASE_URL = `${CONFIG.API_BASE_URL}`;

let currentPage = 1;
let currentFilters = {};
let currentQuery = '';
let currentLocation = '';
let currentJobs = [];

// Phase 3: Batch selection state
let selectedJobs = new Set();
let batchModeActive = false;
let currentJobIdForCustomize = null;

document.addEventListener('DOMContentLoaded', async () => {
    if (!CVision.Utils.isAuthenticated()) {
        window.location.href = '../login.html';
        return;
    }

    initializeJobSearch();

    // Load existing jobs from database on page load
    await loadJobsFromDB();
});

function initializeJobSearch() {
    // Search form submission
    document.getElementById('jobSearchForm').addEventListener('submit', (e) => {
        e.preventDefault();
        performSearch();
    });

    // Apply filters
    document.getElementById('applyFilters').addEventListener('click', () => {
        applyFilters();
    });

    // Clear filters
    document.getElementById('clearFilters').addEventListener('click', () => {
        clearFilters();
    });

    // Sort change
    document.getElementById('sortBy').addEventListener('change', (e) => {
        performSearch(1, e.target.value);
    });

    // Modal controls
    document.getElementById('closeModal').addEventListener('click', closeJobModal);
    document.getElementById('jobModal').addEventListener('click', (e) => {
        if (e.target.id === 'jobModal') closeJobModal();
    });

    // Phase 3: Batch mode toggle
    const batchModeCheckbox = document.getElementById('batchSelectMode');
    if (batchModeCheckbox) {
        batchModeCheckbox.addEventListener('change', (e) => {
            toggleBatchMode(e.target.checked);
        });
    }
}

async function loadJobsFromDB() {
    try {
        showLoading();

        // FIXED: Properly structure the request body to match JobSearch model
        const response = await fetch(`${API_BASE_URL}/api/v1/jobs/search`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${CVision.Utils.getToken()}`
            },
            body: JSON.stringify({
                query: null,  // FIXED: Added required field
                location: null,  // FIXED: Added required field
                filters: null,  // FIXED: Added required field
                page: 1,
                size: 20,
                sort_by: 'created_at',
                sort_order: 'desc'
            })
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => null);
            console.error('Search error:', errorData);
            throw new Error(errorData?.detail || 'Failed to load jobs');
        }

        const data = await response.json();
        currentJobs = data.jobs || [];

        document.getElementById('loadingState').classList.add('hidden');

        if (currentJobs.length === 0) {
            // Show message encouraging user to add jobs
            document.getElementById('resultsCount').textContent = 'No jobs in database yet.';
            showEmptyStateWithSearchPrompt();
        } else {
            displayJobs(currentJobs);
            updateResultsCount(data.total || currentJobs.length, currentJobs.length);
            if (data.pages > 1) {
                updatePagination(data.page || 1, data.pages);
            }
        }
    } catch (error) {
        console.error('Error loading jobs:', error);
        document.getElementById('loadingState').classList.add('hidden');
        showEmptyStateWithSearchPrompt();
    }
}

/**
 * Show empty state with search prompt
 */
function showEmptyStateWithSearchPrompt() {
    const emptyState = document.getElementById('emptyState');
    emptyState.innerHTML = `
        <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
        <h3 class="mt-4 text-lg font-medium text-gray-900">Start Your Job Search</h3>
        <p class="mt-2 text-gray-500">Enter job title and location above to find opportunities</p>
        <p class="mt-1 text-sm text-gray-400">Your saved jobs will appear here</p>
    `;
    emptyState.classList.remove('hidden');
}

/**
 * ALTERNATIVE: If you want to show recent job searches instead of saved jobs,
 * you can use this endpoint (requires backend support):
 */
async function loadUserJobHistory() {
    try {
        showLoading();

        // This would load jobs from user's search history
        const response = await fetch(`${API_BASE_URL}/api/v1/jobs/history/me?page=1&size=20`, {
            headers: {
                'Authorization': `Bearer ${CVision.Utils.getToken()}`
            }
        });

        if (response.ok) {
            const data = await response.json();
            currentJobs = data.jobs || [];

            document.getElementById('loadingState').classList.add('hidden');

            if (currentJobs.length === 0) {
                showEmptyStateWithSearchPrompt();
            } else {
                displayJobs(currentJobs);
                updateResultsCount(data.total || currentJobs.length, currentJobs.length);
                if (data.pages > 1) {
                    updatePagination(data.page || 1, data.pages);
                }
            }
        } else {
            throw new Error('Failed to load job history');
        }
    } catch (error) {
        console.error('Error loading job history:', error);
        document.getElementById('loadingState').classList.add('hidden');
        showEmptyStateWithSearchPrompt();
    }
}

async function performSearch(page = 1, sortBy = 'relevance') {
    currentQuery = document.getElementById('searchQuery').value;
    currentLocation = document.getElementById('searchLocation').value;
    currentPage = page;

    if (!currentQuery && !currentLocation) {
        CVision.Utils.showAlert('Please enter a job title or location', 'warning');
        return;
    }

    // FIXED: Properly structure search data
    const searchData = {
        query: currentQuery || null,
        location: currentLocation || null,
        filters: buildFilters(),  // This returns a properly structured filters object
        page: currentPage,
        size: 20,
        sort_by: sortBy,
        sort_order: 'desc'
    };

    try {
        showLoading();

        const response = await fetch(`${API_BASE_URL}/api/v1/jobs/search`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${CVision.Utils.getToken()}`
            },
            body: JSON.stringify(searchData)
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => null);
            console.error('Search error:', errorData);
            throw new Error(errorData?.detail || 'Search failed');
        }

        const data = await response.json();
        currentJobs = data.jobs || [];

        if (currentJobs.length === 0) {
            showEmptyState();
        } else {
            displayJobs(currentJobs);
            updateResultsCount(data.total, currentJobs.length);
            updatePagination(data.page, data.pages);
        }
    } catch (error) {
        console.error('Search error:', error);
        CVision.Utils.showAlert('Failed to search jobs. Please try again.', 'error');
        showEmptyState();
    }
}

function buildFilters() {
    const employmentTypes = Array.from(
        document.querySelectorAll('.employment-type:checked')
    ).map(cb => cb.value);

    const workArrangements = Array.from(
        document.querySelectorAll('.work-arrangement:checked')
    ).map(cb => cb.value);

    const salaryMin = document.getElementById('salaryMin')?.value;
    const salaryMax = document.getElementById('salaryMax')?.value;

    // FIXED: Return null if no filters are applied, otherwise return filters object
    const hasFilters = employmentTypes.length > 0 ||
        workArrangements.length > 0 ||
        salaryMin ||
        salaryMax;

    if (!hasFilters) {
        currentFilters = null;
        return null;
    }

    const filters = {};

    if (employmentTypes.length > 0) {
        filters.employment_types = employmentTypes;
    }

    if (workArrangements.length > 0) {
        filters.work_arrangements = workArrangements;
    }

    if (salaryMin) filters.salary_min = parseFloat(salaryMin);
    if (salaryMax) filters.salary_max = parseFloat(salaryMax);

    currentFilters = filters;
    return filters;
}

function applyFilters() {
    if (currentQuery || currentLocation) {
        performSearch(1);
    } else {
        loadJobsFromDB();
    }
}

function clearFilters() {
    document.querySelectorAll('.employment-type, .work-arrangement').forEach(cb => {
        cb.checked = false;
    });
    const salaryMinEl = document.getElementById('salaryMin');
    const salaryMaxEl = document.getElementById('salaryMax');
    if (salaryMinEl) salaryMinEl.value = '';
    if (salaryMaxEl) salaryMaxEl.value = '';
    currentFilters = null;

    if (currentQuery || currentLocation) {
        performSearch(1);
    } else {
        loadJobsFromDB();
    }
}

function displayJobs(jobs) {
    const container = document.getElementById('jobsContainer');
    container.innerHTML = '';
    document.getElementById('emptyState').classList.add('hidden');
    document.getElementById('loadingState').classList.add('hidden');

    jobs.forEach(job => {
        const jobCard = createJobCard(job);
        container.appendChild(jobCard);
    });
}

function createJobCard(job) {
    const card = document.createElement('div');
    card.className = 'job-card bg-white rounded-xl shadow-sm border border-gray-100 hover:shadow-md transition p-6 relative';

    const matchScoreHTML = job.match_score
        ? `<div class="flex items-center gap-2 mb-2">
               <span class="text-sm font-medium text-green-600">${Math.round(job.match_score * 100)}% Match</span>
               <div class="h-2 flex-1 bg-gray-200 rounded-full max-w-[100px]">
                   <div class="h-2 bg-green-600 rounded-full" style="width: ${job.match_score * 100}%"></div>
               </div>
           </div>`
        : '';

    // Phase 3: Batch selection checkbox
    const batchCheckboxHTML = batchModeActive ? `
        <div class="absolute top-4 left-4">
            <input type="checkbox" 
                   class="job-select-checkbox w-5 h-5 rounded text-primary-600 border-gray-300 focus:ring-primary-500" 
                   onchange="toggleJobSelection('${job._id || job.id}', this)">
        </div>
    ` : '';

    card.innerHTML = `
        ${batchCheckboxHTML}
        <div class="${batchModeActive ? 'ml-8' : ''}">
            ${matchScoreHTML}
            <div class="flex justify-between items-start">
                <div class="flex-1 cursor-pointer" onclick="showJobDetails('${job._id || job.id}')">
                    <h3 class="text-lg font-semibold text-gray-900 hover:text-primary-600">
                        ${job.title}
                    </h3>
                    <p class="text-gray-600 mt-1">${job.company_name}</p>
                    <p class="text-gray-500 text-sm mt-1">${job.location}</p>
                </div>
                <button class="save-job-btn text-gray-400 hover:text-primary-600" onclick="event.stopPropagation(); saveJob('${job._id || job.id}')">
                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"/>
                    </svg>
                </button>
            </div>
            
            <div class="flex flex-wrap gap-2 mt-4">
                ${job.employment_type ? `<span class="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm">${formatEnumValue(job.employment_type)}</span>` : ''}
                ${job.work_arrangement ? `<span class="px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm">${formatEnumValue(job.work_arrangement)}</span>` : ''}
            </div>

            <p class="text-gray-600 mt-4 line-clamp-2">${job.description || 'No description available'}</p>

            ${job.skills_required && job.skills_required.length > 0 ? `
                <div class="mt-4 flex flex-wrap gap-2">
                    ${job.skills_required.slice(0, 5).map(skill =>
        `<span class="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs">${skill}</span>`
    ).join('')}
                    ${job.skills_required.length > 5 ? `
                        <span class="px-2 py-1 bg-gray-200 text-gray-600 rounded text-xs">+${job.skills_required.length - 5} more</span>
                    ` : ''}
                </div>
            ` : ''}

            <div class="mt-4 text-sm text-gray-500">
                Posted ${formatDate(job.posted_date || job.created_at)}
            </div>

            <!-- Phase 3 & 6: Action buttons -->
            <div class="flex gap-2 mt-4">
                <button onclick="event.stopPropagation(); saveJob('${job._id || job.id}')" 
                    class="flex-1 border border-gray-300 text-gray-700 rounded-lg px-3 py-2 text-sm font-medium hover:bg-gray-50 transition-colors">
                    Save
                </button>
                
                <button onclick="event.stopPropagation(); showCustomizeModal('${job._id || job.id}')" 
                    style="background: #667eea;" 
                    class="flex-1 text-white rounded-lg px-3 py-2 text-sm font-medium hover:opacity-90 transition-all flex items-center justify-center gap-1">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                    </svg>
                    Customize
                </button>
                
                <button onclick="event.stopPropagation(); applyToJob('${job._id || job.id}')" 
                    class="flex-1 btn-gradient text-white rounded-lg px-3 py-2 text-sm font-medium hover:shadow-lg transition-all flex items-center justify-center gap-1">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                              d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"/>
                    </svg>
                    Apply
                </button>
            </div>
        </div>
    `;

    return card;
}

function showJobDetails(jobId) {
    const job = currentJobs.find(j => (j._id || j.id) === jobId);
    if (!job) return;

    document.getElementById('modalTitle').textContent = job.title;
    document.getElementById('modalCompany').textContent = job.company_name;
    document.getElementById('modalLocation').textContent = job.location;

    const content = document.getElementById('modalContent');
    content.innerHTML = `
        ${job.match_score ? `
            <div class="bg-green-50 border border-green-200 rounded-lg p-4">
                <div class="flex items-center">
                    <svg class="w-5 h-5 text-green-600 mr-2" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"/>
                    </svg>
                    <span class="font-semibold text-green-900">
                        ${Math.round(job.match_score * 100)}% match with your profile
                    </span>
                </div>
            </div>
        ` : ''}

        <div class="flex gap-3 flex-wrap">
            ${job.employment_type ? `<span class="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm">${formatEnumValue(job.employment_type)}</span>` : ''}
            ${job.work_arrangement ? `<span class="px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm">${formatEnumValue(job.work_arrangement)}</span>` : ''}
        </div>

        <div class="mt-4">
            <h4 class="font-semibold mb-2">Job Description</h4>
            <p class="text-gray-700 whitespace-pre-line">${job.description || 'No description available'}</p>
        </div>

        ${job.requirements && job.requirements.length > 0 ? `
            <div class="mt-4">
                <h4 class="font-semibold mb-2">Requirements</h4>
                <ul class="list-disc list-inside space-y-1 text-gray-700">
                    ${job.requirements.map(req => `<li>${req}</li>`).join('')}
                </ul>
            </div>
        ` : ''}

        ${job.skills_required && job.skills_required.length > 0 ? `
            <div class="mt-4">
                <h4 class="font-semibold mb-2">Required Skills</h4>
                <div class="flex flex-wrap gap-2">
                    ${job.skills_required.map(skill =>
        `<span class="px-3 py-1 bg-gray-100 text-gray-700 rounded">${skill}</span>`
    ).join('')}
                </div>
            </div>
        ` : ''}

        ${job.salary_range ? `
            <div class="mt-4">
                <h4 class="font-semibold mb-2">Salary Range</h4>
                <p class="text-gray-700">${job.salary_range.min} - ${job.salary_range.max} ${job.salary_range.currency || 'USD'}</p>
            </div>
        ` : ''}

        ${job.external_url ? `
            <div class="mt-4">
                <h4 class="font-semibold mb-2">Application Link</h4>
                <a href="${job.external_url}" target="_blank" class="text-primary-600 hover:text-primary-700 underline">
                    Apply on company website
                </a>
            </div>
        ` : ''}
    `;

    document.getElementById('modalSaveJob').onclick = () => saveJob(jobId);

    // Phase 3: Update customize button
    const customizeBtn = document.getElementById('modalCustomize');
    if (customizeBtn) {
        customizeBtn.onclick = () => {
            closeJobModal();
            showCustomizeModal(jobId);
        };
    }

    // Phase 6: Update apply button with browser automation
    const applyBtn = document.getElementById('modalApply');
    if (applyBtn) {
        applyBtn.onclick = () => {
            closeJobModal();
            applyToJob(jobId);
        };
    }

    document.getElementById('jobModal').classList.remove('hidden');
    document.getElementById('jobModal').classList.add('flex');
}

function closeJobModal() {
    document.getElementById('jobModal').classList.add('hidden');
    document.getElementById('jobModal').classList.remove('flex');
}

async function saveJob(jobId) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/jobs/save/${jobId}`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${CVision.Utils.getToken()}`
            }
        });

        if (!response.ok) throw new Error('Failed to save job');

        CVision.Utils.showAlert('Job saved successfully!', 'success');

        const saveBtn = document.querySelector(`[onclick*="saveJob('${jobId}')"]`);
        if (saveBtn) {
            saveBtn.innerHTML = `
                <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"/>
                </svg>
            `;
            saveBtn.classList.add('text-primary-600');
        }
    } catch (error) {
        console.error('Error saving job:', error);
        CVision.Utils.showAlert('Failed to save job', 'error');
    }
}

function updateResultsCount(total, showing) {
    document.getElementById('resultsCount').textContent = `Showing ${showing} of ${total} jobs`;
}

function updatePagination(currentPage, totalPages) {
    const container = document.getElementById('pagination');

    if (totalPages <= 1) {
        container.classList.add('hidden');
        return;
    }

    container.classList.remove('hidden');
    container.innerHTML = '';

    if (currentPage > 1) {
        const prevBtn = createPageButton('Previous', currentPage - 1);
        container.appendChild(prevBtn);
    }

    const startPage = Math.max(1, currentPage - 2);
    const endPage = Math.min(totalPages, currentPage + 2);

    for (let i = startPage; i <= endPage; i++) {
        const pageBtn = createPageButton(i, i, i === currentPage);
        container.appendChild(pageBtn);
    }

    if (currentPage < totalPages) {
        const nextBtn = createPageButton('Next', currentPage + 1);
        container.appendChild(nextBtn);
    }
}

function createPageButton(text, page, isActive = false) {
    const btn = document.createElement('button');
    btn.textContent = text;
    btn.onclick = () => performSearch(page);
    btn.className = isActive
        ? 'px-4 py-2 bg-primary-600 text-white rounded-lg'
        : 'px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50';
    return btn;
}

function showLoading() {
    document.getElementById('loadingState').classList.remove('hidden');
    document.getElementById('jobsContainer').innerHTML = '';
    document.getElementById('emptyState').classList.add('hidden');
}

function showEmptyState() {
    document.getElementById('emptyState').classList.remove('hidden');
    document.getElementById('jobsContainer').innerHTML = '';
    document.getElementById('loadingState').classList.add('hidden');
}

function formatEnumValue(value) {
    return value.replace(/_/g, ' ')
        .split(' ')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
}

function formatDate(dateStr) {
    if (!dateStr) return 'recently';

    const date = new Date(dateStr);
    const now = new Date();
    const diffTime = Math.abs(now - date);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays === 0) return 'today';
    if (diffDays === 1) return 'yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;
    if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
    return `${Math.floor(diffDays / 30)} months ago`;
}

// Phase 3: Batch selection functions
function toggleBatchMode(enabled) {
    batchModeActive = enabled;

    if (!enabled) {
        clearBatchSelection();
    }

    // Re-render jobs to show/hide checkboxes
    displayJobs(currentJobs);
}

function toggleJobSelection(jobId, checkbox) {
    if (checkbox.checked) {
        selectedJobs.add(jobId);
    } else {
        selectedJobs.delete(jobId);
    }
    updateBatchSelectionBar();
}

function updateBatchSelectionBar() {
    const bar = document.getElementById('batchSelectionBar');
    const count = document.getElementById('selectedCount');

    if (bar && count) {
        count.textContent = selectedJobs.size;
        bar.style.display = selectedJobs.size > 0 ? 'block' : 'none';
    }
}

function clearBatchSelection() {
    selectedJobs.clear();
    updateBatchSelectionBar();
    document.querySelectorAll('.job-select-checkbox').forEach(cb => {
        cb.checked = false;
    });
}

async function batchCustomize() {
    if (selectedJobs.size === 0) {
        CVision.Utils.showAlert('No jobs selected', 'error');
        return;
    }

    if (selectedJobs.size > 10) {
        CVision.Utils.showAlert('Maximum 10 jobs allowed for batch generation', 'error');
        return;
    }

    // Get user's CVs
    const cvs = await loadUserCVsForBatch();
    if (!cvs || cvs.length === 0) {
        CVision.Utils.showAlert('Please upload a CV first', 'error');
        return;
    }

    // Use first CV for batch
    const cvId = cvs[0].id;

    try {
        if (typeof GenerationModule !== 'undefined') {
            await GenerationModule.batchCustomize(cvId, Array.from(selectedJobs));
            clearBatchSelection();
        } else {
            CVision.Utils.showAlert('Generation module not loaded', 'error');
        }
    } catch (error) {
        console.error('Batch customization failed:', error);
    }
}

async function loadUserCVsForBatch() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/documents/?document_type=cv`, {
            headers: {
                'Authorization': `Bearer ${CVision.Utils.getToken()}`
            }
        });

        if (!response.ok) throw new Error('Failed to load CVs');

        const data = await response.json();
        return data.documents || [];
    } catch (error) {
        console.error('Failed to load CVs:', error);
        return [];
    }
}

// ============================================================================
// Phase 6: Browser Automation Apply Functions
// ============================================================================

/**
 * Phase 6: Apply to job with browser automation
 * Opens modal for CV/cover letter selection, then starts browser autofill
 */
async function applyToJob(jobId) {
    try {
        const job = currentJobs.find(j => (j._id || j.id) === jobId);
        if (!job) {
            CVision.Utils.showAlert('Job not found', 'error');
            return;
        }

        // Check if job has application URL
        if (!job.external_url && !job.apply_url) {
            CVision.Utils.showAlert('This job does not have an application link', 'warning');
            return;
        }

        // Show modal to select CV and cover letter
        await showApplyModal(jobId);
        const cvResponse = await fetch(`${API_BASE_URL}/api/v1/documents/?document_type=cv`, {
            headers: {
                'Authorization': `Bearer ${CVision.Utils.getToken()}`
            }
        });

        if (cvResponse.ok) {
            const cvData = await cvResponse.json();
            const cvSelect = document.getElementById('applyModalCvSelect');

            if (cvData.documents && cvData.documents.length > 0) {
                cvSelect.innerHTML = cvData.documents.map(doc => `
                    <option value="${doc.id}">${doc.filename}</option>
                `).join('');
            } else {
                cvSelect.innerHTML = '<option value="">No CVs available - Upload one first</option>';
            }
        }

        // Load cover letters
        const clResponse = await fetch(`${API_BASE_URL}/api/v1/documents/?document_type=cover_letter`, {
            headers: {
                'Authorization': `Bearer ${CVision.Utils.getToken()}`
            }
        });

        if (clResponse.ok) {
            const clData = await clResponse.json();
            const clSelect = document.getElementById('applyModalCoverLetterSelect');

            if (clData.documents && clData.documents.length > 0) {
                clSelect.innerHTML = '<option value="">No cover letter</option>' +
                    clData.documents.map(doc => `
                        <option value="${doc.id}">${doc.filename}</option>
                    `).join('');
            }
        }

    } catch (error) {
        console.error('Failed to load documents:', error);
        CVision.Utils.showAlert('Failed to load documents', 'error');
    }
}

/**
 * Start Quick Apply (Email Agent)
 */
async function startQuickApply(jobId) {
    const cvId = document.getElementById('applyModalCvSelect')?.value;
    const coverLetterId = document.getElementById('applyModalCoverLetterSelect')?.value;

    if (!cvId) {
        CVision.Utils.showAlert('Please select a CV', 'warning');
        return;
    }

    // Show loading state in button
    const applyBtn = document.querySelector('#applyModal button.btn-gradient');
    const originalText = applyBtn.innerHTML;
    applyBtn.innerHTML = `
        <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        Sending Application...
    `;
    applyBtn.disabled = true;

    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/email-applications/apply`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${CVision.Utils.getToken()}`
            },
            body: JSON.stringify({
                job_id: jobId,
                cv_id: cvId,
                cover_letter: coverLetterId || null
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Failed to send application');
        }

        CVision.Utils.showAlert('Application sent successfully via email!', 'success');
        closeApplyModal();

        // Update UI to show applied status
        const applyBtnInCard = document.querySelector(`button[onclick*="applyToJob('${jobId}')"]`);
        if (applyBtnInCard) {
            applyBtnInCard.innerHTML = `
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                </svg>
                Applied
            `;
            applyBtnInCard.classList.remove('btn-gradient');
            applyBtnInCard.classList.add('bg-green-600', 'hover:bg-green-700');
            applyBtnInCard.disabled = true;
        }

    } catch (error) {
        console.error('Quick Apply failed:', error);
        CVision.Utils.showAlert(error.message || 'Failed to send application', 'error');

        // Reset button
        applyBtn.innerHTML = originalText;
        applyBtn.disabled = false;
    }
}

/**
 * Track application in database (Legacy - now handled by backend)
 */
async function trackApplication(jobId, cvId, coverLetterId) {
    // This is now handled automatically by the backend email-applications endpoint
    console.log('Application tracking handled by backend');
}

/**
 * Show apply modal for job application
 */
async function showApplyModal(jobId) {
    const job = currentJobs.find(j => (j._id || j.id) === jobId);
    if (!job) {
        CVision.Utils.showAlert('Job not found', 'error');
        return;
    }

    // Check if job has email application method
    const hasEmail = job.application_email ||
        job.employer_email ||
        (job.company_info && job.company_info.contact && job.company_info.contact.email);

    if (!hasEmail) {
        CVision.Utils.showAlert('This job does not support email applications', 'warning');
        return;
    }

    // Create modal HTML
    const modalHTML = `
        <div id="applyModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div class="bg-white rounded-xl shadow-2xl max-w-md w-full p-6">
                <div class="flex justify-between items-center mb-4">
                    <h3 class="text-xl font-bold text-gray-900">Quick Apply</h3>
                    <button onclick="closeApplyModal()" class="text-gray-400 hover:text-gray-600">
                        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                        </svg>
                    </button>
                </div>
                
                <div class="mb-4">
                    <p class="text-gray-600 mb-2">Applying to:</p>
                    <p class="font-semibold text-gray-900">${job.title}</p>
                    <p class="text-sm text-gray-500">${job.company_name}</p>
                </div>

                <div class="space-y-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Select CV *</label>
                        <select id="applyModalCvSelect" class="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-primary-500 focus:border-primary-500">
                            <option value="">Loading CVs...</option>
                        </select>
                    </div>

                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Select Cover Letter (Optional)</label>
                        <select id="applyModalCoverLetterSelect" class="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-primary-500 focus:border-primary-500">
                            <option value="">Loading cover letters...</option>
                        </select>
                    </div>
                </div>

                <div class="flex gap-3 mt-6">
                    <button onclick="closeApplyModal()" class="flex-1 border border-gray-300 text-gray-700 rounded-lg px-4 py-2 font-medium hover:bg-gray-50 transition-colors">
                        Cancel
                    </button>
                    <button onclick="openQuickApplyForm('${jobId}')" class="flex-1 btn-gradient text-white rounded-lg px-4 py-2 font-medium hover:shadow-lg transition-all">
                        Apply Now
                    </button>
                </div>
            </div>
        </div>
    `;

    // Remove existing modal if any
    const existingModal = document.getElementById('applyModal');
    if (existingModal) {
        existingModal.remove();
    }

    // Add modal to body
    document.body.insertAdjacentHTML('beforeend', modalHTML);
}

/**
 * Close apply modal
 */
function closeApplyModal() {
    const modal = document.getElementById('applyModal');
    if (modal) {
        modal.remove();
    }
}

// ============================================================================
// Phase 3: Customization Modal Functions
// ============================================================================

async function showCustomizeModal(jobId) {
    console.log('showCustomizeModal called with jobId:', jobId);

    currentJobIdForCustomize = jobId;

    const modal = document.getElementById('customizeModal');
    if (!modal) {
        console.error('Customize modal not found');
        return;
    }

    modal.classList.remove('hidden');
    modal.classList.add('flex');

    await loadUserCVs();
    await checkGenerationLimits();
    setupTemplateSelector();
}

function closeCustomizeModal() {
    const modal = document.getElementById('customizeModal');
    if (modal) {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
    }
    currentJobIdForCustomize = null;
}

async function loadUserCVs() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/documents/?document_type=cv`, {
            headers: {
                'Authorization': `Bearer ${CVision.Utils.getToken()}`
            }
        });

        if (!response.ok) throw new Error('Failed to load CVs');

        const data = await response.json();
        const cvs = data.documents || [];

        const select = document.getElementById('cvSelect');
        if (!select) return cvs;

        if (cvs.length > 0) {
            select.innerHTML = cvs.map(doc => `
                <option value="${doc.id}">
                    ${doc.filename} (${formatDate(doc.upload_date)})
                </option>
            `).join('');
        } else {
            select.innerHTML = '<option value="">No CVs found - Upload a CV first</option>';
        }

        return cvs;
    } catch (error) {
        console.error('Failed to load CVs:', error);
        return [];
    }
}

async function checkGenerationLimits() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/auth/me`, {
            headers: {
                'Authorization': `Bearer ${CVision.Utils.getToken()}`
            }
        });

        if (!response.ok) return;

        const user = await response.json();
        const tier = user.subscription_tier || 'free';

        const limits = {
            'free': 1,
            'basic': 150,
            'premium': 200
        };

        const used = user.usage_stats?.monthly_searches || 0;
        const remaining = Math.max(0, limits[tier] - used);

        const warningDiv = document.getElementById('usageWarning');
        if (warningDiv && remaining <= 5) {
            warningDiv.style.display = 'block';
            const remainingSpan = document.getElementById('remainingGenerations');
            if (remainingSpan) {
                remainingSpan.textContent = remaining;
            }
        }
    } catch (error) {
        console.error('Failed to check limits:', error);
    }
}

function setupTemplateSelector() {
    const options = document.querySelectorAll('.template-option');

    options.forEach(option => {
        option.addEventListener('click', function () {
            options.forEach(o => {
                o.classList.remove('active', 'border-primary-500');
                o.classList.add('border-gray-200');
            });
            this.classList.add('active', 'border-primary-500');
            this.classList.remove('border-gray-200');
        });
    });

    const coverLetterCheckbox = document.getElementById('includeCoverLetter');
    const coverLetterOptions = document.getElementById('coverLetterOptions');

    if (coverLetterCheckbox && coverLetterOptions) {
        coverLetterCheckbox.addEventListener('change', function () {
            coverLetterOptions.style.display = this.checked ? 'block' : 'none';
        });
    }
}

async function startCustomization() {
    console.log('startCustomization - currentJobIdForCustomize:', currentJobIdForCustomize);

    const cvSelect = document.getElementById('cvSelect');
    const cvId = cvSelect ? cvSelect.value : null;

    if (!cvId) {
        CVision.Utils.showAlert('Please select a CV', 'error');
        return;
    }

    if (!currentJobIdForCustomize) {
        CVision.Utils.showAlert('No job selected', 'error');
        console.error('currentJobIdForCustomize is null/undefined');
        return;
    }

    // Capture jobId locally before closing modal
    const jobId = currentJobIdForCustomize;

    const activeTemplate = document.querySelector('.template-option.active');
    const template = activeTemplate ? activeTemplate.dataset.template : 'professional';

    const includeCoverLetterCheckbox = document.getElementById('includeCoverLetter');
    const includeCoverLetter = includeCoverLetterCheckbox ? includeCoverLetterCheckbox.checked : true;

    const toneSelect = document.getElementById('toneSelect');
    const tone = toneSelect ? toneSelect.value : 'professional';

    // Close modal after capturing jobId
    closeCustomizeModal();

    try {
        if (typeof GenerationModule !== 'undefined' && GenerationModule.customizeForJob) {
            await GenerationModule.customizeForJob(cvId, jobId, {
                template,
                includeCoverLetter,
                tone
            });
        } else {
            CVision.Utils.showAlert('Generation module not loaded. Please refresh the page.', 'error');
        }
    } catch (error) {
        console.error('Customization failed:', error);
        CVision.Utils.showAlert('Customization failed: ' + error.message, 'error');
    }
}

// ============================================================================
// Make functions available globally for onclick handlers
// ============================================================================
window.showJobDetails = showJobDetails;
window.saveJob = saveJob;
window.applyToJob = applyToJob;
window.toggleJobSelection = toggleJobSelection;
window.clearBatchSelection = clearBatchSelection;
window.batchCustomize = batchCustomize;
window.toggleBatchMode = toggleBatchMode;
window.showCustomizeModal = showCustomizeModal;
window.closeCustomizeModal = closeCustomizeModal;
window.startCustomization = startCustomization;
window.showApplyModal = showApplyModal;
window.closeApplyModal = closeApplyModal;
// window.startBrowserAutofill = startBrowserAutofill; // Deprecated - using openQuickApplyForm instead


/**
 * Load CVs for apply modal
 */
async function loadCVsForApply() {
    try {
        const response = await CVision.API.request('/documents/?document_type=cv');
        const cvSelect = document.getElementById('applyModalCvSelect');

        if (!cvSelect) return;

        if (response.documents && response.documents.length > 0) {
            cvSelect.innerHTML = response.documents.map(doc =>
                `<option value="${doc.id}">${doc.filename}</option>`
            ).join('');
        } else {
            cvSelect.innerHTML = '<option value="">No CVs available - Upload one first</option>';
        }
    } catch (error) {
        console.error('Failed to load CVs:', error);
    }
}

/**
 * Load cover letters for apply modal
 */
async function loadCoverLettersForApply() {
    try {
        const response = await CVision.API.request('/documents/?document_type=cover_letter');
        const clSelect = document.getElementById('applyModalCoverLetterSelect');

        if (!clSelect) return;

        if (response.documents && response.documents.length > 0) {
            clSelect.innerHTML = '<option value="">No cover letter</option>' +
                response.documents.map(doc =>
                    `<option value="${doc.id}">${doc.filename}</option>`
                ).join('');
        }
    } catch (error) {
        console.error('Failed to load cover letters:', error);
    }
}

/**
 * Generate email preview
 */
function generateEmailPreview(job) {
    const emailTo = job.application_email || job.employer_email || 'Not available';
    const subject = `Application for ${job.title} Position`;
    const body = `Dear Hiring Manager,

I am writing to express my interest in the ${job.title} position at ${job.company_name}.

I have attached my CV for your review. I believe my skills and experience make me a strong candidate for this role.

Thank you for considering my application. I look forward to hearing from you.

Best regards`;

    const emailToEl = document.getElementById('emailTo');
    const emailSubjectEl = document.getElementById('emailSubject');
    const emailBodyEl = document.getElementById('emailBody');

    if (emailToEl) emailToEl.textContent = emailTo;
    if (emailSubjectEl) emailSubjectEl.textContent = subject;
    if (emailBodyEl) emailBodyEl.textContent = body;
}

/**
 * Send email application
 */
async function sendEmailApplication() {
    const cvId = document.getElementById('applyModalCvSelect')?.value;
    const coverLetterId = document.getElementById('applyModalCoverLetterSelect')?.value;

    if (!cvId) {
        CVision.Utils.showAlert('Please select a CV', 'warning');
        return;
    }

    const job = currentJobs.find(j => (j._id || j.id) === currentJobIdForApply);
    if (!job) {
        CVision.Utils.showAlert('Job not found', 'error');
        return;
    }

    const btn = document.getElementById('sendApplicationBtn');
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<span class="animate-spin mr-2">⏳</span> Sending...';
    }

    try {
        const response = await CVision.API.request('/applications/email-apply', {
            method: 'POST',
            body: JSON.stringify({
                job_id: job._id || job.id,
                cv_id: cvId,
                cover_letter_id: coverLetterId || null
            })
        });

        CVision.Utils.showAlert('Application sent successfully!', 'success');
        closeApplyModal();

        // Optionally redirect to applications page
        setTimeout(() => {
            window.location.href = '/pages/applications.html';
        }, 1500);

    } catch (error) {
        console.error('Failed to send application:', error);
        CVision.Utils.showAlert(error.message || 'Failed to send application', 'error');

        if (btn) {
            btn.disabled = false;
            btn.innerHTML = '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/></svg> Send Application';
        }
    }
}

/**
 * Connect Gmail account
 */
function connectGmail() {
    window.location.href = `${CONFIG.API_BASE_URL}${CONFIG.API_PREFIX}/auth/gmail/connect`;
}

// Store current job ID for apply
let currentJobIdForApply = null;
