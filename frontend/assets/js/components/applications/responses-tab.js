window.ResponsesTab = {
    async load() {
        const url = `${API_BASE_URL}/api/v1/applications/?page=1&size=50&has_response=true`;
        try {
            const response = await fetch(url, {
                headers: { 'Authorization': `Bearer ${CVision.Utils.getToken()}` }
            });
            if (!response.ok) throw new Error('Failed');
            const data = await response.json();
            console.log('DEBUG: Received Responses Data:', data);
            const apps = data.applications || [];
            console.log('DEBUG: Filtered Apps Count:', apps.length);

            if (apps.length === 0) {
                console.log('DEBUG loadReceivedResponses: apps.length is 0, showing empty state');
                const container = document.getElementById('responsesList');
                if (container) {
                    container.innerHTML = `
                        <div class="bg-white rounded-lg border p-12 text-center">
                            <svg class="w-12 h-12 mx-auto mb-3 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path></svg>
                            <h3 class="text-lg font-medium mb-2">No Responses Yet</h3>
                            <p class="text-gray-600 mb-6">Emails from recruiters and status updates will appear here automatically.</p>
                             <p class="text-sm text-gray-500">Ensure your applications have a contact email saved.</p>
                        </div>
                    `;
                }
            } else {
                console.log('DEBUG loadReceivedResponses: Calling displayApplications with', apps.length, 'apps for responsesList');
                // Relying on global displayApplications from main file
                displayApplications(apps, 'responsesList');
            }
        } catch (error) {
            console.error('Load responses error:', error);
            const container = document.getElementById('responsesList');
            if (container) {
                container.innerHTML = '<div class="bg-white rounded-lg border p-6 text-center"><p class="text-red-600">Failed to load received responses</p></div>';
            }
        }
    },

    async viewResponseDetails(event, appId) {
        if (event) event.stopPropagation();

        try {
            const [appRes] = await Promise.all([
                fetch(`${API_BASE_URL}/api/v1/applications/${appId}`, { headers: { 'Authorization': `Bearer ${CVision.Utils.getToken()}` } })
            ]);

            if (!appRes.ok) throw new Error('Failed to fetch application details');
            const app = await appRes.json();

            const communications = app.communications || [];
            communications.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));

            const latestResponse = communications.find(c =>
                c.direction === 'inbound' ||
                c.type === 'response' ||
                (c.type === 'email' && c.direction !== 'outbound')
            );

            this.displayResponseModal(app, latestResponse);

        } catch (error) {
            console.error('Response details error:', error);
            CVision.Utils.showAlert('Failed to load response details', 'error');
        }
    },

    displayResponseModal(app, response) {
        const modalContent = document.getElementById('applicationModalContent');
        if (!modalContent) return;

        if (!response) {
            modalContent.innerHTML = `
                <div class="mb-6 text-center">
                    <div class="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-blue-100 mb-4">
                        <svg class="h-6 w-6 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                    </div>
                    <h3 class="text-lg font-medium text-gray-900">Response Status Update</h3>
                    <p class="mt-2 text-sm text-gray-500">
                        The status for <strong>${app.job_title}</strong> at <strong>${app.company_name}</strong> was updated to 
                        <span class="font-medium text-gray-900">${formatEnumValue(app.status)}</span>.
                    </p>
                    <p class="mt-1 text-sm text-gray-500">No specific message content was recorded.</p>
                </div>
                <div class="flex justify-center">
                    <button onclick="closeModal()" class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200">Close</button>
                </div>
            `;
        } else {
            const date = new Date(response.timestamp).toLocaleString();
            modalContent.innerHTML = `
                <div class="flex justify-between items-start mb-6">
                    <div>
                        <h2 class="text-2xl font-bold">Response from ${app.company_name}</h2>
                        <p class="text-gray-600 mt-1">${app.job_title}</p>
                    </div>
                    <button onclick="closeModal()" class="text-gray-400 hover:text-gray-600">
                        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
                    </button>
                </div>
    
                <div class="bg-gray-50 rounded-lg border border-gray-200 overflow-hidden mb-6">
                    <div class="bg-white px-4 py-3 border-b border-gray-200 flex justify-between items-center">
                        <div class="flex items-center gap-2">
                            <div class="bg-blue-100 p-1.5 rounded-full">
                                <svg class="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path></svg>
                            </div>
                            <span class="font-medium text-gray-900">${response.subject || 'No Subject'}</span>
                        </div>
                        <span class="text-sm text-gray-500">${date}</span>
                    </div>
                    <div class="p-6 bg-white min-h-[200px] prose prose-sm max-w-none text-gray-800">
                        ${response.content ? response.content.replace(/\n/g, '<br>') : '<span class="text-gray-400 font-style-italic">No content available</span>'}
                    </div>
                    <div class="bg-gray-50 px-4 py-3 border-t border-gray-200 text-xs text-gray-500 flex justify-between">
                        <span>From: ${response.contact_email || response.contact_person || 'Unknown Sender'}</span>
                        <span>Type: ${formatEnumValue(response.type)}</span>
                    </div>
                </div>
    
                <div class="flex justify-end gap-3">
                    <button onclick="closeModal()" class="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50">Close</button>
                    <button onclick="updateStatus('${app._id || app.id}')" class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">Update Status</button>
                    ${response.contact_email ? `<a href="mailto:${response.contact_email}?subject=Re: ${response.subject || 'Application for ' + app.job_title}" class="px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 flex items-center gap-2"><svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6"></path></svg> Reply</a>` : ''}
                </div>
            `;
        }

        const modal = document.getElementById('applicationModal');
        if (modal) {
            modal.classList.remove('hidden');
        }
    }
};

// Global Exposure
window.loadReceivedResponses = () => window.ResponsesTab.load();
window.viewResponseDetails = (event, appId) => window.ResponsesTab.viewResponseDetails(event, appId);
