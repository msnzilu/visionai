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

        // State tracking
        this.lastStatus = '';
        this.hasLoggedInitial = false;
        this.activeStep = 'init';
        this.currentViewStep = 'init';
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
                    <div class="fixed inset-0 bg-gray-900 bg-opacity-60 backdrop-blur-sm transition-opacity" aria-hidden="true" id="rt-overlay"></div>
                    
                    <div class="inline-block align-bottom bg-white rounded-2xl text-left overflow-hidden shadow-2xl transform transition-all sm:my-8 sm:align-middle sm:max-w-4xl sm:w-full border border-gray-100 flex flex-col h-[600px]">
                        
                        <!-- Header -->
                        <div class="bg-white px-6 py-4 border-b border-gray-100 flex justify-between items-center bg-gray-50/50">
                            <div class="flex items-center space-x-3">
                                <div class="flex-shrink-0 h-10 w-10 rounded-xl bg-indigo-600 flex items-center justify-center text-white shadow-lg shadow-indigo-200">
                                    <svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                                    </svg>
                                </div>
                                <div>
                                    <h3 class="text-lg font-bold text-gray-900">Auto-Apply Agent</h3>
                                    <p class="text-xs text-gray-500 font-medium tracking-wide uppercas" id="rt-global-status">Ready to start</p>
                                </div>
                            </div>
                            <div class="flex items-center space-x-2">
                                <button type="button" id="rt-close-btn" class="rounded-lg p-2 text-gray-400 hover:text-gray-500 hover:bg-gray-100 transition-colors">
                                    <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
                                </button>
                            </div>
                        </div>
                        
                        <!-- Linear Progress Bar -->
                        <div class="w-full bg-gray-100 h-1.5">
                            <div id="rt-progress" class="bg-indigo-600 h-1.5 transition-all duration-500 ease-out" style="width: 0%"></div>
                        </div>

                        <!-- Main Content (Columns) -->
                        <div class="flex flex-1 overflow-hidden">
                            <!-- Left: Steps Sidebar -->
                            <div class="w-1/3 bg-gray-50 border-r border-gray-100 overflow-y-auto p-4 space-y-2">
                                ${this.renderStepItem('init', 'Setup & Validation', 'Checking prerequisites...')}
                                ${this.renderStepItem('search', 'Finding Jobs', 'Scanning database for matches')}
                                ${this.renderStepItem('analyze', 'AI Analysis', 'Scoring jobs against your CV')}
                                ${this.renderStepItem('apply', 'Applying', 'Generating custom applications')}
                                ${this.renderStepItem('done', 'Summary', 'Results and final report')}
                            </div>

                            <!-- Right: Details Area -->
                            <div class="w-2/3 bg-white flex flex-col relative">
                                <!-- Logs Container -->
                                <div id="rt-content-area" class="flex-1 overflow-y-auto p-6 custom-scrollbar">
                                    <!-- Step Contents (Toggled via JS) -->
                                    <div id="content-init" class="step-content hidden"></div>
                                    <div id="content-search" class="step-content hidden"></div>
                                    <div id="content-analyze" class="step-content hidden"></div>
                                    <div id="content-apply" class="step-content hidden"></div>
                                    <div id="content-done" class="step-content hidden"></div>
                                    
                                    <!-- Empty State for non-started -->
                                    <div id="content-placeholder" class="h-full flex flex-col items-center justify-center text-gray-300">
                                        <svg class="w-16 h-16 mb-4 text-gray-200" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path></svg>
                                        <p>Select a step to view details</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        document.body.insertAdjacentHTML('beforeend', modalHtml);

        document.getElementById('rt-close-btn').addEventListener('click', () => {
            this.hideModal();
        });

        // Add Step Click Listeners
        document.querySelectorAll('.step-trigger').forEach(el => {
            el.addEventListener('click', (e) => {
                const step = e.currentTarget.dataset.step;
                this.activateTab(step);
            });
        });
    }

    renderStepItem(id, title, desc) {
        return `
            <div class="step-trigger group flex items-start space-x-3 p-3 rounded-xl cursor-pointer transition-all hover:bg-white hover:shadow-sm border border-transparent hover:border-gray-200" data-step="${id}" id="step-btn-${id}">
                <div class="flex-shrink-0 mt-0.5">
                     <div class="step-icon w-6 h-6 rounded-full border-2 border-gray-300 flex items-center justify-center text-gray-400 text-[10px] font-bold transition-colors" id="icon-${id}">
                        <div class="w-2 h-2 rounded-full bg-gray-300" id="dot-${id}"></div>
                     </div>
                </div>
                <div class="flex-1 min-w-0">
                    <p class="text-sm font-semibold text-gray-900 flex justify-between">
                        ${title}
                        <span class="step-badge hidden ml-2 bg-gray-100 text-gray-600 py-0.5 px-2 rounded-full text-[10px]" id="badge-${id}">Pending</span>
                    </p>
                    <p class="text-xs text-gray-500 truncate mt-0.5" id="desc-${id}">${desc}</p>
                </div>
            </div>
        `;
    }

    activateTab(stepId) {
        // Hide all contents
        document.querySelectorAll('.step-content').forEach(el => el.classList.add('hidden'));
        document.getElementById('content-placeholder').classList.add('hidden');

        // Show selected
        const content = document.getElementById(`content-${stepId}`);
        if (content) content.classList.remove('hidden');

        // Update active sidebar state
        document.querySelectorAll('.step-trigger').forEach(el => {
            if (el.dataset.step === stepId) {
                el.classList.add('bg-white', 'shadow-md', 'border-indigo-100');
                el.classList.remove('border-transparent');
            } else {
                el.classList.remove('bg-white', 'shadow-md', 'border-indigo-100');
                el.classList.add('border-transparent');
            }
        });

        this.currentViewStep = stepId;
    }

    showModal() {
        const modal = document.getElementById('rt-modal');
        if (modal) {
            modal.classList.remove('hidden');

            // Reset UI
            if (document.getElementById('rt-progress')) {
                document.getElementById('rt-progress').style.width = '0%';
            }
            document.querySelectorAll('.step-content').forEach(el => el.innerHTML = '');
            document.querySelectorAll('.step-icon').forEach(el => {
                el.className = 'step-icon w-6 h-6 rounded-full border-2 border-gray-300 flex items-center justify-center text-gray-400 text-[10px] font-bold transition-colors';
                el.innerHTML = '<div class="w-2 h-2 rounded-full bg-gray-300"></div>';
            });
            document.querySelectorAll('.step-badge').forEach(el => el.classList.add('hidden'));

            // Reset state
            this.lastStatus = '';
            this.hasLoggedInitial = false;
            this.activeStep = 'init';
            this.activateTab('init');

            // Initial log
            this.log('init', 'Initializing test sequence...', 'info');
        }
    }

    hideModal() {
        const modal = document.getElementById('rt-modal');
        if (modal) modal.classList.add('hidden');
    }

    log(stepId, message, type = 'info') {
        const container = document.getElementById(`content-${stepId}`);
        if (!container) return;

        const icons = {
            info: '<span class="text-blue-500">ℹ️</span>',
            success: '<span class="text-green-500">✅</span>',
            error: '<span class="text-red-500">❌</span>',
            neutral: '<span class="text-gray-400">🔹</span>'
        };

        const div = document.createElement('div');
        div.className = 'flex items-start space-x-3 p-3 rounded-lg bg-gray-50 border border-gray-100 mb-2 animate-fade-in-up';
        div.innerHTML = `
            <div class="flex-shrink-0 mt-0.5">${icons[type] || icons.neutral}</div>
            <div class="flex-1 text-sm text-gray-700 leading-relaxed">${message}</div>
        `;

        container.appendChild(div);

        // Auto scroll if visible
        const wrapper = document.getElementById('rt-content-area');
        if (wrapper && this.currentViewStep === stepId) {
            wrapper.scrollTop = wrapper.scrollHeight;
        }
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

        // 1. Check if user has full access via PremiumGuard (Basic/Premium)
        if (typeof PremiumGuard !== 'undefined' && PremiumGuard.hasAccess('RUN_TEST')) {
            return true;
        }

        // 2. Fallback for Free users: Check 1-time usage limit
        const userTier = (user.subscription_tier || 'free').toLowerCase();

        // Paranoid check: if PremiumGuard said no, but tier is basic/premium, weird state, but let's trust PremiumGuard logic principally.
        // Actually PremiumGuard.hasAccess handles the tier check. So if we are here, user is likely Free.

        const hasRunTest = localStorage.getItem(`has_run_test_${user.id || 'anon'}`);
        if (hasRunTest) {
            // Limit reached
            if (typeof PremiumGuard !== 'undefined') {
                PremiumGuard.enforce('RUN_TEST', 'Test Run Limit', 'Free users can run the test simulator once. Upgrade to run unlimited tests.');
            } else if (window.UpgradeModal) {
                UpgradeModal.show('Test Run Limit', 'Upgrade to Premium for unlimited test runs.');
            } else {
                alert('Limit reached: 1 free test run only.');
            }
            return false;
        }

        // Mark as used for next time
        localStorage.setItem(`has_run_test_${user.id || 'anon'}`, 'true');
        return true;
    }

    pollStatus(taskId) {
        let maxStepReached = 0;
        const stepsOrder = ['init', 'search', 'analyze', 'apply', 'done'];

        const pollInterval = setInterval(async () => {
            try {
                const response = await fetch(`${this.apiUrl}/test/status/${taskId}`, {
                    headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` }
                });

                if (response.ok) {
                    const statusData = await response.json();

                    // Calc percent
                    const pct = Math.round((statusData.current / statusData.total) * 100);

                    // Determine Active Step based on Pct
                    let activeIndex = 0;
                    if (pct >= 100) activeIndex = 4;
                    else if (pct >= 40) activeIndex = 3; // Applying
                    else if (pct >= 20) activeIndex = 2; // Analysis
                    else if (pct >= 10) activeIndex = 1; // Searching

                    const activeStepId = stepsOrder[activeIndex];
                    this.activeStep = activeStepId;

                    // Update global status text
                    const globalStatus = document.getElementById('rt-global-status');
                    if (globalStatus) globalStatus.textContent = `${statusData.status} (${pct}%)`;

                    // Mark previous steps as complete
                    if (activeIndex > maxStepReached) {
                        for (let i = maxStepReached; i < activeIndex; i++) {
                            this.markStepComplete(stepsOrder[i]);
                            // Also switch view to new step automatically if user hasn't clicked away
                            // But maybe better to keep user where they are? 
                            // Let's auto-switch for flow
                            this.activateTab(stepsOrder[i + 1]);
                        }
                        maxStepReached = activeIndex;
                    }

                    // Log status changes
                    // We log to the CURRENT active step
                    if (statusData.status && statusData.status !== this.lastStatus) {
                        this.lastStatus = statusData.status;

                        // Don't log generic "Processing..." unless it's the very first one
                        if (statusData.status !== 'Processing...' || !this.hasLoggedInitial) {
                            this.log(activeStepId, statusData.status, 'info');
                            this.hasLoggedInitial = true;
                        }
                    }

                    if (statusData.state === 'SUCCESS' || statusData.state === 'FAILURE') {
                        clearInterval(pollInterval);
                        this.markStepComplete('done');
                        this.activateTab('done');

                        if (statusData.state === 'SUCCESS') {
                            const apps = statusData.applications_sent || 0;
                            if (apps > 0) {
                                this.log('done', `Success! Sent ${apps} applications.`, 'success');
                            } else {
                                this.log('done', 'Completed with 0 applications sent.', 'neutral');
                            }

                            if (statusData.message) {
                                this.log('done', `Server Message: ${statusData.message}`, 'info');
                            }

                            this.onComplete(statusData);
                        } else {
                            this.log('done', `Process Failed: ${statusData.error}`, 'error');
                        }

                        document.getElementById('rt-close-btn').disabled = false;
                        document.getElementById('rt-global-status').textContent = 'Test Run Completed';
                    }
                }
            } catch (error) {
                console.error('Polling error', error);
            }
        }, 1500);
    }

    markStepComplete(stepId) {
        const iconContainer = document.getElementById(`icon-${stepId}`);
        if (iconContainer) {
            iconContainer.className = 'step-icon w-6 h-6 rounded-full bg-green-500 border-2 border-green-500 flex items-center justify-center text-white text-[10px] font-bold transition-all';
            iconContainer.innerHTML = '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>';
        }

        const badge = document.getElementById(`badge-${stepId}`);
        if (badge) {
            badge.classList.remove('hidden', 'bg-gray-100', 'text-gray-600');
            badge.classList.add('bg-green-100', 'text-green-600');
            badge.textContent = 'Done';
        }
    }

    finishModalState(success) {
        // Deprecated in new design, logic handled in pollStatus
    }
}

window.RunTestButton = RunTestButton;
