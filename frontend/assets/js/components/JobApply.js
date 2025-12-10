/**
 * JobApply.js
 * 
 * Reusable component for handling job applications.
 * Manages the "Apply" modal, CV/Cover Letter selection, and transition to Quick Apply.
 */

class JobApplyComponent {
    constructor() {
        this.currentJobId = null;
        this.apiBaseUrl = '/api/v1'; // Adjust as needed based on config

        // Bind methods
        this.openApplyModal = this.openApplyModal.bind(this);
        this.closeApplyModal = this.closeApplyModal.bind(this);
        this.handleNextStep = this.handleNextStep.bind(this);
        this.loadDocuments = this.loadDocuments.bind(this);
    }

    /**
     * Initialize the component
     */
    init() {
        // Inject modal if not present
        if (!document.getElementById('applyModal')) {
            this.injectModal();
        }

        // Global aliases for HTML onclick handlers
        window.openApplyModal = (jobId) => this.openApplyModal(jobId);
        window.closeApplyModal = this.closeApplyModal;
        window.handleApplyNextStep = this.handleNextStep; // For the "Next" button
    }

    /**
     * Inject the Apply Modal into the DOM
     */
    injectModal() {
        const modalHTML = `
            <div id="applyModal" class="fixed inset-0 bg-black bg-opacity-50 hidden items-center justify-center z-50 p-4">
                <div class="bg-white rounded-xl shadow-2xl max-w-md w-full p-6 transform transition-all">
                    <div class="flex justify-between items-center mb-4">
                        <h3 class="text-xl font-bold text-gray-900">Quick Apply</h3>
                        <button onclick="JobApply.closeApplyModal()" class="text-gray-400 hover:text-gray-600 transition-colors">
                            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                            </svg>
                        </button>
                    </div>

                    <div class="mb-4">
                        <p class="text-gray-600 mb-2">Applying to:</p>
                        <p class="font-semibold text-gray-900" id="applyModalJobTitle">Job Title</p>
                        <p class="text-sm text-gray-500" id="applyModalCompanyName">Company Name</p>
                    </div>

                    <div class="space-y-4">
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-2">Select CV *</label>
                            <select id="applyModalCvSelect" class="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-colors">
                                <option value="">Loading CVs...</option>
                            </select>
                        </div>

                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-2">Select Cover Letter (Optional)</label>
                            <select id="applyModalCoverLetterSelect" class="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-colors">
                                <option value="">Loading cover letters...</option>
                            </select>
                        </div>
                    </div>

                    <div class="flex gap-3 mt-6">
                        <button onclick="JobApply.closeApplyModal()" class="flex-1 border border-gray-300 text-gray-700 rounded-lg px-4 py-2 font-medium hover:bg-gray-50 transition-colors">
                            Cancel
                        </button>
                        <button onclick="JobApply.handleNextStep()" class="flex-1 btn-gradient text-white rounded-lg px-4 py-2 font-medium hover:shadow-lg transition-all shadow-md">
                            Next: Application Details
                        </button>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHTML);
    }

    /**
     * Open the apply modal for a specific job
     * @param {string} jobId 
     * @param {Object} [jobObject] - Optional job object if available
     */
    async openApplyModal(jobId, jobObject = null) {
        console.log('JobApply: Opening Apply Modal', { jobId, jobObject });
        this.currentJobId = jobId;

        // Use passed object if available, otherwise try to find it
        let job = jobObject;

        if (!job && window.currentJobs && Array.isArray(window.currentJobs)) {
            job = window.currentJobs.find(j => (j._id || j.id) === jobId);
        }

        // Fallback for different page structures
        if (!job && window.allApplications) {
            const app = window.allApplications.find(a => (a.job_id === jobId || a._id === jobId));
            job = app ? app.job : null;
        }

        if (!job && window.currentSavedJobs) {
            job = window.currentSavedJobs.find(j => (j._id || j.id) === jobId);
        }

        console.log('JobApply: Resolved job object:', job);

        const modal = document.getElementById('applyModal');
        const titleEl = document.getElementById('applyModalJobTitle');
        const companyEl = document.getElementById('applyModalCompanyName');
        const cvSelect = document.getElementById('applyModalCvSelect');

        console.log('JobApply: DOM Elements:', {
            modal: !!modal,
            titleEl: !!titleEl,
            companyEl: !!companyEl,
            cvSelect: !!cvSelect
        });

        if (modal) {
            if (job) {
                // Handle both Job objects (title) and Application objects (job_title)
                const title = job.title || job.job_title || 'No Title';
                const company = job.company_name || job.company || 'No Company';

                if (titleEl) titleEl.textContent = title;
                if (companyEl) companyEl.textContent = company;
            } else {
                if (titleEl) titleEl.textContent = 'Unknown Position';
                console.warn('JobApply: Job details not found for ID:', jobId);
            }

            modal.classList.remove('hidden');
            modal.classList.add('flex');

            // Load docs
            await this.loadDocuments();
        } else {
            console.error('JobApply: Apply modal element not found in DOM');
            // detailed re-check would be needed or just fail gracefully
        }

        // Auto-save the job if not already saved
        this._handleAutoSave(jobId);
    }

    /**
     * Check if job is saved and save it if not
     * @param {string} jobId 
     */
    async _handleAutoSave(jobId) {
        // If job is from currentSavedJobs, it's already saved - skip
        if (window.currentSavedJobs && Array.isArray(window.currentSavedJobs)) {
            const isSaved = window.currentSavedJobs.some(j => (j._id || j.id) == jobId);
            if (isSaved) {
                console.log('JobApply: Job is from saved jobs, skipping auto-save');
                return;
            }
        }

        // Check if we are on a page with save buttons (jobs.js context)
        // Saved buttons usually have 'text-primary-600' class when saved
        let isAlreadySaved = false;

        const saveBtns = document.querySelectorAll(`[onclick*="saveJob('${jobId}')"]`);
        if (saveBtns.length > 0) {
            // If any button has the primary color, it's saved
            saveBtns.forEach(btn => {
                if (btn.classList.contains('text-primary-600')) {
                    isAlreadySaved = true;
                }
            });
        }

        if (isAlreadySaved) {
            console.log('JobApply: Job already saved, skipping auto-save');
            return;
        }

        console.log('JobApply: Auto-saving job...');

        if (typeof window.saveJob === 'function') {
            // Use existing global function with silent=true
            await window.saveJob(jobId, true);
        } else {
            // Fallback API call
            try {
                const token = CVision.Utils.getToken();
                await fetch(`/api/v1/jobs/save/${jobId}`, {
                    method: 'POST',
                    headers: { 'Authorization': `Bearer ${token}` }
                });
            } catch (e) {
                console.warn('JobApply: Auto-save failed', e);
            }
        }
    }

    /**
     * Close the apply modal
     */
    closeApplyModal() {
        const modal = document.getElementById('applyModal');
        if (modal) {
            modal.classList.add('hidden');
            modal.classList.remove('flex');
        }
        // Don't clear currentJobId immediately if we are proceeding to next step
    }

    /**
     * Load CVs and Cover Letters
     */
    async loadDocuments() {
        console.log('JobApply: Loading documents...');
        try {
            // Load CVs
            const cvResponse = await fetch('/api/v1/documents/?document_type=cv', {
                headers: { 'Authorization': `Bearer ${CVision.Utils.getToken()}` }
            });

            console.log('JobApply: CV Response status:', cvResponse.status);

            const cvSelect = document.getElementById('applyModalCvSelect');
            if (cvResponse.ok && cvSelect) {
                const data = await cvResponse.json();
                console.log('JobApply: CV Data:', data);

                const docs = data.documents || [];
                if (docs.length > 0) {
                    // Add default option
                    let options = '<option value="">Select a CV...</option>';
                    options += docs.map(doc => `<option value="${doc.id}">${doc.filename}</option>`).join('');
                    cvSelect.innerHTML = options;

                    // Auto-select the first one ONLY if exactly one exists
                    if (docs.length === 1) {
                        cvSelect.value = docs[0].id;
                    }
                } else {
                    cvSelect.innerHTML = '<option value="">No CVs found</option>';
                }
            }

            // Load Cover Letters
            const clResponse = await fetch('/api/v1/documents/?document_type=cover_letter', {
                headers: { 'Authorization': `Bearer ${CVision.Utils.getToken()}` }
            });

            const clSelect = document.getElementById('applyModalCoverLetterSelect');
            if (clResponse.ok && clSelect) {
                const data = await clResponse.json();
                const docs = data.documents || [];
                if (docs.length > 0) {
                    clSelect.innerHTML = '<option value="">No cover letter</option>' +
                        docs.map(doc => `<option value="${doc.id}">${doc.filename}</option>`).join('');
                } else {
                    clSelect.innerHTML = '<option value="">No cover letters found</option>';
                }
            }

        } catch (error) {
            console.error('Failed to load documents', error);
        }
    }

    /**
     * Handle "Next" button click - transition to Quick Apply Form
     */
    handleNextStep() {
        const cvId = document.getElementById('applyModalCvSelect')?.value;
        const coverLetterId = document.getElementById('applyModalCoverLetterSelect')?.value;

        if (!cvId) {
            // Use standard alert if Utils not available, otherwise usage utils
            if (window.CVision && window.CVision.Utils) {
                CVision.Utils.showAlert('Please select a CV', 'warning');
            } else {
                alert('Please select a CV');
            }
            return;
        }

        this.closeApplyModal();

        // Call the global openQuickApplyForm function if it exists (legacy/current implementation)
        // Or if we move that logic here, we call the internal method.
        // For now, based on instructions, we are bridging to the existing form logic which seems complex.
        if (typeof window.openQuickApplyForm === 'function') {
            window.openQuickApplyForm(this.currentJobId, cvId, coverLetterId);
        } else {
            console.error('openQuickApplyForm function not found');
            alert('Navigation failed: Quick Apply form missing.');
        }
    }
}

// Initialize and expose globally as JobApply
window.JobApply = new JobApplyComponent();
window.JobApply.init();
