const API_BASE_URL = `${CONFIG.API_BASE_URL}`;
let currentTab = 'applications';
let notificationPollingInterval = null;

document.addEventListener('DOMContentLoaded', () => {
    if (!CVision.Utils.isAuthenticated()) {
        window.location.href = '../login.html';
        return;
    }

    initNavbar();
    loadStats();
    loadApplications();
});

// ==================== NAVBAR FUNCTIONS ====================
async function initNavbar() {
    setupNavbarEventListeners();
    await loadNavbarUserInfo();
    await loadNavbarNotifications();
    startNotificationPolling();
}

function setupNavbarEventListeners() {
    const notificationBtn = document.getElementById('notificationBtn');
    const notificationDropdown = document.getElementById('notificationDropdown');

    if (notificationBtn) {
        notificationBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            notificationDropdown?.classList.toggle('show');
            document.getElementById('userDropdown')?.classList.remove('show');
            document.getElementById('mobileMenu')?.classList.remove('show');
        });
    }

    const userMenuBtn = document.getElementById('userMenuBtn');
    const userDropdown = document.getElementById('userDropdown');

    if (userMenuBtn) {
        userMenuBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            userDropdown?.classList.toggle('show');
            notificationDropdown?.classList.remove('show');
            document.getElementById('mobileMenu')?.classList.remove('show');
        });
    }

    const mobileMenuBtn = document.getElementById('mobileMenuBtn');
    if (mobileMenuBtn) {
        mobileMenuBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            document.getElementById('mobileMenu')?.classList.toggle('show');
            notificationDropdown?.classList.remove('show');
            userDropdown?.classList.remove('show');
        });
    }

    document.getElementById('markAllReadBtn')?.addEventListener('click', markAllNotificationsAsRead);

    document.addEventListener('click', () => {
        notificationDropdown?.classList.remove('show');
        userDropdown?.classList.remove('show');
    });
}

async function loadNavbarUserInfo() {
    const token = localStorage.getItem('token');
    if (!token) return;

    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/users/me`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (response.ok) {
            const data = await response.json();
            const user = data.user || data;

            const fullName = user.full_name || user.email || 'User';
            document.getElementById('userFullName').textContent = fullName;
            document.getElementById('userEmail').textContent = user.email;

            const initials = fullName.split(' ').map(n => n[0]).join('').toUpperCase().substring(0, 2);
            document.getElementById('userInitials').textContent = initials;

            const tier = user.subscription_tier || 'free';
            document.getElementById('navUserTier').textContent = tier.charAt(0).toUpperCase() + tier.slice(1);
        }
    } catch (error) {
        console.error('Error loading user info:', error);
    }
}

async function loadNavbarNotifications() {
    const token = localStorage.getItem('token');
    if (!token) return;

    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/notifications/?limit=10&unread_only=false`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (response.ok) {
            const notifications = await response.json();
            displayNavbarNotifications(notifications);
            updateNotificationBadge(notifications);
        }
    } catch (error) {
        console.error('Error loading notifications:', error);
    }
}

function displayNavbarNotifications(notifications) {
    const container = document.getElementById('notificationsList');
    if (!container) return;

    if (!notifications || notifications.length === 0) {
        container.innerHTML = `
            <div class="text-center py-12 text-gray-500">
                <svg class="w-12 h-12 mx-auto mb-3 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"></path>
                </svg>
                <p class="text-sm">No notifications yet</p>
            </div>
        `;
        return;
    }

    container.innerHTML = notifications.map(notif => {
        const isUnread = !notif.is_read;
        const timeAgo = formatNotificationTime(notif.created_at);
        const icon = getNotificationIcon(notif.type);

        return `
            <div class="notification-item ${isUnread ? 'unread' : ''} px-4 py-3 cursor-pointer" 
                 onclick="markNotificationAsRead('${notif.id}')">
                <div class="flex items-start space-x-3">
                    <div class="flex-shrink-0 mt-1">${icon}</div>
                    <div class="flex-1 min-w-0">
                        <p class="text-sm font-medium text-gray-900 ${isUnread ? 'font-semibold' : ''}">${notif.title}</p>
                        <p class="text-sm text-gray-600 mt-1">${notif.message}</p>
                        <p class="text-xs text-gray-500 mt-1">${timeAgo}</p>
                    </div>
                    ${isUnread ? '<div class="flex-shrink-0"><div class="w-2 h-2 bg-blue-600 rounded-full"></div></div>' : ''}
                </div>
            </div>
        `;
    }).join('');
}

function updateNotificationBadge(notifications) {
    const unreadCount = notifications.filter(n => !n.is_read).length;
    const badge = document.getElementById('notificationBadge');

    if (badge) {
        if (unreadCount > 0) {
            badge.textContent = unreadCount > 99 ? '99+' : unreadCount;
            badge.classList.remove('hidden');
        } else {
            badge.classList.add('hidden');
        }
    }
}

function getNotificationIcon(type) {
    const icons = {
        'job_match': '<svg class="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path></svg>',
        'application_update': '<svg class="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>',
        'document_processed': '<svg class="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>',
        'test': '<svg class="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>'
    };
    return icons[type] || icons['test'];
}

function formatNotificationTime(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const seconds = Math.floor((now - date) / 1000);

    if (seconds < 60) return 'Just now';
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    if (seconds < 604800) return `${Math.floor(seconds / 86400)}d ago`;
    return date.toLocaleDateString();
}

async function markNotificationAsRead(notificationId) {
    const token = localStorage.getItem('token');
    if (!token) return;

    try {
        await fetch(`${API_BASE_URL}/api/v1/notifications/${notificationId}/read`, {
            method: 'PUT',
            headers: { 'Authorization': `Bearer ${token}` }
        });
        await loadNavbarNotifications();
    } catch (error) {
        console.error('Error marking notification as read:', error);
    }
}

async function markAllNotificationsAsRead() {
    const token = localStorage.getItem('token');
    if (!token) return;

    try {
        await fetch(`${API_BASE_URL}/api/v1/notifications/mark-all-read`, {
            method: 'PUT',
            headers: { 'Authorization': `Bearer ${token}` }
        });
        await loadNavbarNotifications();
    } catch (error) {
        console.error('Error marking all as read:', error);
    }
}

function startNotificationPolling() {
    notificationPollingInterval = setInterval(loadNavbarNotifications, 30000);
}

function stopNotificationPolling() {
    if (notificationPollingInterval) {
        clearInterval(notificationPollingInterval);
    }
}

function logoutUser() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    stopNotificationPolling();
    window.location.href = '../login.html';
}

// ==================== APPLICATION PAGE FUNCTIONS ====================
function switchTab(tab) {
    currentTab = tab;
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('border-primary-600', 'text-primary-600');
        btn.classList.add('border-transparent', 'text-gray-500');
    });

    const tabElement = document.getElementById(`tab-${tab}`);
    if (tabElement) {
        tabElement.classList.remove('border-transparent', 'text-gray-500');
        tabElement.classList.add('border-primary-600', 'text-primary-600');
    }

    document.querySelectorAll('.tab-content').forEach(content => content.classList.add('hidden'));

    const contentElement = document.getElementById(`content-${tab}`);
    if (contentElement) {
        contentElement.classList.remove('hidden');
    }

    if (tab === 'applications') loadApplications();
    else if (tab === 'interviews') loadUpcomingInterviews();
    else if (tab === 'followups') loadFollowUps();
    else if (tab === 'saved') loadSavedJobs();
}

async function loadStats() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/applications/stats/overview`, {
            headers: { 'Authorization': `Bearer ${CVision.Utils.getToken()}` }
        });
        if (!response.ok) throw new Error('Failed');
        const stats = await response.json();

        const statsContainer = document.getElementById('statsOverview');
        if (statsContainer) {
            statsContainer.innerHTML = `
                <div class="bg-white rounded-lg shadow-sm border p-6">
                    <div class="text-sm text-gray-600 mb-1">Total Applications</div>
                    <div class="text-3xl font-bold text-gray-900">${stats.total_applications || 0}</div>
                </div>
                <div class="bg-white rounded-lg shadow-sm border p-6">
                    <div class="text-sm text-gray-600 mb-1">Active</div>
                    <div class="text-3xl font-bold text-blue-600">${stats.active_applications || 0}</div>
                </div>
                <div class="bg-white rounded-lg shadow-sm border p-6">
                    <div class="text-sm text-gray-600 mb-1">Interviews</div>
                    <div class="text-3xl font-bold text-purple-600">${stats.interview_count || 0}</div>
                </div>
                <div class="bg-white rounded-lg shadow-sm border p-6">
                    <div class="text-sm text-gray-600 mb-1">Success Rate</div>
                    <div class="text-3xl font-bold text-green-600">${stats.success_rate ? Math.round(stats.success_rate * 100) : 0}%</div>
                </div>
            `;
        }
    } catch (error) {
        console.error('Stats error:', error);
    }
}

async function loadApplications() {
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
}

function displayApplications(applications) {
    const container = document.getElementById('applicationsList');
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

    container.innerHTML = applications.map(app => `
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
                ${app.source ? `<span class="text-xs bg-gray-100 px-2 py-1 rounded">${formatEnumValue(app.source)}</span>` : ''}
            </div>
        </div>
    `).join('');
}

function getStatusBadge(status) {
    const colors = {
        draft: 'bg-gray-100 text-gray-700',
        submitted: 'bg-blue-100 text-blue-700',
        applied: 'bg-blue-100 text-blue-800',
        under_review: 'bg-indigo-100 text-indigo-800',
        interview_scheduled: 'bg-purple-100 text-purple-800',
        interview_completed: 'bg-purple-200 text-purple-900',
        second_round: 'bg-violet-100 text-violet-800',
        final_round: 'bg-violet-200 text-violet-900',
        offer_received: 'bg-green-100 text-green-800',
        offer_accepted: 'bg-green-600 text-white',
        offer_declined: 'bg-yellow-100 text-yellow-800',
        rejected: 'bg-red-100 text-red-800',
        withdrawn: 'bg-gray-200 text-gray-700',
        on_hold: 'bg-orange-100 text-orange-800',
        archived: 'bg-gray-300 text-gray-600'
    };
    return `<span class="status-badge ${colors[status] || colors.draft}">${formatEnumValue(status)}</span>`;
}

function getPriorityBadge(priority) {
    const colors = { high: 'bg-red-100 text-red-700', medium: 'bg-yellow-100 text-yellow-700', low: 'bg-green-100 text-green-700' };
    return `<span class="px-2 py-1 rounded text-xs font-medium ${colors[priority] || colors.medium}">${formatEnumValue(priority)} Priority</span>`;
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

function closeModal() {
    const modal = document.getElementById('applicationModal');
    if (modal) {
        modal.classList.add('hidden');
    }
}

async function updateStatus(appId) {
    showActionModal('status', appId);
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
            loadStats();

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

async function scheduleInterview(appId) {
    showActionModal('interview', appId);
}

async function setFollowUp(appId) {
    showActionModal('followup', appId);
}

async function loadUpcomingInterviews() {
    const container = document.getElementById('interviewsList');
    if (!container) return;

    try {
        const res = await fetch(`${API_BASE_URL}/api/v1/applications/upcoming-interviews?days_ahead=30`, {
            headers: { 'Authorization': `Bearer ${CVision.Utils.getToken()}` }
        });

        // Handle 400 errors gracefully (likely no interviews scheduled)
        if (res.status === 400 || !res.ok) {
            console.log('No interviews found or endpoint returned error:', res.status);
            container.innerHTML = '<div class="bg-white rounded-lg border p-12 text-center"><p class="text-gray-600">No upcoming interviews</p></div>';
            return;
        }

        const data = await res.json();

        if (!data.interviews || data.interviews.length === 0) {
            container.innerHTML = `
                <div class="bg-white rounded-lg border p-12 text-center">
                    <svg class="w-16 h-16 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
                    </svg>
                    <h3 class="text-lg font-medium text-gray-900 mb-2">No Upcoming Interviews</h3>
                    <p class="text-gray-600">Schedule interviews from your applications</p>
                </div>
            `;
            return;
        }
        container.innerHTML = data.interviews.map(i => {
            const interviewDate = new Date(i.interview_date);
            const now = new Date();
            const hoursUntil = Math.floor((interviewDate - now) / (1000 * 60 * 60));
            const daysUntil = Math.floor(hoursUntil / 24);
            const isUrgent = hoursUntil <= 24 && hoursUntil > 0;
            const isPast = hoursUntil < 0;

            // Format time until interview
            let timeUntilText = '';
            let timeUntilColor = 'text-gray-600';
            if (isPast) {
                timeUntilText = 'Past interview';
                timeUntilColor = 'text-gray-400';
            } else if (hoursUntil < 1) {
                timeUntilText = 'Starting soon!';
                timeUntilColor = 'text-red-600 font-semibold';
            } else if (hoursUntil < 24) {
                timeUntilText = `In ${hoursUntil} hour${hoursUntil !== 1 ? 's' : ''}`;
                timeUntilColor = 'text-orange-600 font-semibold';
            } else if (daysUntil === 1) {
                timeUntilText = 'Tomorrow';
                timeUntilColor = 'text-yellow-600 font-medium';
            } else if (daysUntil <= 7) {
                timeUntilText = `In ${daysUntil} days`;
                timeUntilColor = 'text-blue-600';
            } else {
                timeUntilText = `In ${daysUntil} days`;
                timeUntilColor = 'text-gray-600';
            }

            // Get interview type badge
            const typeColors = {
                'phone_screening': 'bg-blue-100 text-blue-700',
                'video_call': 'bg-purple-100 text-purple-700',
                'in_person': 'bg-green-100 text-green-700',
                'technical': 'bg-orange-100 text-orange-700',
                'behavioral': 'bg-pink-100 text-pink-700',
                'panel': 'bg-indigo-100 text-indigo-700'
            };
            const typeColor = typeColors[i.interview_type] || 'bg-gray-100 text-gray-700';

            // Get interview type icon
            const typeIcons = {
                'phone_screening': '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"></path></svg>',
                'video_call': '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"></path></svg>',
                'in_person': '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"></path></svg>',
                'technical': '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"></path></svg>',
                'behavioral': '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"></path></svg>',
                'panel': '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"></path></svg>'
            };
            const typeIcon = typeIcons[i.interview_type] || '';

            const borderClass = isUrgent ? 'border-l-4 border-l-orange-500' : isPast ? 'border-l-4 border-l-gray-300' : 'border-l-4 border-l-blue-500';

            return `
                <div class="bg-white rounded-lg border ${borderClass} p-6 hover:shadow-lg transition-all duration-200 ${isPast ? 'opacity-75' : ''}">
                    <div class="flex justify-between items-start mb-4">
                        <div class="flex-1">
                            <div class="flex items-center gap-2 mb-2">
                                <h3 class="text-xl font-bold text-gray-900">${i.job_title}</h3>
                                ${isUrgent ? '<span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-semibold bg-orange-100 text-orange-700 animate-pulse">Urgent</span>' : ''}
                            </div>
                            <p class="text-gray-700 font-medium text-lg">${i.company_name}</p>
                        </div>
                        <div class="flex flex-col items-end gap-2">
                            <span class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium ${typeColor}">
                                ${typeIcon}
                                ${formatEnumValue(i.interview_type)}
                            </span>
                        </div>
                    </div>
                    
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                        <div class="flex items-center gap-3">
                            <div class="flex-shrink-0 w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                                <svg class="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
                                </svg>
                            </div>
                            <div>
                                <p class="text-xs text-gray-500 font-medium uppercase">Date & Time</p>
                                <p class="text-sm font-semibold text-gray-900">${formatDateTime(i.interview_date)}</p>
                            </div>
                        </div>
                        
                        <div class="flex items-center gap-3">
                            <div class="flex-shrink-0 w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
                                <svg class="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                                </svg>
                            </div>
                            <div>
                                <p class="text-xs text-gray-500 font-medium uppercase">Time Until</p>
                                <p class="text-sm font-semibold ${timeUntilColor}">${timeUntilText}</p>
                            </div>
                        </div>
                    </div>
                    
                    ${i.location ? `
                        <div class="flex items-start gap-3 mb-4 p-3 bg-gray-50 rounded-lg">
                            <svg class="w-5 h-5 text-gray-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path>
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"></path>
                            </svg>
                            <div class="flex-1">
                                <p class="text-xs text-gray-500 font-medium uppercase mb-1">Location</p>
                                <p class="text-sm text-gray-900">${i.location}</p>
                            </div>
                        </div>
                    ` : ''}
                    
                    ${i.notes ? `
                        <div class="mb-4 p-3 bg-blue-50 border border-blue-100 rounded-lg">
                            <p class="text-xs text-blue-600 font-medium uppercase mb-1">Notes</p>
                            <p class="text-sm text-gray-700">${i.notes}</p>
                        </div>
                    ` : ''}
                    
                    <div class="flex flex-wrap gap-2 pt-4 border-t border-gray-100">
                        <button onclick="viewApplicationDetails('${i.application_id || i._id}')" 
                                class="flex-1 min-w-[140px] px-4 py-2.5 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-lg hover:from-blue-700 hover:to-blue-800 transition-all duration-200 font-medium text-sm shadow-sm hover:shadow-md flex items-center justify-center gap-2">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path>
                            </svg>
                            View Details
                        </button>
                        <button onclick="addToCalendar('${i.job_title}', '${i.company_name}', '${i.interview_date}', '${i.location || ''}')" 
                                class="flex-1 min-w-[140px] px-4 py-2.5 bg-white border-2 border-gray-300 text-gray-700 rounded-lg hover:border-gray-400 hover:bg-gray-50 transition-all duration-200 font-medium text-sm flex items-center justify-center gap-2">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
                            </svg>
                            Add to Calendar
                        </button>
                    </div>
                </div>
            `;
        }).join('');
    } catch (error) {
        console.error('Load interviews error:', error);
        container.innerHTML = '<div class="bg-white rounded-lg border p-12 text-center"><p class="text-gray-600">No upcoming interviews</p></div>';
    }
}

async function loadFollowUps() {
    try {
        const res = await fetch(`${API_BASE_URL}/api/v1/applications/follow-ups/needed`, {
            headers: { 'Authorization': `Bearer ${CVision.Utils.getToken()}` }
        });
        if (!res.ok) throw new Error('Failed');
        const data = await res.json();
        const container = document.getElementById('followupsList');
        if (!container) return;

        if (!data.applications || data.applications.length === 0) {
            container.innerHTML = '<div class="bg-white rounded-lg border p-12 text-center"><p class="text-gray-600">No follow-ups needed</p></div>';
            return;
        }
        container.innerHTML = data.applications.map(a => `
            <div class="bg-white rounded-lg border border-yellow-200 border-l-4 p-6">
                <h3 class="text-lg font-semibold">${a.job_title}</h3>
                <p class="text-gray-600">${a.company_name}</p>
                <p class="text-sm text-yellow-600 mt-2">Follow-up due: ${formatDate(a.next_follow_up)}</p>
                <button onclick="viewApplicationDetails('${a._id}')" class="mt-4 px-4 py-2 text-sm bg-primary-600 text-white rounded-lg">View Details</button>
            </div>
        `).join('');
    } catch (error) {
        const container = document.getElementById('followupsList');
        if (container) {
            container.innerHTML = '<div class="bg-white rounded-lg border p-6 text-center"><p class="text-red-600">Failed to load</p></div>';
        }
    }
}

async function loadSavedJobs() {
    try {
        const res = await fetch(`${API_BASE_URL}/api/v1/jobs/saved/me?page=1&size=20`, {
            headers: { 'Authorization': `Bearer ${CVision.Utils.getToken()}` }
        });

        if (!res.ok) throw new Error('Failed');
        const data = await res.json();
        const jobs = data.jobs || data; // Handle both {jobs: [...]} and direct array
        window.currentSavedJobs = jobs; // Store for modal access globally
        const container = document.getElementById('savedJobsList');
        if (!container) return;

        if (!jobs || jobs.length === 0) {
            container.innerHTML = `
                <div class="bg-white rounded-lg border p-12 text-center">
                    <h3 class="text-lg font-medium mb-2">No Saved Jobs</h3>
                    <p class="text-gray-600 mb-6">Save jobs while searching</p>
                    <a href="jobs.html" class="btn-gradient text-white px-6 py-2 rounded-lg inline-block">Search Jobs</a>
                </div>
            `;
            return;
        }
        container.innerHTML = jobs.map(j => `
            <div class="bg-white rounded-xl border border-gray-200 p-6 hover:shadow-lg transition-all duration-300 group relative">
                <button onclick="unsaveJob('${j._id || j.id}')" class="absolute top-4 right-4 text-gray-400 hover:text-red-500 transition-colors p-2 rounded-full hover:bg-red-50" title="Remove from saved">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                    </svg>
                </button>

                <div class="pr-12">
                    <h3 class="text-xl font-bold text-gray-900 group-hover:text-primary-600 transition-colors mb-1">
                        <a href="javascript:void(0)" onclick="showJobDetails('${j._id || j.id}')" class="hover:underline">${j.title}</a>
                    </h3>
                    <div class="flex items-center gap-2 mb-3">
                        <span class="text-gray-700 font-medium">${j.company_name}</span>
                        <span class="text-gray-300">•</span>
                        <span class="text-sm text-gray-500 flex items-center gap-1">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"/></svg>
                            ${j.location}
                        </span>
                    </div>

                    <div class="flex flex-wrap gap-2 mb-4">
                        ${j.employment_type ? `<span class="px-2 py-1 bg-blue-50 text-blue-700 rounded text-xs font-medium">${formatEnumValue(j.employment_type)}</span>` : ''}
                        ${j.salary_range ? `<span class="px-2 py-1 bg-green-50 text-green-700 rounded text-xs font-medium">${j.salary_range.min_amount ? '$' + j.salary_range.min_amount.toLocaleString() : ''} - ${j.salary_range.max_amount ? '$' + j.salary_range.max_amount.toLocaleString() : ''}</span>` : ''}
                        <span class="px-2 py-1 bg-gray-100 text-gray-600 rounded text-xs">Saved ${formatDate(j.saved_at)}</span>
                    </div>

                    <div class="flex items-center justify-between border-t pt-4 mt-4">
                        <div class="w-full">
                            ${window.JobActions ? window.JobActions.getButtonsHTML(j) : ''}
                        </div>
                    </div>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Saved jobs error:', error);
        const container = document.getElementById('savedJobsList');
        if (container) {
            container.innerHTML = '<div class="bg-white rounded-lg border p-6 text-center"><p class="text-red-600">Failed to load saved jobs</p></div>';
        }
    }
}


async function unsaveJob(jobId) {
    if (!confirm('Remove this job?')) return;
    try {
        const res = await fetch(`${API_BASE_URL}/api/v1/jobs/save/${jobId}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${CVision.Utils.getToken()}` }
        });
        if (!res.ok) throw new Error('Failed');
        CVision.Utils.showAlert('Job removed', 'success');
        loadSavedJobs();
    } catch (error) {
        CVision.Utils.showAlert('Failed to remove', 'error');
    }
}

function clearFilters() {
    const statusFilter = document.getElementById('filter-status');
    const priorityFilter = document.getElementById('filter-priority');
    const companyFilter = document.getElementById('filter-company');

    if (statusFilter) statusFilter.value = '';
    if (priorityFilter) priorityFilter.value = '';
    if (companyFilter) companyFilter.value = '';

    loadApplications();
}

function showStatusMenu(appId) {
    updateStatus(appId);
}

function formatEnumValue(value) {
    if (!value) return '';
    return value.replace(/_/g, ' ').split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase()).join(' ');
}

function formatDate(dateString) {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
}

function formatDateTime(dateString) {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleString('en-US', { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
}

// Add interview to calendar
function addToCalendar(jobTitle, companyName, interviewDate, location) {
    try {
        const date = new Date(interviewDate);
        const endDate = new Date(date.getTime() + 60 * 60 * 1000); // 1 hour duration

        // Format dates for .ics file (YYYYMMDDTHHMMSSZ)
        const formatICSDate = (d) => {
            return d.toISOString().replace(/[-:]/g, '').split('.')[0] + 'Z';
        };

        const icsContent = [
            'BEGIN:VCALENDAR',
            'VERSION:2.0',
            'PRODID:-//CVision//Interview Calendar//EN',
            'BEGIN:VEVENT',
            `UID:${Date.now()}@cvision.app`,
            `DTSTAMP:${formatICSDate(new Date())}`,
            `DTSTART:${formatICSDate(date)}`,
            `DTEND:${formatICSDate(endDate)}`,
            `SUMMARY:Interview: ${jobTitle} at ${companyName}`,
            `DESCRIPTION:Interview for ${jobTitle} position at ${companyName}`,
            location ? `LOCATION:${location}` : '',
            'STATUS:CONFIRMED',
            'BEGIN:VALARM',
            'TRIGGER:-PT1H',
            'ACTION:DISPLAY',
            'DESCRIPTION:Interview reminder',
            'END:VALARM',
            'END:VEVENT',
            'END:VCALENDAR'
        ].filter(line => line).join('\r\n');

        // Create and download .ics file
        const blob = new Blob([icsContent], { type: 'text/calendar;charset=utf-8' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = `interview-${companyName.replace(/\s+/g, '-')}.ics`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(link.href);

        InlineMessage.success('Calendar event downloaded! Open the file to add to your calendar.');
    } catch (error) {
        console.error('Calendar error:', error);
        InlineMessage.error('Failed to create calendar event');
    }
}

// Modal event listeners
const applicationModal = document.getElementById('applicationModal');
if (applicationModal) {
    applicationModal.addEventListener('click', (e) => {
        if (e.target.id === 'applicationModal') closeModal();
    });
}

document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeModal();
});

// ==================== EMAIL MONITORING FUNCTIONS ====================
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
async function checkForResponses(applicationId) {
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
        if (data.data.responses_found > 0) {
            InlineMessage.success(data.message);
        } else {
            InlineMessage.info(data.message);
        }
        loadApplications(); // Refresh to show updated check time
        viewApplicationDetails(applicationId); // Refresh the modal // Refresh to show updated check time
    } catch (error) {
        console.error('Check responses error:', error);
        InlineMessage.error(error.message || 'Failed to check responses');
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
// ==================== MODIFIED FUNCTIONS ====================
// REPLACE the existing displayApplications function (around line 321) with this enhanced version:
function displayApplications(applications) {
    const container = document.getElementById('applicationsList');
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
    container.innerHTML = applications.map(app => `
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
                <div class="flex gap-2">
                    ${getSourceBadge(app.source)}
                    ${getMonitoringBadge(app)}
                </div>
            </div>
        </div>
    `).join('');
}
// REPLACE the existing displayApplicationModal function (around line 392) with this enhanced version:
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
                <button onclick="event.stopPropagation(); checkForResponses('${app._id || app.id}')" 
                        class="w-full px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 text-sm">
                    Check for Responses Now
                </button>
            </div>
        </div>
        ` : ''}
        
        <div class="mb-6">
            <h3 class="text-lg font-semibold mb-3">Quick Actions</h3>
            <div class="mb-4">
                ${window.JobActions ? window.JobActions.getButtonsHTML(app.job || app) : ''}
            </div>
            <div class="grid grid-cols-3 gap-3">
                <button onclick="updateStatus('${app._id || app.id}')" class="px-4 py-2 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200">Update Status</button>
                <button onclick="scheduleInterview('${app._id || app.id}')" class="px-4 py-2 bg-purple-100 text-purple-700 rounded-lg hover:bg-purple-200">Schedule Interview</button>
                <button onclick="setFollowUp('${app._id || app.id}')" class="px-4 py-2 bg-green-100 text-green-700 rounded-lg hover:bg-green-200">Set Follow-up</button>
            </div>
        </div>
        
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
}

// ==================== SAVED JOB MODAL FUNCTIONS ====================

// Global variable to store saved jobs for modal access
// Global variable to store saved jobs for modal access
// window.currentSavedJobs is populated in loadSavedJobs

function showJobDetails(jobId) {
    // Fallback if not found (e.g. direct call)
    // Relaxed comparison (==) to handle string/number differences
    const savedJobs = window.currentSavedJobs || [];
    let job = savedJobs.find(j => (j.id || j._id) == jobId);

    if (!job) {
        // If not found in memory (shouldn't happen if clicking from list), try to fetch
        CVision.Utils.showAlert('Job details not loaded', 'error');
        return;
    }

    document.getElementById('jobModalTitle').textContent = job.title;
    document.getElementById('jobModalCompany').textContent = job.company_name;
    document.getElementById('jobModalLocation').textContent = job.location;

    const content = document.getElementById('jobModalContent');
    content.innerHTML = `
        ${job.match_score ? `
            <div class="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
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

        <div class="flex gap-3 flex-wrap mb-6">
            ${job.employment_type ? `<span class="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm">${formatEnumValue(job.employment_type)}</span>` : ''}
            ${job.work_arrangement ? `<span class="px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm">${formatEnumValue(job.work_arrangement)}</span>` : ''}
            ${job.salary_range ? `<span class="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm">${job.salary_range.min_amount ? '$' + job.salary_range.min_amount.toLocaleString() : ''} - ${job.salary_range.max_amount ? '$' + job.salary_range.max_amount.toLocaleString() : ''}</span>` : ''}
        </div>

        <div class="mb-6">
            <h4 class="font-semibold text-lg mb-2">Job Description</h4>
            <div class="text-gray-700 whitespace-pre-line leading-relaxed">${job.description || 'No description available'}</div>
        </div>

        ${job.requirements && job.requirements.length > 0 ? `
            <div class="mb-6">
                <h4 class="font-semibold text-lg mb-2">Requirements</h4>
                <ul class="list-disc list-inside space-y-1 text-gray-700">
                    ${job.requirements.map(req => `<li>${req.requirement || req}</li>`).join('')}
                </ul>
            </div>
        ` : ''}
        
        ${job.generated_cv_path || job.generated_cover_letter_path ? `
            <div class="mb-6 pt-6 border-t border-gray-100">
                <h4 class="font-semibold text-lg mb-3">Generated Documents</h4>
                 ${window.JobActions ? window.JobActions.getButtonsHTML(job, false) : ''}
            </div>
        ` : ''}
    `;

    // Setup actions
    const removeBtn = document.getElementById('jobModalUnsave');
    if (removeBtn) {
        removeBtn.onclick = () => {
            unsaveJob(jobId).then(() => closeJobDetailsModal());
        };
        removeBtn.classList.remove('hidden');
    }

    // Check for applied status
    // Saved jobs might have 'job_id' pointing to the original job, or just '_id' if flattened
    const targetJobId = String(job.job_id || job._id || job.id);
    const isApplied = window.JobActions && window.JobActions.appliedJobIds.has(targetJobId);

    // Wire up Customize button
    const customizeBtn = document.getElementById('jobModalCustomize');
    if (customizeBtn) {
        if (isApplied) {
            customizeBtn.style.display = 'none';
        } else {
            customizeBtn.style.display = 'flex';
            customizeBtn.onclick = () => window.JobActions.openCustomizeModal(job._id || job.id);
        }
    }

    // Wire up Apply button
    const applyBtn = document.getElementById('jobModalApply');
    if (applyBtn) {
        if (isApplied) {
            applyBtn.disabled = true;
            applyBtn.innerHTML = `
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>
                Applied
            `;
            applyBtn.className = 'flex-1 bg-green-50 text-green-700 border border-green-200 rounded-lg px-4 py-2.5 text-sm font-semibold opacity-80 cursor-not-allowed flex items-center justify-center gap-2';
            applyBtn.onclick = null;
            applyBtn.style.display = 'flex';
        } else {
            applyBtn.disabled = false;
            applyBtn.innerHTML = `Apply Now`; // Simplified as icon is likely inside or managed differently in app.js? No, reusing HTML structure is safer.
            applyBtn.innerHTML = `
                 <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
                 Apply Now
            `;
            applyBtn.className = 'flex-1 btn-gradient text-white rounded-lg px-4 py-2.5 text-sm font-semibold hover:shadow-lg transition-all shadow-md flex items-center justify-center gap-2';
            applyBtn.onclick = () => window.JobApply.openApplyModal(job._id || job.id, job);
            applyBtn.style.display = 'flex';
        }
    }

    const modal = document.getElementById('jobDetailsModal');
    modal.classList.remove('hidden');
    modal.classList.add('flex');
}

function closeJobDetailsModal() {
    const modal = document.getElementById('jobDetailsModal');
    modal.classList.add('hidden');
    modal.classList.remove('flex');
}



// ==================== DOCUMENT PREVIEW MODAL FUNCTIONS ====================

// Event listener for job updates from JobActions
document.addEventListener('job:updated', (e) => {
    // If needed, refresh the list
    if (document.getElementById('content-saved') && !document.getElementById('content-saved').classList.contains('hidden')) {
        loadSavedJobs();
    }
});

// Alias for JobActions compatibility
window.applyToJob = (jobId) => window.JobApply.openApplyModal(jobId);

// Ensure JobActions is available
if (!window.JobActions) {
    console.error('JobActions component not loaded');
}

// ==================== SAVE JOB FUNCTION (for generation.js compatibility) ====================

/**
 * Save or update a job with optional extra data (like generated document paths)
 * This is called by generation.js after successful document generation
 */
async function saveJob(jobId, silent = false, extraData = null) {
    try {
        const options = {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${CVision.Utils.getToken()} `
            }
        };

        if (extraData) {
            options.headers['Content-Type'] = 'application/json';
            options.body = JSON.stringify(extraData);
        }

        const response = await fetch(`${API_BASE_URL} /api/v1 / jobs / save / ${jobId} `, options);

        if (!response.ok) throw new Error('Failed to save job');

        if (!silent) {
            CVision.Utils.showAlert('Job saved successfully!', 'success');
        }

        return response.json();
    } catch (error) {
        console.error('Error saving job:', error);
        if (!silent) {
            CVision.Utils.showAlert('Failed to save job', 'error');
        }
        throw error;
    }
}

// Make saveJob available globally for generation.js
window.saveJob = saveJob;
