/**
 * RunTestButton Component
 * Encapsulates the "Run Test" functionality:
 * - Render Button
 * - Render Progress Modal (Self-contained)
 * - API Polling & Logic
 */
class RunTestButton {
    constructor(config) {
        this.containerId = config.containerId;
        this.buttonId = config.buttonId;

        // Optional callbacks for external syncing (e.g. refreshing stats)
        this.onComplete = config.onComplete || (() => { });
        this.apiUrl = config.apiUrl || '/api/v1/auto-apply';

        // UI Configuration
        this.label = config.label || '<span>⚡ Run Test Now</span>';
        this.styleClass = config.styleClass || 'bg-white border-2 border-indigo-100 text-indigo-600 hover:bg-indigo-50 hover:border-indigo-200 px-6 py-3 rounded-xl font-semibold shadow-sm transition-all flex items-center gap-2 transform hover:scale-[1.02]';

        this.generatedBtnId = this.containerId ? `${this.containerId}-btn` : this.buttonId;
    }

    init() {
        if (this.containerId) {
            this.render();
        }
        this.createModal();

        const btn = document.getElementById(this.generatedBtnId);
        if (btn) {
            btn.addEventListener('click', () => this.runTest());
        }
    }

    render() {
        const container = document.getElementById(this.containerId);
        if (container) {
            container.innerHTML = `
                <button id="${this.generatedBtnId}" class="${this.styleClass}">
                    ${this.label}
                </button>
            `;
        }
    }

    createModal() {
        if (document.getElementById('rt-modal')) return;

        const modalHtml = `
            <div id="rt-modal" class="fixed inset-0 z-[60] overflow-y-auto hidden" aria-labelledby="modal-title" role="dialog" aria-modal="true">
                <div class="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:p-0">
                    <!-- Overlay -->
                    <div class="fixed inset-0 bg-gray-900 bg-opacity-60 backdrop-blur-sm transition-opacity" aria-hidden="true" id="rt-overlay"></div>
                    
                    <!-- Modal Panel -->
                    <div class="inline-block align-bottom bg-white rounded-2xl text-left overflow-hidden shadow-2xl transform transition-all sm:my-8 sm:align-middle sm:max-w-md sm:w-full border border-gray-100">
                        
                        <!-- Header -->
                        <div class="bg-gradient-to-r from-indigo-50 to-white px-6 py-5 border-b border-indigo-50">
                            <div class="flex items-center space-x-3">
                                <div class="flex-shrink-0 h-10 w-10 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-600">
                                    <svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                                    </svg>
                                </div>
                                <div>
                                    <h3 class="text-lg leading-6 font-bold text-gray-900" id="modal-title">
                                        Auto-Apply Agent
                                    </h3>
                                    <p class="text-xs text-indigo-500 font-medium tracking-wide uppercase">Running Test Sequence</p>
                                </div>
                            </div>
                        </div>

                        <!-- Content -->
                        <div class="px-6 py-6">
                            <!-- Progress Section -->
                            <div class="mb-6">
                                <div class="flex justify-between items-end mb-2">
                                    <span id="rt-status" class="text-sm font-semibold text-gray-700">Initializing...</span>
                                    <span id="rt-percent" class="text-2xl font-bold text-indigo-600">0%</span>
                                </div>
                                <div class="w-full bg-gray-100 rounded-full h-3 overflow-hidden shadow-inner">
                                    <div id="rt-progress" class="bg-gradient-to-r from-indigo-500 to-indigo-600 h-full rounded-full transition-all duration-500 ease-out relative" style="width: 0%">
                                        <div class="absolute inset-0 bg-white opacity-20 animate-pulse"></div>
                                    </div>
                                </div>
                            </div>

                            <!-- Activity Feed -->
                            <div class="bg-gray-50 rounded-xl border border-gray-100 p-4 h-48 overflow-y-auto custom-scrollbar flex flex-col space-y-2" id="rt-logs">
                                <div class="text-center text-gray-400 text-sm py-4 italic">Waiting for agent to start...</div>
                            </div>
                        </div>

                        <!-- Footer -->
                        <div class="bg-gray-50 px-6 py-4 flex flex-row-reverse border-t border-gray-100">
                            <button type="button" id="rt-close-btn" class="w-full inline-flex justify-center items-center rounded-xl border border-transparent shadow-sm px-5 py-2.5 bg-indigo-600 text-base font-semibold text-white hover:!bg-indigo-700 hover:text-white focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:w-auto sm:text-sm disabled:opacity-50 disabled:grayscale transition-all duration-200">
                                Close Window
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        document.body.insertAdjacentHTML('beforeend', modalHtml);

        document.getElementById('rt-close-btn').addEventListener('click', () => {
            this.hideModal();
        });
    }

    showModal() {
        const modal = document.getElementById('rt-modal');
        const closeBtn = document.getElementById('rt-close-btn');
        if (modal) {
            modal.classList.remove('hidden');
            // Reset UI
            document.getElementById('rt-progress').style.width = '0%';
            document.getElementById('rt-percent').textContent = '0%';
            document.getElementById('rt-status').textContent = 'Starting...';
            document.getElementById('rt-status').className = 'text-sm font-semibold text-gray-700'; // Reset color

            const logs = document.getElementById('rt-logs');
            logs.innerHTML = '';
            this.log('Initializing test sequence...', 'info');

            closeBtn.innerHTML = '<span class="animate-pulse">Running...</span>';
            closeBtn.disabled = true;
        }
    }

    hideModal() {
        const modal = document.getElementById('rt-modal');
        if (modal) modal.classList.add('hidden');
    }

    log(message, type = 'info') {
        const logs = document.getElementById('rt-logs');
        if (!logs) return;

        const icons = {
            info: '<span class="bg-blue-100 text-blue-600 rounded-full p-0.5"><svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg></span>',
            success: '<span class="bg-green-100 text-green-600 rounded-full p-0.5"><svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg></span>',
            error: '<span class="bg-red-100 text-red-600 rounded-full p-0.5"><svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg></span>',
            neutral: '<span class="bg-gray-100 text-gray-500 rounded-full p-0.5"><svg class="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" /></svg></span>'
        };

        const icon = icons[type] || icons.neutral;
        const div = document.createElement('div');
        div.className = 'flex items-start space-x-2 text-sm animate-fade-in-up';
        div.innerHTML = `
            <div class="flex-shrink-0 mt-0.5">${icon}</div>
            <div class="flex-1 text-gray-600 leading-snug">${message}</div>
        `;

        logs.appendChild(div);
        logs.scrollTop = logs.scrollHeight;
    }

    async runTest() {
        const btn = document.getElementById(this.generatedBtnId);

        // Tier Check
        if (!this.checkTierLimit()) return;

        this.showModal();

        try {
            // Trigger API
            const response = await fetch(`${this.apiUrl}/test`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` }
            });

            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.detail || 'Test failed to start');
            }

            const data = await response.json();
            this.pollStatus(data.task_id);

        } catch (error) {
            console.error('Test Run Error:', error);
            this.log(`Error: ${error.message}`, 'error');
            this.finishModalState(false);
        }
    }

    checkTierLimit() {
        const user = (window.CVision && CVision.getUser) ? CVision.getUser() : null;
        if (!user) return true;

        const userTier = (user.subscription_tier || 'free').toLowerCase();
        if (userTier === 'free' || userTier === 'freemium') {
            const hasRunTest = localStorage.getItem(`has_run_test_${user.id || 'anon'}`);
            if (hasRunTest) {
                if (window.UpgradeModal) {
                    UpgradeModal.show('Test Run Limit', 'Upgrade to Premium for unlimited test runs.');
                } else {
                    alert('Limit reached: 1 free test run only.');
                }
                return false;
            }
            localStorage.setItem(`has_run_test_${user.id || 'anon'}`, 'true');
        }
        return true;
    }

    pollStatus(taskId) {
        const pollInterval = setInterval(async () => {
            try {
                const response = await fetch(`${this.apiUrl}/test/status/${taskId}`, {
                    headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` }
                });

                if (response.ok) {
                    const statusData = await response.json();

                    // Update Progress
                    const pct = Math.round((statusData.current / statusData.total) * 100);
                    document.getElementById('rt-progress').style.width = `${pct}%`;
                    document.getElementById('rt-percent').textContent = `${pct}%`;

                    const statusEl = document.getElementById('rt-status');
                    if (statusEl.textContent !== statusData.status) {
                        statusEl.textContent = statusData.status || 'Processing...';
                        // Add log for major status changes if needed, or rely on existing log logic
                    }

                    if (statusData.state === 'SUCCESS' || statusData.state === 'FAILURE') {
                        clearInterval(pollInterval);

                        if (statusData.state === 'SUCCESS') {
                            const apps = statusData.applications_sent || 0;
                            this.log(`Completed successfully! ${apps} applications sent.`, 'success');
                            if (statusData.message) this.log(statusData.message, 'info');

                            this.finishModalState(true);
                            this.onComplete(statusData);
                        } else {
                            this.log(`Failed: ${statusData.error}`, 'error');
                            this.finishModalState(false);
                        }
                    }
                }
            } catch (error) {
                console.error('Polling error', error);
            }
        }, 1500);
    }

    finishModalState(success) {
        const closeBtn = document.getElementById('rt-close-btn');
        const status = document.getElementById('rt-status');

        closeBtn.disabled = false;
        closeBtn.innerHTML = 'Close Window';

        if (success) {
            status.textContent = 'Test Completed';
            status.className = 'text-sm font-bold text-green-600';
        } else {
            status.textContent = 'Test Failed';
            status.className = 'text-sm font-bold text-red-600';
        }
    }
}

window.RunTestButton = RunTestButton;
