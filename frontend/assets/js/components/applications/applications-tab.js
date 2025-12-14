window.ApplicationsTab = {
    async load() {
        const status = document.getElementById('filter-status')?.value || '';
        const priority = document.getElementById('filter-priority')?.value || '';
        const company = document.getElementById('filter-company')?.value || '';
        let url = `${API_BASE_URL}/api/v1/applications/?page=1&size=50`;
        if (status) url += `&status=${status}`;
        if (priority) url += `&priority=${priority}`;
        if (company) url += `&company=${encodeURIComponent(company)}`;

        try {
            const response = await fetch(url, {
                headers: { 'Authorization': `Bearer ${CVision.Utils.getToken()}` }
            });
            if (!response.ok) throw new Error('Failed');
            const data = await response.json();
            console.log('DEBUG loadApplications: API returned', data.applications?.length || 0, 'apps, total:', data.total);
            window.allApplications = data.applications || [];
            if (window.JobActions) {
                window.JobActions.setAppliedJobs(data.applications || []);
            }
            displayApplications(data.applications || []);
        } catch (error) {
            console.error('Load applications error:', error);
            const container = document.getElementById('applicationsList');
            if (container) {
                container.innerHTML = '<div class="bg-white rounded-lg border p-6 text-center"><p class="text-red-600">Failed to load applications</p></div>';
            }
        }
    },

    clearFilters() {
        const statusFilter = document.getElementById('filter-status');
        const priorityFilter = document.getElementById('filter-priority');
        const companyFilter = document.getElementById('filter-company');

        if (statusFilter) statusFilter.value = '';
        if (priorityFilter) priorityFilter.value = '';
        if (companyFilter) companyFilter.value = '';

        this.load();
    }
};

// Expose clearFilters globally for HTML onclick binding
window.loadApplications = () => window.ApplicationsTab.load();
window.clearFilters = () => window.ApplicationsTab.clearFilters();

// ==========================================
// MOVED LOGIC FROM applications.js
// ==========================================

function displayApplications(applications, containerId = 'applicationsList') {
    const container = document.getElementById(containerId);
    if (!container) return;

    if (!applications || applications.length === 0) {
        container.innerHTML = `
            <div class="bg-white rounded-lg border p-12 text-center">
                <h3 class="text-lg font-medium mb-2">No Applications Yet</h3>
                <p class="text-gray-600 mb-6">Start applying to jobs to track them here</p>
                <a href="jobs.html" class="btn-gradient text-white px-6 py-2 rounded-lg inline-block">Search Jobs</a>
            </div>
        `;
        return;
    }

    try {
        const htmlParts = applications.map((app, index) => {
            const isResponseTab = containerId === 'responsesList';
            return `
            <div class="bg-white rounded-lg border p-6 hover:shadow-md transition cursor-pointer" onclick="viewApplicationDetails('${app._id || app.id}')">
                <div class="flex justify-between items-start mb-4">
                    <div class="flex-1">
                        <h3 class="text-lg font-semibold">${app.job_title}</h3>
                        <p class="text-gray-600 mt-1">${app.company_name}</p>
                        <p class="text-gray-500 text-sm mt-1">${app.location || 'Remote'}</p>
                    </div>
                    <div class="flex flex-col items-end gap-2">
                        ${getStatusBadge(app.status)}
                        ${app.priority ? getPriorityBadge(app.priority) : ''}
                    </div>
                </div>
                <div class="flex justify-between items-center text-sm text-gray-500">
                    <span>Applied: ${formatDate(app.created_at)}</span>
                        ${isResponseTab ?
                    `<span class="bg-blue-50 text-blue-600 px-3 py-1 rounded-full text-xs font-medium">Response Received</span>` :
                    (app.source ? getSourceBadge(app.source) : '')
                }
                </div>
                ${isResponseTab ? `
                <div class="mt-4 pt-4 border-t border-gray-100 flex justify-end">
                    <button onclick="viewResponseDetails(event, '${app._id || app.id}')" class="text-blue-600 hover:text-blue-800 text-sm font-medium flex items-center">
                        View Response
                        <svg class="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path></svg>
                    </button>
                </div>
                ` : ''}
            </div>
            `;
        });

        container.innerHTML = htmlParts.join('');

    } catch (e) {
        console.error('Error displaying applications:', e);
    }
}

async function viewApplicationDetails(appId) {
    try {
        const [appRes, timelineRes] = await Promise.all([
            fetch(`${API_BASE_URL}/api/v1/applications/${appId}`, { headers: { 'Authorization': `Bearer ${CVision.Utils.getToken()}` } }),
            fetch(`${API_BASE_URL}/api/v1/applications/${appId}/timeline`, { headers: { 'Authorization': `Bearer ${CVision.Utils.getToken()}` } })
        ]);
        if (!appRes.ok) throw new Error('Failed');
        const app = await appRes.json();
        const timeline = timelineRes.ok ? await timelineRes.json() : { timeline: [] };
        displayApplicationModal(app, timeline.timeline);
    } catch (error) {
        console.error('Details error:', error);
        CVision.Utils.showAlert('Failed to load details', 'error');
    }
}

function displayApplicationModal(app, timeline) {
    const modalContent = document.getElementById('applicationModalContent');
    if (!modalContent) return;
    const isEmailApp = app.source === 'auto_apply';
    const monitoringEnabled = app.email_monitoring_enabled || false;

    modalContent.innerHTML = `
        <div class="flex justify-between mb-6">
            <div>
                <h2 class="text-2xl font-bold">${app.job_title}</h2>
                <p class="text-gray-600 mt-1">${app.company_name}</p>
            </div>
            <button onclick="closeModal()" class="text-gray-400 hover:text-gray-600">
                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
            </button>
        </div>
        
        <div class="grid grid-cols-2 gap-4 mb-6">
            <div><span class="text-sm text-gray-600">Status:</span> ${getStatusBadge(app.status)}</div>
            <div><span class="text-sm text-gray-600">Priority:</span> ${getPriorityBadge(app.priority)}</div>
            <div><span class="text-sm text-gray-600">Source:</span> ${getSourceBadge(app.source)}</div>
            ${isEmailApp ? `<div><span class="text-sm text-gray-600">Monitoring:</span> ${getMonitoringBadge(app)}</div>` : ''}
        </div>
        
        ${isEmailApp ? `
        <div class="mb-6 p-4 bg-purple-50 rounded-lg border border-purple-200">
            <h3 class="text-lg font-semibold mb-3 flex items-center gap-2">
                <svg class="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path>
                </svg>
                Email Agent Monitoring
            </h3>
            <div class="space-y-3">
                <div class="flex items-center justify-between">
                    <span class="text-sm text-gray-700">Auto-check for responses:</span>
                    <button onclick="event.stopPropagation(); toggleEmailMonitoring('${app._id || app.id}', ${monitoringEnabled})"                            class="px-4 py-2 text-sm rounded-lg ${monitoringEnabled ? 'bg-green-600 text-white hover:bg-green-700' : 'bg-gray-200 text-gray-700 hover:bg-gray-300'}">
                        ${monitoringEnabled ? 'Enabled' : 'Disabled'}
                    </button>
                </div>
                ${app.last_response_check ? `
                <div class="text-xs text-gray-600">
                    Last checked: ${formatDateTime(app.last_response_check)} (${app.response_check_count || 0} checks)
                </div>
                ` : ''}
                <button onclick="event.stopPropagation(); checkForResponses('${app._id || app.id}', this)" 
                        class="w-full px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 text-sm flex items-center justify-center transition-all">
                    Check for Responses Now
                </button>
            </div>
        </div>
        ` : ''}
        
        <div id="emailAnalysisSection"></div>
        
        <div>
            <h3 class="text-lg font-semibold mb-3">Timeline</h3>
            <div class="space-y-3 max-h-64 overflow-y-auto">
                ${timeline && timeline.length > 0 ? timeline.map(e => `
                    <div class="border-l-2 border-gray-200 pl-4 py-2">
                        <p class="text-sm font-medium">${e.description}</p>
                        <p class="text-xs text-gray-500">${formatDateTime(e.timestamp)}</p>
                    </div>
                `).join('') : '<p class="text-gray-500 text-sm">No timeline events</p>'}
            </div>
        </div>
    `;
    const modal = document.getElementById('applicationModal');
    if (modal) {
        modal.classList.remove('hidden');
    }

    // Render email analysis section using component
    if (window.EmailAnalysisComponent) {
        window.EmailAnalysisComponent.renderAnalysisSection(app, 'emailAnalysisSection');
    }
}

function closeModal() {
    const modal = document.getElementById('applicationModal');
    if (modal) {
        modal.classList.add('hidden');
    }
}

async function updateStatus(appId) {
    showActionModal('status', appId);
}

async function scheduleInterview(appId) {
    showActionModal('interview', appId);
}

async function setFollowUp(appId) {
    showActionModal('followup', appId);
}

function showActionModal(actionType, appId) {
    const modalContent = document.getElementById('applicationModalContent');
    if (!modalContent) return;

    let formHTML = '';

    if (actionType === 'status') {
        formHTML = `
            <div class="mb-6">
                <h2 class="text-2xl font-bold mb-4">Update Application Status</h2>
                <form id="actionForm" class="space-y-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">New Status</label>
                        <select id="statusInput" required class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500">
                            <option value="">Select status...</option>
                            <option value="draft">Draft</option>
                            <option value="submitted">Submitted</option>
                            <option value="applied">Applied</option>
                            <option value="under_review">Under Review</option>
                            <option value="interview_scheduled">Interview Scheduled</option>
                            <option value="interview_completed">Interview Completed</option>
                            <option value="second_round">Second Round</option>
                            <option value="final_round">Final Round</option>
                            <option value="offer_received">Offer Received</option>
                            <option value="offer_accepted">Offer Accepted</option>
                            <option value="offer_declined">Offer Declined</option>
                            <option value="rejected">Rejected</option>
                            <option value="withdrawn">Withdrawn</option>
                            <option value="on_hold">On Hold</option>
                            <option value="archived">Archived</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Notes (optional)</label>
                        <textarea id="notesInput" rows="3" class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500" placeholder="Add any notes about this status change..."></textarea>
                    </div>
                    <div class="flex gap-3 justify-end w-full mt-4">
                        <button type="button" onclick="closeModal()" class="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 flex-shrink-0">Cancel</button>
                        <button type="submit" class="px-6 py-2 rounded-lg flex-shrink-0 text-white" style="background-color: var(--primary-600);">Update Status</button>
                    </div>
                </form>
            </div>
        `;
    } else if (actionType === 'interview') {
        formHTML = `
            <div class="mb-6">
                <h2 class="text-2xl font-bold mb-4">Schedule Interview</h2>
                <form id="actionForm" class="space-y-4">
                    <div class="grid grid-cols-2 gap-4">
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-2">Date</label>
                            <input type="date" id="dateInput" required class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500">
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-2">Time</label>
                            <input type="time" id="timeInput" required class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500">
                        </div>
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Interview Type</label>
                        <select id="typeInput" required class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500">
                            <option value="phone_screening">Phone Screening</option>
                            <option value="video_call">Video Call</option>
                            <option value="in_person">In Person</option>
                            <option value="technical">Technical</option>
                            <option value="behavioral">Behavioral</option>
                            <option value="panel">Panel</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Location (optional)</label>
                        <input type="text" id="locationInput" class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500" placeholder="Meeting link or physical location">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Notes (optional)</label>
                        <textarea id="notesInput" rows="2" class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500" placeholder="Preparation notes, topics to cover, etc."></textarea>
                    </div>
                    <div class="flex gap-3 justify-end w-full mt-4">
                        <button type="button" onclick="closeModal()" class="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 flex-shrink-0">Cancel</button>
                        <button type="submit" class="px-6 py-2 rounded-lg flex-shrink-0 text-white" style="background-color: var(--primary-600);">Schedule Interview</button>
                    </div>
                </form>
            </div>
        `;
    } else if (actionType === 'followup') {
        formHTML = `
            <div class="mb-6">
                <h2 class="text-2xl font-bold mb-4">Set Follow-up Reminder</h2>
                <form id="actionForm" class="space-y-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Follow-up Date</label>
                        <input type="date" id="dateInput" required class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Notes (optional)</label>
                        <textarea id="notesInput" rows="3" class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500" placeholder="What do you want to follow up about?"></textarea>
                    </div>
                    <div class="flex gap-3 justify-end w-full mt-4">
                        <button type="button" onclick="closeModal()" class="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 flex-shrink-0">Cancel</button>
                        <button type="submit" class="px-6 py-2 rounded-lg flex-shrink-0 text-white" style="background-color: var(--primary-600);">Set Reminder</button>
                    </div>
                </form>
            </div>
        `;
    }

    modalContent.innerHTML = formHTML;

    // Attach form submit handler
    const form = document.getElementById('actionForm');
    if (form) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            await handleActionSubmit(actionType, appId);
        });
    }

    // Show modal
    const modal = document.getElementById('applicationModal');
    if (modal) {
        modal.classList.remove('hidden');
    }
}

async function handleActionSubmit(actionType, appId) {
    try {
        if (actionType === 'status') {
            const status = document.getElementById('statusInput').value;
            const notes = document.getElementById('notesInput').value;

            if (!status) {
                InlineMessage.error('Please select a status');
                return;
            }

            const res = await fetch(`${API_BASE_URL}/api/v1/applications/${appId}/status`, {
                method: 'PUT',
                headers: { 'Authorization': `Bearer ${CVision.Utils.getToken()}`, 'Content-Type': 'application/json' },
                body: JSON.stringify({ status, notes })
            });

            if (!res.ok) throw new Error('Failed to update status');

            InlineMessage.success('Status updated successfully');
            closeModal();
            loadApplications();
            // loadStats(); // Assuming locally available or need to export loadStats if used

        } else if (actionType === 'interview') {
            const date = document.getElementById('dateInput').value;
            const time = document.getElementById('timeInput').value;
            const type = document.getElementById('typeInput').value;
            const location = document.getElementById('locationInput').value;
            const notes = document.getElementById('notesInput').value;

            if (!date || !time) {
                InlineMessage.error('Please provide date and time');
                return;
            }

            const interviewDate = new Date(`${date}T${time}`);

            const res = await fetch(`${API_BASE_URL}/api/v1/applications/${appId}/schedule-interview`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${CVision.Utils.getToken()}`, 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    interview_date: interviewDate.toISOString(),
                    interview_type: type,
                    location: location || null,
                    notes: notes || ''
                })
            });

            if (!res.ok) throw new Error('Failed to schedule interview');

            InlineMessage.success('Interview scheduled successfully');
            closeModal();
            loadApplications();

        } else if (actionType === 'followup') {
            const date = document.getElementById('dateInput').value;
            const notes = document.getElementById('notesInput').value;

            if (!date) {
                InlineMessage.error('Please provide a follow-up date');
                return;
            }

            const followUpDate = new Date(date);

            const res = await fetch(`${API_BASE_URL}/api/v1/applications/${appId}/set-follow-up`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${CVision.Utils.getToken()}`, 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    follow_up_date: followUpDate.toISOString(),
                    notes: notes || ''
                })
            });

            if (!res.ok) throw new Error('Failed to set follow-up');

            InlineMessage.success('Follow-up reminder set successfully');
            closeModal();
            loadApplications();
        }
    } catch (error) {
        console.error('Action error:', error);
        InlineMessage.error(error.message || 'Failed to complete action');
    }
}

async function toggleEmailMonitoring(applicationId, currentlyEnabled) {
    const endpoint = currentlyEnabled ? 'disable-monitoring' : 'enable-monitoring';
    const action = currentlyEnabled ? 'disabled' : 'enabled';
    try {
        const res = await fetch(`${API_BASE_URL}/api/v1/applications/${applicationId}/${endpoint}`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${CVision.Utils.getToken()}` }
        });
        if (!res.ok) {
            const error = await res.json();
            throw new Error(error.detail || 'Failed to toggle monitoring');
        }
        InlineMessage.success(`Email monitoring ${action}`);
        loadApplications(); // Refresh the list
        viewApplicationDetails(applicationId); // Refresh the modal

    } catch (error) {
        console.error('Toggle monitoring error:', error);
        InlineMessage.error(error.message || 'Failed to toggle monitoring');
    }
}

async function checkForResponses(applicationId, btnElement) {
    if (btnElement) {
        btnElement.disabled = true;
        btnElement.innerHTML = `
            <svg class="animate-spin h-4 w-4 mr-2 text-white inline-block" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Checking...
        `;
    }

    try {
        const res = await fetch(`${API_BASE_URL}/api/v1/applications/${applicationId}/check-responses`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${CVision.Utils.getToken()}` }
        });
        if (!res.ok) {
            const error = await res.json();
            throw new Error(error.detail || 'Failed to check responses');
        }
        const data = await res.json();

        if (data.data && data.data.responses_found > 0) {
            InlineMessage.success(data.message);
        } else {
            InlineMessage.info(data.message || 'No new responses found');
        }

        if (typeof loadApplications === 'function') {
            loadApplications();
        }

        viewApplicationDetails(applicationId);

    } catch (error) {
        console.error('Check responses error:', error);
        InlineMessage.error(error.message || 'Failed to check responses');

        if (btnElement) {
            btnElement.disabled = false;
            btnElement.innerHTML = 'Check for Responses Now';
        }
    }
}

function getSourceBadge(source) {
    if (source === 'auto_apply') {
        return `<span class="inline-flex items-center gap-1 text-xs bg-purple-100 text-purple-700 px-2 py-1 rounded">
            <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path>
            </svg>
            Email Agent
        </span>`;
    }
    return `<span class="text-xs bg-gray-100 px-2 py-1 rounded">${formatEnumValue(source)}</span>`;
}

function getMonitoringBadge(app) {
    if (app.source !== 'auto_apply') return '';
    if (app.email_monitoring_enabled) {
        return `<span class="inline-flex items-center gap-1 text-xs bg-green-100 text-green-700 px-2 py-1 rounded">
            <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                <path d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"></path>
            </svg>
            Monitoring
        </span>`;
    }
    return `<span class="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">Manual</span>`;
}


// Expose functions globally
window.displayApplications = displayApplications;
window.viewApplicationDetails = viewApplicationDetails;
window.displayApplicationModal = displayApplicationModal;
window.closeModal = closeModal;
window.updateStatus = updateStatus;
window.scheduleInterview = scheduleInterview;
window.setFollowUp = setFollowUp;
window.toggleEmailMonitoring = toggleEmailMonitoring;
window.checkForResponses = checkForResponses;

