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
            container.innerHTML = '<div class="bg-white rounded-lg border p-12 text-center"><p class="text-gray-600">No upcoming interviews</p></div>';
            return;
        }
        container.innerHTML = data.interviews.map(i => `
            <div class="bg-white rounded-lg border p-6">
                <h3 class="text-lg font-semibold">${i.job_title}</h3>
                <p class="text-gray-600">${i.company_name}</p>
                <p class="text-sm text-gray-500 mt-2">${formatDateTime(i.interview_date)}</p>
                <p class="text-sm text-gray-500">${i.location || 'Location TBD'}</p>
            </div>
        `).join('');
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
            <div class="bg-white rounded-lg border p-6 hover:shadow-md transition">
                <div class="flex justify-between gap-4">
                    <div class="flex-1">
                        <h3 class="text-lg font-semibold">${j.title}</h3>
                        <p class="text-gray-600 mt-1">${j.company_name}</p>
                        <p class="text-gray-500 text-sm mt-1">${j.location}</p>
                    </div>
                    <div class="flex flex-col gap-2">
                        <button onclick="window.location.href='jobs.html?job=${j.id}'" class="px-4 py-2 text-sm text-white bg-primary-600 hover:bg-primary-700 rounded-lg">View</button>
                        <button onclick="unsaveJob('${j.id}')" class="px-4 py-2 text-sm text-red-600 bg-red-100 hover:bg-red-200 rounded-lg">Remove</button>
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
            <div class="grid grid-cols-3 gap-3">
                <button onclick="updateStatus('${app._id || app.id}')" class="px-4 py-2 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200">Update Status</button>
                <button onclick="scheduleInterview('${app._id || app.id}')" class="px-4 py-2 bg-purple-100 text-purple-700 rounded-lg hover:bg-purple-200">Schedule Interview</button>
                <button onclick="setFollowUp('${app._id || app.id}')" class="px-4 py-2 bg-green-100 text-green-700 rounded-lg hover:bg-green-200">Set Follow-up</button>        </div>
        
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
