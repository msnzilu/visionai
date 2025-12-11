/**
 * Email Analysis Component
 * Reusable component for analyzing emails and displaying results
 */

const EmailAnalysisComponent = {
    /**
     * Initialize the component
     */
    init() {
        console.log('Email Analysis Component initialized');
    },

    /**
     * Render email analysis section in application modal
     * @param {Object} app - Application object
     * @param {string} containerId - ID of container to render into
     */
    renderAnalysisSection(app, containerId = 'emailAnalysisSection') {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`Container #${containerId} not found`);
            return;
        }

        if (!app.email_thread_id) {
            container.innerHTML = '';
            return;
        }

        container.innerHTML = `
            <div class="mb-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
                <h3 class="text-lg font-semibold mb-3 flex items-center gap-2">
                    <svg class="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                    </svg>
                    Email Analysis
                </h3>
                <div class="space-y-3">
                    ${this._renderLastAnalysis(app.last_email_analysis)}
                    ${this._renderAnalyzeButton(app._id || app.id)}
                    ${this._renderAnalysisHistory(app.email_analysis_history)}
                </div>
            </div>
        `;
    },

    /**
     * Render last analysis result
     * @private
     */
    _renderLastAnalysis(lastAnalysis) {
        if (!lastAnalysis) {
            return '<p class="text-sm text-gray-600">No email analysis yet</p>';
        }

        return `
            <div class="bg-white rounded-lg p-3 border border-blue-100">
                <div class="flex items-center justify-between mb-2">
                    <span class="text-sm font-medium text-gray-700">Last Analysis:</span>
                    <span class="px-2 py-1 rounded text-xs font-medium ${this._getCategoryBadgeColor(lastAnalysis.category)}">
                        ${this._formatEnumValue(lastAnalysis.category)}
                    </span>
                </div>
                <div class="flex items-center gap-2 mb-2">
                    <span class="text-xs text-gray-600">Confidence:</span>
                    <div class="flex-1 bg-gray-200 rounded-full h-2">
                        <div class="bg-blue-600 h-2 rounded-full" style="width: ${(lastAnalysis.confidence * 100).toFixed(0)}%"></div>
                    </div>
                    <span class="text-xs font-medium text-gray-700">${(lastAnalysis.confidence * 100).toFixed(0)}%</span>
                </div>
                <div class="text-xs text-gray-500">
                    ${lastAnalysis.ai_used ? '🤖 AI Analysis' : '🔍 Keyword Match'} • 
                    ${this._formatDateTime(lastAnalysis.analyzed_at)}
                </div>
            </div>
        `;
    },

    /**
     * Render analyze button
     * @private
     */
    _renderAnalyzeButton(appId) {
        return `
            <button onclick="EmailAnalysisComponent.analyzeEmail('${appId}')" 
                    class="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm flex items-center justify-center gap-2">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
                </svg>
                Analyze Latest Email
            </button>
        `;
    },

    /**
     * Render analysis history
     * @private
     */
    _renderAnalysisHistory(history) {
        if (!history || history.length === 0) {
            return '';
        }

        return `
            <details class="mt-3">
                <summary class="text-sm font-medium text-blue-700 cursor-pointer hover:text-blue-800">
                    View Analysis History (${history.length})
                </summary>
                <div class="mt-2 space-y-2 max-h-48 overflow-y-auto">
                    ${history.slice(0, 5).map(analysis => `
                        <div class="bg-white rounded p-2 border border-gray-200 text-xs">
                            <div class="flex items-center justify-between mb-1">
                                <span class="px-2 py-0.5 rounded text-xs ${this._getCategoryBadgeColor(analysis.category)}">
                                    ${this._formatEnumValue(analysis.category)}
                                </span>
                                <span class="text-gray-500">${(analysis.confidence * 100).toFixed(0)}%</span>
                            </div>
                            <div class="text-gray-600">${this._formatDateTime(analysis.analyzed_at)}</div>
                        </div>
                    `).join('')}
                </div>
            </details>
        `;
    },

    /**
     * Analyze email for an application
     * @param {string} appId - Application ID
     */
    async analyzeEmail(appId) {
        try {
            if (window.InlineMessage) {
                window.InlineMessage.info('Analyzing latest email...');
            }
            
            const API_BASE_URL = window.CONFIG?.API_BASE_URL || '';
            const token = localStorage.getItem('token');
            
            const response = await fetch(`${API_BASE_URL}/api/v1/email-analysis/applications/${appId}/analyze-latest-email`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to analyze email');
            }
            
            const analysis = await response.json();
            
            // Display analysis result
            this.displayAnalysisResult(analysis, appId);
            
        } catch (error) {
            console.error('Email analysis error:', error);
            if (window.InlineMessage) {
                window.InlineMessage.error(error.message || 'Failed to analyze email');
            } else {
                alert(error.message || 'Failed to analyze email');
            }
        }
    },

    /**
     * Display email analysis result in modal
     * @param {Object} analysis - Analysis result
     * @param {string} appId - Application ID
     */
    displayAnalysisResult(analysis, appId) {
        const categoryLabels = {
            'interview_invitation': 'Interview Invitation',
            'rejection': 'Rejection',
            'offer': 'Job Offer',
            'information_request': 'Information Request',
            'follow_up_required': 'Follow-up Required',
            'acknowledgment': 'Acknowledgment',
            'scheduling_request': 'Scheduling Request',
            'unknown': 'Unknown'
        };
        
        const categoryIcons = {
            'interview_invitation': '📅',
            'rejection': '❌',
            'offer': '🎉',
            'information_request': '📋',
            'follow_up_required': '🔔',
            'acknowledgment': '✅',
            'scheduling_request': '⏰',
            'unknown': '❓'
        };
        
        const confidenceColor = analysis.confidence >= 0.9 ? 'text-green-600' : 
                               analysis.confidence >= 0.7 ? 'text-blue-600' : 
                               'text-yellow-600';
        
        const modalContent = document.getElementById('applicationModalContent');
        if (!modalContent) return;
        
        modalContent.innerHTML = `
            <div class="mb-6">
                <div class="flex justify-between items-start mb-4">
                    <h2 class="text-2xl font-bold">Email Analysis Result</h2>
                    <button onclick="EmailAnalysisComponent.closeModal()" class="text-gray-400 hover:text-gray-600">
                        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                        </svg>
                    </button>
                </div>
                
                <div class="bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg p-6 mb-6">
                    <div class="flex items-center gap-3 mb-4">
                        <span class="text-4xl">${categoryIcons[analysis.category] || '📧'}</span>
                        <div>
                            <h3 class="text-xl font-bold text-gray-900">${categoryLabels[analysis.category] || 'Unknown'}</h3>
                            <p class="text-sm text-gray-600">${analysis.ai_used ? '🤖 AI Analysis' : '🔍 Keyword Match'}</p>
                        </div>
                    </div>
                    
                    <div class="mb-4">
                        <div class="flex items-center justify-between mb-2">
                            <span class="text-sm font-medium text-gray-700">Confidence Score</span>
                            <span class="text-lg font-bold ${confidenceColor}">${(analysis.confidence * 100).toFixed(0)}%</span>
                        </div>
                        <div class="w-full bg-gray-200 rounded-full h-3">
                            <div class="${confidenceColor.replace('text-', 'bg-')} h-3 rounded-full transition-all duration-500" 
                                 style="width: ${(analysis.confidence * 100).toFixed(0)}%"></div>
                        </div>
                    </div>
                    
                    ${analysis.ai_reasoning ? `
                    <div class="bg-white rounded-lg p-4 border border-blue-100">
                        <p class="text-sm font-medium text-gray-700 mb-2">AI Reasoning:</p>
                        <p class="text-sm text-gray-600">${analysis.ai_reasoning}</p>
                    </div>
                    ` : ''}
                </div>
                
                ${analysis.suggested_status ? `
                <div class="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
                    <p class="text-sm font-medium text-blue-900 mb-2">Suggested Action:</p>
                    <p class="text-sm text-blue-700">Update status to: <strong>${this._formatEnumValue(analysis.suggested_status)}</strong></p>
                </div>
                ` : ''}
                
                ${analysis.keywords_matched && analysis.keywords_matched.length > 0 ? `
                <div class="mb-4">
                    <p class="text-sm font-medium text-gray-700 mb-2">Keywords Matched:</p>
                    <div class="flex flex-wrap gap-2">
                        ${analysis.keywords_matched.map(kw => `
                            <span class="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs">${kw}</span>
                        `).join('')}
                    </div>
                </div>
                ` : ''}
                
                <div class="flex gap-3 justify-end mt-6">
                    <button onclick="EmailAnalysisComponent.closeModal()" 
                            class="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50">
                        Close
                    </button>
                    <button onclick="EmailAnalysisComponent.reloadApplicationDetails('${appId}')" 
                            class="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                        View Updated Application
                    </button>
                </div>
            </div>
        `;
        
        const modal = document.getElementById('applicationModal');
        if (modal) {
            modal.classList.remove('hidden');
        }
    },

    /**
     * Close modal
     */
    closeModal() {
        const modal = document.getElementById('applicationModal');
        if (modal) {
            modal.classList.add('hidden');
        }
    },

    /**
     * Reload application details
     * @param {string} appId - Application ID
     */
    reloadApplicationDetails(appId) {
        this.closeModal();
        // Call the global viewApplicationDetails function if it exists
        if (typeof window.viewApplicationDetails === 'function') {
            window.viewApplicationDetails(appId);
        }
    },

    /**
     * Get badge color for email category
     * @private
     */
    _getCategoryBadgeColor(category) {
        const colors = {
            'interview_invitation': 'bg-purple-100 text-purple-700',
            'rejection': 'bg-red-100 text-red-700',
            'offer': 'bg-green-100 text-green-700',
            'information_request': 'bg-blue-100 text-blue-700',
            'follow_up_required': 'bg-yellow-100 text-yellow-700',
            'acknowledgment': 'bg-gray-100 text-gray-700',
            'scheduling_request': 'bg-orange-100 text-orange-700',
            'unknown': 'bg-gray-100 text-gray-500'
        };
        return colors[category] || colors.unknown;
    },

    /**
     * Format enum value for display
     * @private
     */
    _formatEnumValue(value) {
        if (!value) return '';
        return value.split('_').map(word => 
            word.charAt(0).toUpperCase() + word.slice(1).toLowerCase()
        ).join(' ');
    },

    /**
     * Format datetime for display
     * @private
     */
    _formatDateTime(dateString) {
        if (!dateString) return '';
        const date = new Date(dateString);
        return date.toLocaleString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }
};

// Make component available globally
window.EmailAnalysisComponent = EmailAnalysisComponent;

// Auto-initialize on DOM load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => EmailAnalysisComponent.init());
} else {
    EmailAnalysisComponent.init();
}
