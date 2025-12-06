/**
 * Reusable Quick Apply Module
 * Shared between jobs.js and cv-analysis.js
 */

const QuickApply = {
    /**
     * Search for jobs and apply to the first match
     */
    async searchAndApply(roleTitle, cvId, coverLetterId = null, onProgress = null) {
        try {
            // Search for jobs
            if (onProgress) onProgress('Searching jobs...');

            const searchResponse = await fetch(`${CONFIG.API_BASE_URL}/api/v1/jobs/search`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${CVision.Utils.getToken()}`
                },
                body: JSON.stringify({
                    query: roleTitle,
                    location: null,
                    filters: null,
                    page: 1,
                    size: 5,
                    sort_by: 'relevance',
                    sort_order: 'desc'
                })
            });

            if (!searchResponse.ok) {
                throw new Error('Failed to search for jobs');
            }

            const searchData = await searchResponse.json();

            if (!searchData.jobs || searchData.jobs.length === 0) {
                throw new Error(`No jobs found for "${roleTitle}"`);
            }

            const firstJob = searchData.jobs[0];

            // Apply to job
            if (onProgress) onProgress('Sending application...');

            const applyResponse = await fetch(`${CONFIG.API_BASE_URL}/api/v1/email-applications/apply`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${CVision.Utils.getToken()}`
                },
                body: JSON.stringify({
                    job_id: firstJob._id || firstJob.id,
                    cv_id: cvId,
                    cover_letter: coverLetterId || null
                })
            });

            const applyData = await applyResponse.json();

            if (!applyResponse.ok) {
                throw new Error(applyData.detail || 'Failed to submit application');
            }

            return {
                success: true,
                job: firstJob,
                message: `Application sent for ${firstJob.title} at ${firstJob.company_name}!`
            };

        } catch (error) {
            return {
                success: false,
                error: error.message
            };
        }
    },

    /**
     * Load user's CVs and cover letters
     */
    async loadDocuments() {
        try {
            const [cvResponse, clResponse] = await Promise.all([
                fetch(`${CONFIG.API_BASE_URL}/api/v1/documents/?document_type=cv`, {
                    headers: { 'Authorization': `Bearer ${CVision.Utils.getToken()}` }
                }),
                fetch(`${CONFIG.API_BASE_URL}/api/v1/documents/?document_type=cover_letter`, {
                    headers: { 'Authorization': `Bearer ${CVision.Utils.getToken()}` }
                })
            ]);

            const cvData = cvResponse.ok ? await cvResponse.json() : { documents: [] };
            const clData = clResponse.ok ? await clResponse.json() : { documents: [] };

            return {
                cvs: cvData.documents || [],
                coverLetters: clData.documents || []
            };
        } catch (error) {
            console.error('Failed to load documents:', error);
            return { cvs: [], coverLetters: [] };
        }
    }
};

// Make it globally available
window.QuickApply = QuickApply;
