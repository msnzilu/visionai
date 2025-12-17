class GmailConnect {
    constructor(config) {
        this.containerId = config.containerId;
        this.container = document.getElementById(this.containerId);
        this.apiUrl = config.apiUrl || `${CONFIG.API_BASE_URL}`; // CONFIG global assumed
        this.onConnect = config.onConnect || (() => { });
    }

    init() {
        if (!this.container) {
            console.error(`GmailConnect: Container #${this.containerId} not found`);
            return;
        }
        this.renderSkeleton();
        this.checkStatus();
    }

    async checkStatus() {
        try {
            // Use existing user info if available, or fetch
            let user = CVision.Utils.getUser();
            if (!user) {
                const response = await CVision.API.getProfile();
                if (response.success) {
                    user = response.data.user;
                    CVision.Utils.setUser(user);
                }
            }

            if (user && user.gmail_connected) {
                this.renderConnected(user);
            } else {
                this.renderConnect();
            }
        } catch (error) {
            console.error('GmailConnect: Error checking status', error);
            this.renderConnect(); // Fallback
        }
    }

    renderSkeleton() {
        this.container.innerHTML = `
            <div id="gmailAlertSkeleton" class="bg-gray-50 border-l-4 border-gray-200 p-4 mb-4 rounded-r shadow-sm animate-pulse">
                <div class="flex flex-col sm:flex-row items-center gap-4">
                    <div class="flex items-center w-full sm:flex-1">
                        <div class="flex-shrink-0 w-5 h-5 bg-gray-200 rounded-full"></div>
                        <div class="ml-3 w-full">
                            <div class="h-4 bg-gray-200 rounded w-1/3 mb-2"></div>
                            <div class="h-3 bg-gray-200 rounded w-1/4"></div>
                        </div>
                    </div>
                    <div class="flex items-center justify-end gap-3 w-full sm:w-auto mt-3 sm:mt-0">
                        <div class="h-8 w-24 bg-gray-200 rounded"></div>
                        <div class="h-[30px] w-[140px] bg-gray-200 rounded-full"></div>
                    </div>
                </div>
            </div>
        `;
    }

    renderConnect() {
        this.container.innerHTML = `
            <div id="connectGmailAlert" class="bg-blue-50 border-l-4 border-blue-500 p-4 mb-4 rounded-r shadow-sm">
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
                                <button id="btnConnectGmail" class="text-sm font-medium text-blue-600 hover:text-blue-500 bg-white px-3 py-1.5 rounded border border-blue-200 shadow-sm transition-colors">
                                    Connect Gmail
                                </button>
                            </div>
                        </div>
                    </div>
                    <button id="btnDismissGmail" class="text-blue-400 hover:text-blue-500">
                        <span class="sr-only">Dismiss</span>
                        <svg class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                            <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
                        </svg>
                    </button>
                </div>
            </div>
        `;

        // Bind events
        this.container.querySelector('#btnConnectGmail').addEventListener('click', () => this.connect());
        this.container.querySelector('#btnDismissGmail').addEventListener('click', () => {
            this.container.innerHTML = ''; // Or hide class
        });
    }

    renderConnected(user) {
        this.container.innerHTML = `
            <div id="gmailConnectedAlert" class="bg-green-50 border-l-4 border-green-500 p-4 mb-4 rounded-r shadow-sm">
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
                                <p>Tracking: <strong>${user.email || 'your Gmail account'}</strong></p>
                            </div>
                        </div>
                    </div>
                    <div class="flex flex-wrap items-center justify-end gap-3 w-full sm:w-auto mt-3 sm:mt-0">
                        <button id="quickRunTestBtn" class="text-sm font-medium text-green-700 hover:text-green-800 bg-white/50 hover:bg-white/80 border border-green-200 px-3 py-1.5 rounded-md transition-colors flex items-center gap-1.5 whitespace-nowrap">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.384-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
                            </svg>
                            Run Test
                        </button>
                        <div id="dashboardAutoApplyContainer" class="flex items-center justify-end w-[160px]" style="min-height: 30px;">
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Initialize AutoApplyButton
        if (typeof AutoApplyButton !== 'undefined') {
            const autoApplyBtn = new AutoApplyButton({
                containerId: 'dashboardAutoApplyContainer',
                textColor: 'text-gray-800',
                label: 'Auto-Apply',
                onToggle: (isEnabled) => {
                    // Could bubble this up if needed
                }
            });
            autoApplyBtn.init();
        }

        // Initialize Quick RunTestButton
        if (typeof RunTestButton !== 'undefined') {
            const quickTestBtn = new RunTestButton({
                buttonId: 'quickRunTestBtn',
                apiUrl: `${this.apiUrl}/api/v1/auto-apply`,
                onStart: () => {
                    CVision.Utils.showAlert('Test run started in background...', 'info');
                },
                onProgress: (data) => { },
                onComplete: (data) => {
                    if (data.applications_sent > 0) {
                        CVision.Utils.showAlert(`Success! ${data.applications_sent} applications sent.`, 'success');
                    }
                    if (window.loadAutomationStatus) window.loadAutomationStatus();
                },
                onError: (error) => {
                    CVision.Utils.showAlert(`Test Failed: ${error.message}`, 'error');
                }
            });
            quickTestBtn.init();
        }
    }

    async connect() {
        try {
            const response = await fetch(`${this.apiUrl}/api/v1/auth/gmail/connect`, {
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
}
