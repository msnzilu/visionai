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
            document.getElementById(`tab-${tab}`).classList.remove('border-transparent', 'text-gray-500');
            document.getElementById(`tab-${tab}`).classList.add('border-primary-600', 'text-primary-600');
            document.querySelectorAll('.tab-content').forEach(content => content.classList.add('hidden'));
            document.getElementById(`content-${tab}`).classList.remove('hidden');
            
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
                document.getElementById('statsOverview').innerHTML = `
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
                console.error('Load error:', error);
                document.getElementById('applicationsList').innerHTML = '<div class="bg-white rounded-lg border p-6 text-center"><p class="text-red-600">Failed to load applications</p></div>';
            }
        }

        function displayApplications(applications) {
            const container = document.getElementById('applicationsList');
            if (!applications || applications.length === 0) {
                container.innerHTML = `
                    <div class="bg-white rounded-lg border p-12 text-center">
                        <h3 class="text-lg font-medium text-gray-900 mb-2">No Applications Yet</h3>
                        <p class="text-gray-600 mb-6">Start applying to jobs to track them here</p>
                        <a href="jobs.html" class="btn-gradient text-white px-6 py-2 rounded-lg inline-block">Search for Jobs</a>
                    </div>
                `;
                return;
            }
            container.innerHTML = applications.map(app => `
                <div class="bg-white rounded-lg border p-6 hover:shadow-md transition">
                    <div class="flex justify-between gap-4">
                        <div class="flex-1">
                            <div class="flex items-start gap-3 mb-2">
                                <h3 class="text-lg font-semibold">${app.job_title || 'Unknown'}</h3>
                                ${getStatusBadge(app.status)}
                            </div>
                            <p class="text-gray-600">${app.company_name || 'Unknown'}</p>
                            <p class="text-gray-500 text-sm mt-1">${app.location || 'Location not specified'}</p>
                            <div class="flex gap-2 mt-3">
                                ${getPriorityBadge(app.priority)}
                                ${app.applied_date ? `<span class="px-2 py-1 bg-gray-100 text-gray-600 rounded text-xs">Applied: ${formatDate(app.applied_date)}</span>` : ''}
                            </div>
                        </div>
                        <div class="flex flex-col gap-2">
                            <button onclick="viewApplicationDetails('${app.id}')" class="px-4 py-2 text-sm text-white bg-primary-600 hover:bg-primary-700 rounded-lg">View Details</button>
                            <button onclick="showStatusMenu('${app.id}')" class="px-4 py-2 text-sm text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg">Update Status</button>
                        </div>
                    </div>
                </div>
            `).join('');
        }

        function getStatusBadge(status) {
            const colors = {
                pending: 'bg-yellow-100 text-yellow-800',
                applied: 'bg-blue-100 text-blue-800',
                screening: 'bg-indigo-100 text-indigo-800',
                interview: 'bg-purple-100 text-purple-800',
                offer: 'bg-green-100 text-green-800',
                accepted: 'bg-green-600 text-white',
                rejected: 'bg-red-100 text-red-800',
                withdrawn: 'bg-gray-100 text-gray-800'
            };
            return `<span class="status-badge ${colors[status] || colors.pending}">${formatEnumValue(status)}</span>`;
        }

        function getPriorityBadge(priority) {
            const colors = { high: 'bg-red-100 text-red-700', medium: 'bg-yellow-100 text-yellow-700', low: 'bg-green-100 text-green-700' };
            return `<span class="px-2 py-1 rounded text-xs font-medium ${colors[priority] || colors.medium}">${formatEnumValue(priority)} Priority</span>`;
        }

        async function viewApplicationDetails(appId) {
            try {
                const [appRes, timelineRes] = await Promise.all([
                    fetch(`${API_BASE_URL}/api/v1/applications/${appId}`, { headers: { 'Authorization': `Bearer ${CVision.Utils.getToken()}` }}),
                    fetch(`${API_BASE_URL}/api/v1/applications/${appId}/timeline`, { headers: { 'Authorization': `Bearer ${CVision.Utils.getToken()}` }})
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
            document.getElementById('applicationModalContent').innerHTML = `
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
                </div>
                <div class="mb-6">
                    <h3 class="text-lg font-semibold mb-3">Quick Actions</h3>
                    <div class="grid grid-cols-3 gap-3">
                        <button onclick="updateStatus('${app.id}')" class="px-4 py-2 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200">Update Status</button>
                        <button onclick="scheduleInterview('${app.id}')" class="px-4 py-2 bg-purple-100 text-purple-700 rounded-lg hover:bg-purple-200">Schedule Interview</button>
                        <button onclick="setFollowUp('${app.id}')" class="px-4 py-2 bg-green-100 text-green-700 rounded-lg hover:bg-green-200">Set Follow-up</button>
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
            document.getElementById('applicationModal').classList.remove('hidden');
        }

        function closeModal() {
            document.getElementById('applicationModal').classList.add('hidden');
        }

        async function updateStatus(appId) {
            const status = prompt('Enter status (pending/applied/screening/interview/offer/accepted/rejected/withdrawn):');
            if (!status) return;
            try {
                const res = await fetch(`${API_BASE_URL}/api/v1/applications/${appId}/status`, {
                    method: 'PUT',
                    headers: { 'Authorization': `Bearer ${CVision.Utils.getToken()}`, 'Content-Type': 'application/json' },
                    body: JSON.stringify({ status, notes: '' })
                });
                if (!res.ok) throw new Error('Failed');
                CVision.Utils.showAlert('Status updated', 'success');
                closeModal();
                loadApplications();
                loadStats();
            } catch (error) {
                CVision.Utils.showAlert('Failed to update', 'error');
            }
        }

        async function scheduleInterview(appId) {
            const dateStr = prompt('Interview date/time (YYYY-MM-DD HH:MM):');
            if (!dateStr) return;
            const type = prompt('Type (phone/video/onsite):', 'phone');
            const location = prompt('Location (optional):');
            try {
                const res = await fetch(`${API_BASE_URL}/api/v1/applications/${appId}/schedule-interview`, {
                    method: 'POST',
                    headers: { 'Authorization': `Bearer ${CVision.Utils.getToken()}`, 'Content-Type': 'application/json' },
                    body: JSON.stringify({ interview_date: new Date(dateStr).toISOString(), interview_type: type || 'phone', location: location || null, notes: '' })
                });
                if (!res.ok) throw new Error('Failed');
                CVision.Utils.showAlert('Interview scheduled', 'success');
                closeModal();
                loadApplications();
            } catch (error) {
                CVision.Utils.showAlert('Failed to schedule', 'error');
            }
        }

        async function setFollowUp(appId) {
            const dateStr = prompt('Follow-up date (YYYY-MM-DD):');
            if (!dateStr) return;
            const notes = prompt('Notes (optional):');
            try {
                const res = await fetch(`${API_BASE_URL}/api/v1/applications/${appId}/set-follow-up`, {
                    method: 'POST',
                    headers: { 'Authorization': `Bearer ${CVision.Utils.getToken()}`, 'Content-Type': 'application/json' },
                    body: JSON.stringify({ follow_up_date: new Date(dateStr).toISOString(), notes: notes || '' })
                });
                if (!res.ok) throw new Error('Failed');
                CVision.Utils.showAlert('Follow-up set', 'success');
                closeModal();
                loadApplications();
            } catch (error) {
                CVision.Utils.showAlert('Failed to set follow-up', 'error');
            }
        }

        async function loadUpcomingInterviews() {
            try {
                const res = await fetch(`${API_BASE_URL}/api/v1/applications/upcoming-interviews?days_ahead=30`, {
                    headers: { 'Authorization': `Bearer ${CVision.Utils.getToken()}` }
                });
                if (!res.ok) throw new Error('Failed');
                const data = await res.json();
                const container = document.getElementById('interviewsList');
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
                document.getElementById('interviewsList').innerHTML = '<div class="bg-white rounded-lg border p-6 text-center"><p class="text-red-600">Failed to load</p></div>';
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
                document.getElementById('followupsList').innerHTML = '<div class="bg-white rounded-lg border p-6 text-center"><p class="text-red-600">Failed to load</p></div>';
            }
        }

        async function loadSavedJobs() {
            try {
                const res = await fetch(`${API_BASE_URL}/api/v1/jobs/saved/me?page=1&size=20`, {
                    headers: { 'Authorization': `Bearer ${CVision.Utils.getToken()}` }
                });
                if (!res.ok) throw new Error('Failed');
                const jobs = await res.json();
                const container = document.getElementById('savedJobsList');
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
                document.getElementById('savedJobsList').innerHTML = '<div class="bg-white rounded-lg border p-6 text-center"><p class="text-red-600">Failed to load</p></div>';
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
            document.getElementById('filter-status').value = '';
            document.getElementById('filter-priority').value = '';
            document.getElementById('filter-company').value = '';
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

        document.getElementById('applicationModal').addEventListener('click', (e) => {
            if (e.target.id === 'applicationModal') closeModal();
        });
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') closeModal();
        });