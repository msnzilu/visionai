/**
 * JobCard Component
 * 
 * A standalone, reusable component for rendering job cards and their detailed modals.
 * Features:
 * - Consistent rendering of job cards with match scores and auto-apply badges.
 * - Integrated job details modal.
 * - Batch selection support.
 * - Integration with JobActions and JobApply components.
 */

class JobCardComponent {
    constructor() {
        this.currentJobs = [];
        this.initialized = false;

        // Batch selection state
        this.batchModeActive = false;
        this.selectedJobs = new Set();

        // Bind methods
        this.render = this.render.bind(this);
        this.showDetails = this.showDetails.bind(this);
        this.closeDetails = this.closeDetails.bind(this);
        this.toggleJobSelection = this.toggleJobSelection.bind(this);
    }

    /**
     * Initialize the component
     * @param {Object} options - Configuration options
     */
    init(options = {}) {
        if (this.initialized) return;

        // Set up global references
        window.JobCard = this;
        // For legacy onclick handlers
        window.showJobDetails = (jobId) => this.showDetails(jobId);
        window.toggleJobSelection = (jobId, checkbox) => this.toggleJobSelection(jobId, checkbox);

        this.initialized = true;
    }

    /**
     * Setting the current jobs list for details lookup
     * @param {Array} jobs 
     */
    setJobs(jobs) {
        this.currentJobs = jobs;
    }

    /**
     * Decodes HTML entities for safe display
     */
    decodeHtmlEntities(text) {
        if (!text) return '';
        const textArea = document.createElement('textarea');
        textArea.innerHTML = text;
        return textArea.value;
    }

    /**
     * Formats enum values for display (e.g., full_time -> Full Time)
     */
    formatEnumValue(value) {
        if (!value) return '';
        return value.split('_')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ');
    }

    /**
     * Renders a single job card
     * @param {Object} job - The job data object
     * @returns {HTMLElement} The card element
     */
    render(job) {
        const card = document.createElement('div');
        card.className = 'job-card bg-white rounded-xl shadow-sm border border-gray-100 hover:shadow-lg transition-all duration-300 relative overflow-hidden group flex flex-col h-full';

        // Match Score Gradient Border
        const matchBorder = job.match_score
            ? `<div class="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-green-400 to-primary-500 transform scale-x-0 group-hover:scale-x-100 transition-transform duration-300 origin-left"></div>`
            : '';

        // Batch Selection Checkbox
        const batchCheckboxHTML = this.batchModeActive ? `
            <div class="absolute top-4 left-4 z-10">
                <input type="checkbox" 
                       class="job-select-checkbox w-5 h-5 rounded text-primary-600 border-gray-300 focus:ring-primary-500" 
                       ${this.selectedJobs.has(String(job._id || job.id)) ? 'checked' : ''}
                       onchange="toggleJobSelection('${job._id || job.id}', this)">
            </div>
        ` : '';

        // Badges
        const matchBadge = job.match_score
            ? `<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 mr-2">
                 <svg class="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"/></svg>
                 ${Math.round(job.match_score * 100)}% Match
               </span>`
            : '';

        const canAutoApply = !!(
            job.application_email ||
            job.contact_email ||
            job.email ||
            (job.company_info?.contact?.email) ||
            job.application_url ||
            job.external_url ||
            job.apply_url
        );

        const autoApplyBadge = canAutoApply
            ? '' // Keep it clean for auto-apply
            : `<span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-800 border border-amber-200 shadow-sm">
                 <svg class="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/></svg>
                 Manual Application Required
               </span>`;

        const formatDate = window.CVision ? window.CVision.formatDate : (d) => new Date(d).toLocaleDateString();

        card.innerHTML = `
            ${matchBorder}
            ${batchCheckboxHTML}
            
            <div class="p-6 flex-1 flex flex-col cursor-pointer" onclick="showJobDetails('${job._id || job.id}')">
                <div class="flex justify-between items-start mb-4 ${this.batchModeActive ? 'ml-8' : ''}">
                    <div class="flex-1 min-w-0 pr-4">
                        <div class="flex items-center gap-2 mb-1">
                            ${matchBadge}
                            ${autoApplyBadge}
                            <span class="text-xs text-gray-500 flex items-center ml-2">
                                <svg class="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                                ${formatDate(job.posted_date || job.created_at)}
                            </span>
                        </div>
                        <h3 class="text-xl font-bold text-gray-900 leading-tight group-hover:text-primary-600 transition-colors line-clamp-2" title="${this.decodeHtmlEntities(job.title)}">
                            ${this.decodeHtmlEntities(job.title)}
                        </h3>
                        <p class="text-base text-gray-600 font-medium mt-1 truncate">${this.decodeHtmlEntities(job.company_name)}</p>
                    </div>
                    
                    <button class="save-job-btn p-2 rounded-full hover:bg-gray-100 ${job.is_saved ? 'text-primary-600' : 'text-gray-400'} hover:text-primary-600 transition-colors flex-shrink-0" 
                            onclick="event.stopPropagation(); window.saveJob('${job._id || job.id}')" title="${job.is_saved ? 'Saved' : 'Save Job'}">
                        <svg class="w-6 h-6" fill="${job.is_saved ? 'currentColor' : 'none'}" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"/>
                        </svg>
                    </button>
                </div>

                <div class="flex flex-wrap items-center gap-y-2 gap-x-4 text-sm text-gray-500 mb-4 ${this.batchModeActive ? 'ml-8' : ''}">
                    <div class="flex items-center">
                        <svg class="w-4 h-4 mr-1.5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"/></svg>
                        ${this.decodeHtmlEntities(job.location)}
                    </div>
                    ${job.salary_range && (job.salary_range.min_amount || job.salary_range.max_amount) ? `
                        <div class="flex items-center">
                            <svg class="w-4 h-4 mr-1.5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                            ${job.salary_range.min_amount ? `${job.salary_range.min_amount.toLocaleString()} ` : ''}
                            ${job.salary_range.min_amount && job.salary_range.max_amount ? '- ' : ''}
                            ${job.salary_range.max_amount ? `${job.salary_range.max_amount.toLocaleString()} ` : ''}
                            ${job.salary_range.currency || 'USD'}
                        </div>
                    ` : ''}
                </div>

                <div class="flex flex-wrap gap-2 mb-4 ${this.batchModeActive ? 'ml-8' : ''}">
                    ${job.employment_type ? `<span class="px-2.5 py-0.5 bg-blue-50 text-blue-700 rounded-md text-xs font-medium border border-blue-100">${this.formatEnumValue(job.employment_type)}</span>` : ''}
                    ${job.work_arrangement ? `<span class="px-2.5 py-0.5 bg-purple-50 text-purple-700 rounded-md text-xs font-medium border border-purple-100">${this.formatEnumValue(job.work_arrangement)}</span>` : ''}
                </div>

                <p class="text-gray-600 text-sm line-clamp-3 mb-4 leading-relaxed ${this.batchModeActive ? 'ml-8' : ''}">
                    ${job.description ? this.decodeHtmlEntities(job.description).replace(/<[^>]*>?/gm, '') : 'No description available'}
                </p>

                ${(() => {
                // Handle skills_required as either array or comma-separated string
                let skills = job.skills_required;
                if (typeof skills === 'string') {
                    skills = skills.split(',').map(s => s.trim()).filter(s => s);
                }
                if (skills && skills.length > 0) {
                    return `
                    <div class="mt-auto pt-4 border-t border-gray-50 ${this.batchModeActive ? 'ml-8' : ''}">
                        <div class="flex flex-wrap gap-2">
                            ${skills.slice(0, 3).map(skill =>
                        `<span class="px-2 py-1 bg-gray-100 text-gray-600 rounded text-xs font-medium">${this.decodeHtmlEntities(skill)}</span>`
                    ).join('')}
                            ${skills.length > 3 ? `
                                <span class="px-2 py-1 text-gray-400 text-xs">+${skills.length - 3}</span>
                            ` : ''}
                        </div>
                    </div>
                        `;
                }
                return '';
            })()}
            </div>

            <div class="mt-4">
                ${window.JobActions ? window.JobActions.getButtonsHTML(job) : ''}
            </div>
        `;

        return card;
    }

    /**
     * Shows the job details modal
     * @param {string} jobId 
     */
    showDetails(jobId) {
        const job = this.currentJobs.find(j => (j._id || j.id) === jobId);
        if (!job) return;

        document.getElementById('modalTitle').textContent = job.title;
        document.getElementById('modalCompany').textContent = job.company_name;
        document.getElementById('modalLocation').textContent = job.location;

        const canAutoApply = (
            job.application_email ||
            job.contact_email ||
            job.email ||
            (job.company_info?.contact?.email) ||
            job.application_url ||
            job.external_url ||
            job.apply_url
        );

        const content = document.getElementById('modalContent');
        content.innerHTML = `
            ${job.match_score ? `
                <div class="bg-green-50 border border-green-200 rounded-lg p-4 mb-4">
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

            <div class="flex gap-3 flex-wrap mb-4">
                ${job.employment_type ? `<span class="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm">${this.formatEnumValue(job.employment_type)}</span>` : ''}
                ${job.work_arrangement ? `<span class="px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm">${this.formatEnumValue(job.work_arrangement)}</span>` : ''}
                ${canAutoApply
                ? '' // Flagging manual only
                : `<span class="px-3 py-1 bg-amber-100 text-amber-800 border border-amber-200 shadow-sm rounded-full text-sm flex items-center font-semibold">
                        <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/></svg>
                        Manual Application Required
                       </span>`}
            </div>

            <div class="mt-4">
                <h4 class="font-semibold mb-2">Job Description</h4>
                <p class="text-gray-700 whitespace-pre-line">${job.description || 'No description available'}</p>
            </div>

            ${job.salary_range && (job.salary_range.min_amount || job.salary_range.max_amount) ? `
                <div class="mt-4">
                    <h4 class="font-semibold mb-2">Salary Range</h4>
                    <p class="text-gray-700">
                        ${job.salary_range.min_amount ? `${job.salary_range.min_amount.toLocaleString()} ` : ''}
                        ${job.salary_range.min_amount && job.salary_range.max_amount ? '- ' : ''}
                        ${job.salary_range.max_amount ? `${job.salary_range.max_amount.toLocaleString()} ` : ''}
                        ${job.salary_range.currency || 'USD'}
                        <span class="text-sm text-gray-500 ml-1">(${job.salary_range.period || 'yearly'})</span>
                    </p>
                </div>
            ` : ''}

            ${(() => {
                // Handle skills_required as either array or comma-separated string
                let skills = job.skills_required;
                if (typeof skills === 'string') {
                    skills = skills.split(',').map(s => s.trim()).filter(s => s);
                }
                const hasRequirements = job.requirements && job.requirements.length > 0;
                const hasSkills = skills && skills.length > 0;

                if (hasRequirements || hasSkills) {
                    return `
                <div class="mt-6">
                    <h4 class="font-semibold mb-3">Requirements & Skills</h4>
                    
                    ${hasRequirements ? `
                        <ul class="list-disc list-inside text-gray-700 mb-4 space-y-1">
                            ${job.requirements.map(req =>
                        `<li class="text-sm">${this.decodeHtmlEntities(req.requirement || req)}</li>`
                    ).join('')}
                        </ul>
                    ` : ''}

                    <div class="flex flex-wrap gap-2">
                        ${hasSkills ? skills.map(skill =>
                        `<span class="px-3 py-1.5 bg-gray-50 text-gray-700 border border-gray-200 rounded-lg text-sm font-medium hover:bg-white hover:shadow-sm transition-all">${this.decodeHtmlEntities(skill)}</span>`
                    ).join('') : ''}
                    </div>
                </div>
                    `;
                }
                return '';
            })()}

            ${job.benefits && job.benefits.length > 0 ? `
                <div class="mt-6 pb-2">
                    <h4 class="font-semibold mb-3">Benefits</h4>
                    <div class="flex flex-wrap gap-2">
                        ${job.benefits.map(benefit =>
                `<span class="px-3 py-1.5 bg-green-50 text-green-700 border border-green-100 rounded-lg text-sm font-medium">
                                ${this.decodeHtmlEntities(benefit.name || benefit)}
                             </span>`
            ).join('')}
                    </div>
                </div>
            ` : ''}

            <div class="mt-6 pt-6 border-t border-gray-100">
                <h4 class="font-semibold text-lg mb-3">Generated Documents</h4>
                ${window.JobActions ? window.JobActions.getButtonsHTML(job, false) : ''}
            </div>
        `;

        // Wire up Modal Buttons (Save, Customize, Apply)
        this.wireModalActions(job);

        // Show modal
        const modal = document.getElementById('jobModal');
        modal.classList.remove('hidden');
        modal.classList.add('flex');
    }

    /**
     * Wires up buttons in the modal
     */
    wireModalActions(job) {
        const jobId = job._id || job.id;

        // Save button
        const saveBtn = document.getElementById('modalSaveJob');
        if (saveBtn) {
            saveBtn.onclick = () => window.saveJob(jobId);
            if (job.is_saved) {
                saveBtn.innerHTML = `<svg class="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 24 24"><path d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"/></svg> Saved`;
                saveBtn.className = 'flex items-center text-primary-600 font-medium';
            } else {
                saveBtn.innerHTML = 'Save Job';
                saveBtn.className = 'flex items-center text-gray-700 font-medium hover:text-primary-600';
            }
        }

        // Apply Status & Actions
        const isApplied = window.JobActions && window.JobActions.appliedJobIds.has(String(jobId));

        const customizeBtn = document.getElementById('modalCustomize');
        if (customizeBtn) {
            customizeBtn.style.display = isApplied ? 'none' : 'flex';
            customizeBtn.onclick = () => window.JobActions.openCustomizeModal(jobId);
        }

        const applyBtn = document.getElementById('modalApply');
        if (applyBtn) {
            if (isApplied) {
                applyBtn.disabled = true;
                applyBtn.innerHTML = `<svg class="w-5 h-5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg> Applied`;
                applyBtn.className = 'flex-1 bg-green-50 text-green-700 border border-green-200 rounded-lg px-4 py-2.5 text-sm font-semibold opacity-80 cursor-not-allowed flex items-center justify-center gap-2';
            } else {
                applyBtn.disabled = false;
                applyBtn.innerHTML = `<svg class="w-5 h-5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg> Apply Now`;
                applyBtn.className = 'flex-1 btn-gradient text-white rounded-lg px-4 py-2.5 text-sm font-semibold hover:shadow-lg transition-all shadow-md flex items-center justify-center gap-2';
                applyBtn.onclick = () => window.JobApply.openApplyModal(jobId, job);
            }
        }
    }

    /**
     * Closes the job modal
     */
    closeDetails() {
        const modal = document.getElementById('jobModal');
        if (modal) {
            modal.classList.add('hidden');
            modal.classList.remove('flex');
        }
    }

    /**
     * Handles batch selection
     */
    toggleJobSelection(jobId, checkbox) {
        if (checkbox.checked) {
            this.selectedJobs.add(String(jobId));
        } else {
            this.selectedJobs.delete(String(jobId));
        }

        // Dispatch event for page-specific handling (e.g. updating counts)
        document.dispatchEvent(new CustomEvent('job:selectionUpdated', {
            detail: { selectedCount: this.selectedJobs.size }
        }));
    }
}

// Global initialization
document.addEventListener('DOMContentLoaded', () => {
    const component = new JobCardComponent();
    component.init();
});
