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

    // Fetch applied jobs to update UI state
    try {
        const appRes = await fetch(`${API_BASE_URL}/api/v1/applications/?page=1&size=100`, {
            headers: { 'Authorization': `Bearer ${CVision.Utils.getToken()}` }
        });
        if (appRes.ok) {
            const appData = await appRes.json();
            if (window.JobActions) {
                window.JobActions.setAppliedJobs(appData.applications || []);
                // Re-render job list to reflect status
                displayJobs(currentJobs);
            }
        }
    } catch (e) {
        console.error('Failed to load application status', e);
    }

    // Check for job ID in URL after jobs are loaded
    const urlParams = new URLSearchParams(window.location.search);
    const jobIdParam = urlParams.get('job');
    if (jobIdParam) {
        // Wait a bit to ensure DOM updates
        setTimeout(() => {
            // If job not in current list (search results usually 20), we might need to fetch it individually
            // For now try to show from list, or fetch if missing
            const jobInList = currentJobs.find(j => (j._id || j.id) === jobIdParam);
            if (jobInList) {
                showJobDetails(jobIdParam);
            } else {
                // Fetch individual job if not in current list
                fetchJobAndShow(jobIdParam);
            }
        }, 500);
    }
    // Event listener for job updates from JobActions
    document.addEventListener('job:updated', (e) => {
        const { jobId, result } = e.detail;
        updateJobInList(jobId, {
            generated_cv_path: result.cv_pdf_url,
            generated_cover_letter_path: result.cover_letter_pdf_url
        });
    });

    // Listen for new applications to update buttons
    document.addEventListener('job:applied', () => {
        // Re-render current list to show "Applied" button
        if (currentJobs) displayJobs(currentJobs);
    });

});

async function fetchJobAndShow(jobId) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/jobs/${jobId}`, {
            headers: { 'Authorization': `Bearer ${CVision.Utils.getToken()}` }
        });
        if (response.ok) {
            const job = await response.json();

            // Check if job already exists in list
            const existingIndex = currentJobs.findIndex(j => (j._id || j.id) === (job._id || job.id));
            if (existingIndex !== -1) {
                currentJobs[existingIndex] = job;
            } else {
                currentJobs.push(job);
            }

            showJobDetails(jobId);
        }
    } catch (e) {
        console.error('Failed to load deep-linked job', e);
    }
}

function updateJobInList(jobId, updates) {
    const validJobId = String(jobId);
    if (!currentJobs) return;

    // Update in current list
    const jobIndex = currentJobs.findIndex(j => String(j._id || j.id) === validJobId);
    if (jobIndex !== -1) {
        // Merge updates
        currentJobs[jobIndex] = { ...currentJobs[jobIndex], ...updates };

        // Refresh display of this card if visible (or just all for simplicity)
        displayJobs(currentJobs);
        console.log(`Updated job ${validJobId} in list with`, updates);
    } else {
        console.warn(`Job ${validJobId} not found in current list to update`);
    }
}

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
        window.currentJobs = currentJobs; // Expose globally for JobApply.js

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

            // Fetch saved jobs to check for generated documents
            try {
                const savedResponse = await fetch(`${API_BASE_URL}/api/v1/jobs/saved/me?size=100`, {
                    headers: { 'Authorization': `Bearer ${CVision.Utils.getToken()}` }
                });
                if (savedResponse.ok) {
                    const savedData = await savedResponse.json();
                    const savedJobs = savedData.jobs || [];

                    let needsUpdate = false;
                    savedJobs.forEach(savedJob => {
                        const jobIndex = currentJobs.findIndex(j => (j._id || j.id) === (savedJob._id || savedJob.id));
                        if (jobIndex !== -1) {
                            // Mark as saved for UI
                            currentJobs[jobIndex].is_saved = true;
                            needsUpdate = true;

                            // Merge generated paths if they exist
                            if (savedJob.generated_cv_path) {
                                currentJobs[jobIndex].generated_cv_path = savedJob.generated_cv_path;
                            }
                            if (savedJob.generated_cover_letter_path) {
                                currentJobs[jobIndex].generated_cover_letter_path = savedJob.generated_cover_letter_path;
                            }
                            if (savedJob.generated_cv_id) {
                                currentJobs[jobIndex].generated_cv_id = savedJob.generated_cv_id;
                            }
                            if (savedJob.generated_cover_letter_id) {
                                currentJobs[jobIndex].generated_cover_letter_id = savedJob.generated_cover_letter_id;
                            }
                        }
                    });

                    if (needsUpdate) {
                        displayJobs(currentJobs);
                    }
                }
            } catch (e) {
                console.warn('Failed to sync saved job status:', e);
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


function decodeHtmlEntities(text) {
    if (!text) return '';
    const textArea = document.createElement('textarea');
    textArea.innerHTML = text;
    return textArea.value;
}

function createJobCard(job) {
    const card = document.createElement('div');
    card.className = 'job-card bg-white rounded-xl shadow-sm border border-gray-100 hover:shadow-lg transition-all duration-300 relative overflow-hidden group flex flex-col h-full';

    // Match Score Gradient Border (Optional)
    const matchBorder = job.match_score
        ? `<div class="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-green-400 to-primary-500 transform scale-x-0 group-hover:scale-x-100 transition-transform duration-300 origin-left"></div>`
        : '';

    // Batch Selection Checkbox
    const batchCheckboxHTML = batchModeActive ? `
        <div class="absolute top-4 left-4 z-10">
            <input type="checkbox" 
                   class="job-select-checkbox w-5 h-5 rounded text-primary-600 border-gray-300 focus:ring-primary-500" 
                   onchange="toggleJobSelection('${job._id || job.id}', this)">
        </div>
    ` : '';

    // Header Section
    const matchBadge = job.match_score
        ? `<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
             <svg class="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"/></svg>
             ${Math.round(job.match_score * 100)}% Match
           </span>`
        : '';

    card.innerHTML = `
        ${matchBorder}
        ${batchCheckboxHTML}
        
        <div class="p-6 flex-1 flex flex-col cursor-pointer" onclick="showJobDetails('${job._id || job.id}')">
            <!-- Header: Title & Company -->
            <div class="flex justify-between items-start mb-4 ${batchModeActive ? 'ml-8' : ''}">
                <div class="flex-1 min-w-0 pr-4">
                    <div class="flex items-center gap-2 mb-1">
                        ${matchBadge}
                        <span class="text-xs text-gray-500 flex items-center">
                            <svg class="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                            ${formatDate(job.posted_date || job.created_at)}
                        </span>
                    </div>
                    <h3 class="text-xl font-bold text-gray-900 leading-tight group-hover:text-primary-600 transition-colors line-clamp-2" title="${decodeHtmlEntities(job.title)}">
                        ${decodeHtmlEntities(job.title)}
                    </h3>
                    <p class="text-base text-gray-600 font-medium mt-1 truncate">${decodeHtmlEntities(job.company_name)}</p>
                </div>
                <button class="save-job-btn p-2 rounded-full hover:bg-gray-100 ${job.is_saved ? 'text-primary-600' : 'text-gray-400'} hover:text-primary-600 transition-colors flex-shrink-0" 
                        onclick="event.stopPropagation(); saveJob('${job._id || job.id}')" title="${job.is_saved ? 'Saved' : 'Save Job'}">
                    ${job.is_saved ? `
                    <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"/>
                    </svg>
                    ` : `
                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"/>
                    </svg>
                    `}
                </button>
            </div>

            <!-- Metadata Row -->
            <div class="flex flex-wrap items-center gap-y-2 gap-x-4 text-sm text-gray-500 mb-4 ${batchModeActive ? 'ml-8' : ''}">
                <div class="flex items-center">
                    <svg class="w-4 h-4 mr-1.5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"/></svg>
                    ${decodeHtmlEntities(job.location)}
                </div>
                ${job.salary_range ? `
                    <div class="flex items-center">
                        <svg class="w-4 h-4 mr-1.5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                        ${job.salary_range.min ? `${job.salary_range.min} - ` : ''}${job.salary_range.max} ${job.salary_range.currency || ''}
                    </div>
                ` : ''}
            </div>

            <!-- Tags -->
            <div class="flex flex-wrap gap-2 mb-4 ${batchModeActive ? 'ml-8' : ''}">
                ${job.employment_type ? `<span class="px-2.5 py-0.5 bg-blue-50 text-blue-700 rounded-md text-xs font-medium border border-blue-100">${formatEnumValue(job.employment_type)}</span>` : ''}
                ${job.work_arrangement ? `<span class="px-2.5 py-0.5 bg-purple-50 text-purple-700 rounded-md text-xs font-medium border border-purple-100">${formatEnumValue(job.work_arrangement)}</span>` : ''}
            </div>

            <!-- Description -->
            <p class="text-gray-600 text-sm line-clamp-3 mb-4 leading-relaxed ${batchModeActive ? 'ml-8' : ''}">
                ${job.description ? decodeHtmlEntities(job.description).replace(/<[^>]*>?/gm, '') : 'No description available'}
            </p>

            <!-- Skills (Bottom of content) -->
            ${job.skills_required && job.skills_required.length > 0 ? `
                <div class="mt-auto pt-4 border-t border-gray-50 ${batchModeActive ? 'ml-8' : ''}">
                    <div class="flex flex-wrap gap-2">
                        ${job.skills_required.slice(0, 3).map(skill =>
        `<span class="px-2 py-1 bg-gray-100 text-gray-600 rounded text-xs font-medium">${decodeHtmlEntities(skill)}</span>`
    ).join('')}
                        ${job.skills_required.length > 3 ? `
                            <span class="px-2 py-1 text-gray-400 text-xs">+${job.skills_required.length - 3}</span>
                        ` : ''}
                    </div>
                </div>
            ` : ''}
        </div>

        <!-- Footer Actions -->
             <div class="mt-4">
                 ${window.JobActions ? window.JobActions.getButtonsHTML(job) : ''}
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


        <div class="mt-6 pt-6 border-t border-gray-100">
            <h4 class="font-semibold text-lg mb-3">Generated Documents</h4>
            ${window.JobActions ? window.JobActions.getButtonsHTML(job, false) : ''}
        </div>


        ${job.external_url ? `
            <div class="mt-4">
                <h4 class="font-semibold mb-2">Application Link</h4>
                <a href="${job.external_url}" target="_blank" class="text-primary-600 hover:text-primary-700 underline">
                    Apply on company website
                </a>
            </div>
        ` : ''
        }
`;

    // Wire up Save Job button
    const saveBtn = document.getElementById('modalSaveJob');
    if (saveBtn) {
        saveBtn.onclick = () => saveJob(jobId);
        saveBtn.dataset.jobId = jobId;

        if (job.is_saved) {
            saveBtn.innerHTML = `
                <svg class="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
                </svg>
                Saved
            `;
            saveBtn.classList.remove('text-gray-700');
            saveBtn.classList.add('text-primary-600');
        } else {
            saveBtn.innerHTML = 'Save Job';
            saveBtn.classList.remove('text-primary-600');
            saveBtn.classList.add('text-gray-700');
        }
    }

    // Check for applied status
    const isApplied = window.JobActions && window.JobActions.appliedJobIds.has(String(jobId));

    // Wire up Customize button
    const customizeBtn = document.getElementById('modalCustomize');
    if (customizeBtn) {
        if (isApplied) {
            customizeBtn.style.display = 'none';
        } else {
            customizeBtn.style.display = 'flex';
            customizeBtn.onclick = () => window.JobActions.openCustomizeModal(jobId);
        }
    }

    // Wire up Apply button
    const applyBtn = document.getElementById('modalApply');
    if (applyBtn) {
        if (isApplied) {
            applyBtn.disabled = true;
            applyBtn.innerHTML = `
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>
                Applied
            `;
            // Remove gradient classes and add applied styles
            applyBtn.className = 'flex-1 bg-green-50 text-green-700 border border-green-200 rounded-lg px-4 py-2.5 text-sm font-semibold opacity-80 cursor-not-allowed flex items-center justify-center gap-2';
            applyBtn.onclick = null;
        } else {
            applyBtn.disabled = false;
            applyBtn.innerHTML = `
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
                Apply Now
            `;
            // Restore gradient classes
            applyBtn.className = 'flex-1 btn-gradient text-white rounded-lg px-4 py-2.5 text-sm font-semibold hover:shadow-lg transition-all shadow-md flex items-center justify-center gap-2';
            applyBtn.onclick = () => window.JobApply.openApplyModal(jobId, job);
        }
    }



    document.getElementById('jobModal').classList.remove('hidden');
    document.getElementById('jobModal').classList.add('flex');
}

function closeJobModal() {
    document.getElementById('jobModal').classList.add('hidden');
    document.getElementById('jobModal').classList.remove('flex');
}

async function saveJob(jobId, silent = false, extraData = null) {
    try {
        const options = {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${CVision.Utils.getToken()}`
            }
        };

        if (extraData) {
            options.headers['Content-Type'] = 'application/json';
            options.body = JSON.stringify(extraData);
        }

        const response = await fetch(`${API_BASE_URL}/api/v1/jobs/save/${jobId}`, options);

        if (!response.ok) throw new Error('Failed to save job');

        if (!silent) {
            CVision.Utils.showAlert('Job saved successfully!', 'success');
        }

        // Update list button(s)
        const listSaveBtns = document.querySelectorAll(`[onclick *= "saveJob('${jobId}')"]`);
        listSaveBtns.forEach(btn => {
            btn.innerHTML = `
    <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
        <path d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
    </svg>
    `;
            btn.classList.add('text-primary-600');
        });

        // Update modal button if it matches the current job
        const modalSaveBtn = document.getElementById('modalSaveJob');
        if (modalSaveBtn && modalSaveBtn.dataset.jobId === jobId) {
            modalSaveBtn.innerHTML = `
    <svg class="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 24 24">
        <path d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
    </svg>
    Saved
        `;
            modalSaveBtn.classList.remove('text-gray-700');
            modalSaveBtn.classList.add('text-primary-600');
        }
    } catch (error) {
        console.error('Error saving job:', error);
        if (!silent) {
            CVision.Utils.showAlert('Failed to save job', 'error');
        }
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
        const response = await fetch(`${API_BASE_URL} /api/v1 / documents /? document_type = cv`, {
            headers: {
                'Authorization': `Bearer ${CVision.Utils.getToken()} `
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

// ============================================================================
// Application Limits Logic
// ============================================================================

async function checkApplicationLimit() {
    const user = CVision.Utils.getUser();
    const userTier = user?.subscription_tier?.toLowerCase() || 'free';

    // Limits definition
    const LIMITS = {
        'free': 5,
        'basic': 30,
        'premium': Infinity
    };

    const limit = LIMITS[userTier] || 5;

    // Skip check for premium
    if (limit === Infinity) return true;

    try {
        // Fetch stats from backend
        const response = await fetch(`${API_BASE_URL} /api/v1 / applications / stats / overview`, {
            headers: {
                'Authorization': `Bearer ${CVision.Utils.getToken()} `
            }
        });

        if (!response.ok) throw new Error('Failed to fetch application stats');

        const stats = await response.json();
        const count = stats.applications_today || 0;

        // Debug logging
        console.log('[DEBUG-LIMITS-BACKEND]', {
            tier: userTier,
            limit: limit,
            currentCount: count,
            userId: user?.id,
            isLimitReached: count >= limit
        });

        if (count >= limit) {
            if (typeof UpgradeModal !== 'undefined') {
                UpgradeModal.show(
                    'Daily Application Limit Reached',
                    `You have reached your daily limit of ${limit} applications.Upgrade your plan to apply to more jobs today.`
                );
            } else {
                alert(`Daily Limit Reached: You have used your ${limit} free applications.`);
            }
            return false;
        }

        return true;
    } catch (error) {
        console.error('Error checking limits:', error);
        console.warn('Falling back to simple allow on error');
        return true;
    }
}

// Legacy increment removed as backend handles it automatically
function incrementApplicationCount() {
    // No-op for backward compatibility if called
}

/**
 * Phase 6: Apply to job with browser automation
 * Opens modal for CV/cover letter selection, then starts browser autofill
 */
// Quick Apply logic moved to quick-apply.js component

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
/**
 * Show apply modal for job application
 */
async function showApplyModal(jobId) {
    if (window.JobApply) {
        window.JobApply.openApplyModal(jobId);
    } else {
        console.error('JobApply component not loaded');
        CVision.Utils.showAlert('Application component not loaded', 'error');
    }
}



/**
 * Close apply modal
 */


// ============================================================================
// Phase 3: Customization Modal Functions
// ============================================================================

// Legacy customization logic removed. Handled by JobActions.js

// Customization logic moved to JobActions.js

// ============================================================================
// Make functions available globally for onclick handlers
// ============================================================================
window.showJobDetails = showJobDetails;
window.saveJob = saveJob;

window.toggleJobSelection = toggleJobSelection;
window.clearBatchSelection = clearBatchSelection;
window.batchCustomize = batchCustomize;
window.toggleBatchMode = toggleBatchMode;
// window.showCustomizeModal = showCustomizeModal;
// window.closeCustomizeModal = closeCustomizeModal;
// window.startCustomization = startCustomization;
// window.startBrowserAutofill = startBrowserAutofill; // Deprecated - using openQuickApplyForm instead


// Logic moved to JobApply.js

// Logic moved to JobApply.js

/**
 * Generate email preview
 */
// Email application logic moved to JobApply.js

/**
 * Connect Gmail account
 */
function connectGmail() {
    window.location.href = `${CONFIG.API_BASE_URL}${CONFIG.API_PREFIX} /auth/gmail / connect`;
}

// Logic migrated to JobApply.js component
