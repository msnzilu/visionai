
/**
 * Load CVs for apply modal
 */
async function loadCVsForApply() {
    try {
        const response = await CVision.API.request('/documents/?document_type=cv');
        const cvSelect = document.getElementById('applyModalCvSelect');

        if (!cvSelect) return;

        if (response.documents && response.documents.length > 0) {
            cvSelect.innerHTML = response.documents.map(doc =>
                `<option value="${doc.id}">${doc.filename}</option>`
            ).join('');
        } else {
            cvSelect.innerHTML = '<option value="">No CVs available - Upload one first</option>';
        }
    } catch (error) {
        console.error('Failed to load CVs:', error);
    }
}

/**
 * Load cover letters for apply modal
 */
async function loadCoverLettersForApply() {
    try {
        const response = await CVision.API.request('/documents/?document_type=cover_letter');
        const clSelect = document.getElementById('applyModalCoverLetterSelect');

        if (!clSelect) return;

        if (response.documents && response.documents.length > 0) {
            clSelect.innerHTML = '<option value="">No cover letter</option>' +
                response.documents.map(doc =>
                    `<option value="${doc.id}">${doc.filename}</option>`
                ).join('');
        }
    } catch (error) {
        console.error('Failed to load cover letters:', error);
    }
}

/**
 * Generate email preview
 */
function generateEmailPreview(job) {
    const emailTo = job.application_email || job.employer_email || 'Not available';
    const subject = `Application for ${job.title} Position`;
    const body = `Dear Hiring Manager,

I am writing to express my interest in the ${job.title} position at ${job.company_name}.

I have attached my CV for your review. I believe my skills and experience make me a strong candidate for this role.

Thank you for considering my application. I look forward to hearing from you.

Best regards`;

    const emailToEl = document.getElementById('emailTo');
    const emailSubjectEl = document.getElementById('emailSubject');
    const emailBodyEl = document.getElementById('emailBody');

    if (emailToEl) emailToEl.textContent = emailTo;
    if (emailSubjectEl) emailSubjectEl.textContent = subject;
    if (emailBodyEl) emailBodyEl.textContent = body;
}

/**
 * Send email application
 */
async function sendEmailApplication() {
    const cvId = document.getElementById('applyModalCvSelect')?.value;
    const coverLetterId = document.getElementById('applyModalCoverLetterSelect')?.value;

    if (!cvId) {
        CVision.Utils.showAlert('Please select a CV', 'warning');
        return;
    }

    const job = currentJobs.find(j => (j._id || j.id) === currentJobIdForApply);
    if (!job) {
        CVision.Utils.showAlert('Job not found', 'error');
        return;
    }

    const btn = document.getElementById('sendApplicationBtn');
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<span class="animate-spin mr-2">⏳</span> Sending...';
    }

    try {
        const response = await CVision.API.request('/applications/email-apply', {
            method: 'POST',
            body: JSON.stringify({
                job_id: job._id || job.id,
                cv_id: cvId,
                cover_letter_id: coverLetterId || null
            })
        });

        CVision.Utils.showAlert('Application sent successfully!', 'success');
        closeApplyModal();

        // Optionally redirect to applications page
        setTimeout(() => {
            window.location.href = '/pages/applications.html';
        }, 1500);

    } catch (error) {
        console.error('Failed to send application:', error);
        CVision.Utils.showAlert(error.message || 'Failed to send application', 'error');

        if (btn) {
            btn.disabled = false;
            btn.innerHTML = '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/></svg> Send Application';
        }
    }
}

/**
 * Connect Gmail account
 */
function connectGmail() {
    window.location.href = `${CONFIG.API_BASE_URL}${CONFIG.API_PREFIX}/auth/gmail/connect`;
}

// Store current job ID for apply
let currentJobIdForApply = null;
