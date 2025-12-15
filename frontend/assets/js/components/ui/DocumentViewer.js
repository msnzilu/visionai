/**
 * DocumentViewer Component
 * Reusable component for viewing generated documents (CVs, Cover Letters)
 * Handles modal injection and preview logic.
 */
class DocumentViewerComponent {
    constructor() {
        this.modalId = 'docPreviewModal';
        this.frameId = 'docPreviewFrame';
        this.initialized = false;

        // Bind methods
        this.openPreview = this.openPreview.bind(this);
        this.closePreview = this.closePreview.bind(this);
    }

    init() {
        if (this.initialized) return;
        this.injectModal();
        this.initialized = true;
        console.log('DocumentViewer initialized');
    }

    injectModal() {
        if (document.getElementById(this.modalId)) return;

        const modalHTML = `
            <div id="${this.modalId}" class="hidden fixed inset-0 bg-black bg-opacity-75 z-[70] flex items-center justify-center p-4">
                <div class="bg-white rounded-xl shadow-2xl w-full max-w-5xl h-[85vh] flex flex-col">
                    <div class="px-6 py-4 border-b border-gray-100 flex justify-between items-center">
                        <h3 class="text-xl font-bold text-gray-900" id="docPreviewTitle">Document Preview</h3>
                        <button onclick="DocumentViewer.closePreview()" class="text-gray-400 hover:text-gray-600 p-2 rounded-full hover:bg-gray-100 transition-colors">
                            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
                        </button>
                    </div>
                    <div class="flex-1 bg-gray-100 relative">
                        <iframe id="${this.frameId}" class="w-full h-full border-none" src=""></iframe>
                        <div id="docPreviewLoader" class="absolute inset-0 flex items-center justify-center bg-white z-10 hidden">
                            <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
                        </div>
                    </div>
                </div>
            </div>`;
        document.body.insertAdjacentHTML('beforeend', modalHTML);
    }

    _resolveUrl(path) {
        if (!path) return '';
        if (path.startsWith('http')) return path;

        let baseUrl = window.location.origin;
        if (typeof CONFIG !== 'undefined' && CONFIG.API_BASE_URL) {
            baseUrl = CONFIG.API_BASE_URL;
        } else if (window.CVision && window.CVision.config && window.CVision.config.API_BASE_URL) {
            baseUrl = window.CVision.config.API_BASE_URL;
        } else if (window.CONFIG && window.CONFIG.API_BASE_URL) {
            baseUrl = window.CONFIG.API_BASE_URL;
        }

        const cleanPath = path.startsWith('/') ? path : `/${path}`;
        // Remove double slashes if base url has one and path has one, or ensure one exists
        // Simple robust concatenation:
        return `${baseUrl.replace(/\/+$/, '')}/${cleanPath.replace(/^\/+/, '')}`;
    }

    openPreview(url, title = 'Document Preview') {
        const fullUrl = this._resolveUrl(url);
        const modal = document.getElementById(this.modalId);
        const frame = document.getElementById(this.frameId);
        const titleEl = document.getElementById('docPreviewTitle');
        const loader = document.getElementById('docPreviewLoader');

        if (!modal || !frame) return;

        if (titleEl) titleEl.textContent = title;
        if (loader) loader.classList.remove('hidden');

        frame.src = fullUrl;
        frame.onload = () => {
            if (loader) loader.classList.add('hidden');
        };

        modal.classList.remove('hidden');
        modal.classList.add('flex');
    }

    closePreview() {
        const modal = document.getElementById(this.modalId);
        const frame = document.getElementById(this.frameId);
        if (modal) {
            modal.classList.add('hidden');
            modal.classList.remove('flex');
        }
        if (frame) frame.src = '';
    }

    /**
     * Generates HTML for View CV / View Cover Letter buttons
     * @param {Object} paths - Object containing { cvPath, clPath }
     * @param {Object} styles - Optional style overrides
     */
    renderButtons({ cvPath, clPath }) {
        if (!cvPath && !clPath) return '';

        let html = '<div class="flex gap-2 mb-2">';

        if (cvPath) {
            html += `
                <button onclick="DocumentViewer.openPreview('${cvPath}', 'CV Preview')" 
                    class="flex-1 bg-blue-50 text-blue-700 border border-blue-200 hover:bg-blue-100 rounded-lg px-2 py-1.5 text-xs font-semibold transition-colors flex items-center justify-center gap-1.5">
                    <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/></svg>
                    View CV
                </button>`;
        }

        if (clPath) {
            html += `
                <button onclick="DocumentViewer.openPreview('${clPath}', 'Cover Letter Preview')" 
                    class="flex-1 bg-purple-50 text-purple-700 border border-purple-200 hover:bg-purple-100 rounded-lg px-2 py-1.5 text-xs font-semibold transition-colors flex items-center justify-center gap-1.5">
                    <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/></svg>
                    View CL
                </button>`;
        }

        html += '</div>';
        return html;
    }
}

// Global instance
window.DocumentViewer = new DocumentViewerComponent();

// Auto-init
document.addEventListener('DOMContentLoaded', () => {
    window.DocumentViewer.init();
});
