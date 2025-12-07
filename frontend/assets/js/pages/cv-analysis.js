const API_BASE_URL = `${CONFIG.API_BASE_URL}`;
let cvData = null;

document.addEventListener('DOMContentLoaded', function () {
    if (!CVision.Utils.isAuthenticated()) {
        window.location.href = '../login.html';
        return;
    }

    initializeCVAnalysis();
});

async function initializeCVAnalysis() {
    await loadCVAnalysis();
    await loadAutomationStatus();
}

// Load CV analysis
async function loadCVAnalysis() {
    try {
        // Fetch CV documents from documents API
        const response = await fetch(`${API_BASE_URL}/api/v1/documents/`, {
            headers: {
                'Authorization': `Bearer ${CVision.Utils.getToken()}`
            }
        });

        // Redirect to login on auth failures or backend errors
        if (!response.ok) {
            if (response.status === 401 || response.status === 502 || response.status === 503) {
                console.error('Authentication or backend error, redirecting to login...');
                CVision.Utils.removeToken();
                window.location.href = '../login.html';
                return;
            }
        }

        const data = await response.json();

        // Get the most recent CV document
        if (!data.documents || data.documents.length === 0) {
            showEmptyState();
            return;
        }

        // Get the first (most recent) document
        const cvDocument = data.documents[0];
        cvData = cvDocument.cv_data;

        if (!cvData || Object.keys(cvData).length === 0) {
            showEmptyState();
            return;
        }

        // Fetch user info for personal details
        const userResponse = await fetch(`${API_BASE_URL}/api/v1/users/me`, {
            headers: {
                'Authorization': `Bearer ${CVision.Utils.getToken()}`
            }
        });

        const userData = await userResponse.json();

        // Load all sections
        loadPersonalInfo(userData, cvData);
        loadProfessionalSummary(cvData);
        loadSkills(cvData);
        loadExperience(cvData);
        loadRecommendedRoles(cvData);
        updateStats(cvData);

    } catch (error) {
        console.error('Error loading CV analysis:', error);
        // If it's a network error or JSON parse error, likely backend is down
        if (error instanceof SyntaxError || error.message.includes('fetch')) {
            console.error('Backend appears to be down, redirecting to login...');
            CVision.Utils.removeToken();
            window.location.href = '../login.html';
            return;
        }
        showError();
    }
}

// Load personal information
function loadPersonalInfo(userData, cvData) {
    // Extract personal info from CV data
    const personalInfo = cvData.personal_info || {};

    const html = `
        <div class="data-row">
            <span class="data-label">Full Name</span>
            <span class="data-value">${userData.full_name || personalInfo.name || 'Not provided'}</span>
        </div>
        <div class="data-row">
            <span class="data-label">Email</span>
            <span class="data-value">${userData.email || personalInfo.email || 'Not provided'}</span>
        </div>
        <div class="data-row">
            <span class="data-label">Phone</span>
            <span class="data-value">${personalInfo.phone || 'Not provided'}</span>
        </div>
        <div class="data-row">
            <span class="data-label">Location</span>
            <span class="data-value">${personalInfo.location || 'Not provided'}</span>
        </div>
        <div class="data-row">
            <span class="data-label">Experience</span>
            <span class="data-value">${cvData.experience ? cvData.experience.length : 0} roles</span>
        </div>
        <div class="data-row">
            <span class="data-label">Education</span>
            <span class="data-value">${cvData.education && cvData.education.length > 0 ? cvData.education[0].degree : 'Not provided'}</span>
        </div>
    `;
    document.getElementById('personalInfo').innerHTML = html;
}

// Load professional summary
function loadProfessionalSummary(cvData) {
    const summary = cvData.summary || cvData.professional_summary ||
        'No professional summary available. Upload your CV to get AI-generated insights.';

    // Split into sentences (handle multiple sentence endings)
    let sentences = summary.match(/[^.!?]+[.!?]+/g);

    // Fallback: if no proper sentences detected, split by character chunks
    if (!sentences || sentences.length <= 1) {
        const words = summary.split(' ');
        sentences = [];
        let chunk = '';
        for (const word of words) {
            chunk += word + ' ';
            if (chunk.length >= 150) {
                sentences.push(chunk.trim());
                chunk = '';
            }
        }
        if (chunk.trim()) sentences.push(chunk.trim());
    }

    const maxInitialSentences = 5;
    const hasMore = summary.length > 200;

    if (hasMore) {
        const initialText = summary.substring(0, 200).trim() + '...';;
        const remainingText = summary.substring(200).trim();

        const html = `
            <p id="summaryInitial" style="color: #4b5563; line-height: 1.8;">${initialText}</p>
            <p id="summaryMore" style="color: #4b5563; line-height: 1.8; display: none; margin-top: 0.5rem;">${remainingText}</p>
            <div onclick="toggleSummary()" id="summaryToggleBtn" style="color: #667eea; cursor: pointer; margin-top: 0.75rem; font-size: 0.875rem; display: inline-flex; align-items: center; gap: 0.25rem;">
                <span>Show More</span> <span id="summaryArrow">▼</span>
            </div>
        `;
        document.getElementById('professionalSummary').innerHTML = html;
    } else {
        document.getElementById('professionalSummary').innerHTML = `
            <p style="color: #4b5563; line-height: 1.8;">${summary}</p>
        `;
    }
}

// Toggle summary visibility
function toggleSummary() {
    const moreSection = document.getElementById('summaryMore');
    const btn = document.getElementById('summaryToggleBtn');

    if (moreSection.style.display === 'none') {
        moreSection.style.display = 'block';
        btn.textContent = 'Show Less';
    } else {
        moreSection.style.display = 'none';
        btn.textContent = 'Show More';
    }
}

// Load skills
function loadSkills(cvData) {
    let skillsArray = [];
    const skillsData = cvData.skills || [];

    // Handle both array and object formats
    if (Array.isArray(skillsData)) {
        skillsArray = skillsData;
    } else if (typeof skillsData === 'object') {
        // Flatten categorized skills (technical, soft, languages)
        if (skillsData.technical) skillsArray.push(...skillsData.technical);
        if (skillsData.soft) skillsArray.push(...skillsData.soft);
        if (skillsData.languages) skillsArray.push(...skillsData.languages);
    }

    if (skillsArray.length === 0) {
        document.getElementById('skillsSection').innerHTML = `
            <p style="color: #6b7280;">No skills found in CV.</p>
        `;
        return;
    }

    const maxInitialSkills = 5;
    const hasMore = skillsArray.length > maxInitialSkills;
    const initialSkills = hasMore ? skillsArray.slice(0, maxInitialSkills) : skillsArray;
    const remainingSkills = hasMore ? skillsArray.slice(maxInitialSkills) : [];

    const html = `
        <div class="skills-grid" id="skillsGridInitial">
            ${initialSkills.map(skill => `
                <div class="skill-badge">${skill}</div>
            `).join('')}
        </div>
        ${hasMore ? `
            <div class="skills-grid" id="skillsGridMore" style="display: none; margin-top: 0.75rem;">
                ${remainingSkills.map(skill => `
                    <div class="skill-badge">${skill}</div>
                `).join('')}
            </div>
            <div onclick="toggleSkills()" id="skillsToggleBtn" style="color: #667eea; cursor: pointer; margin-top: 0.75rem; font-size: 0.875rem; display: inline-flex; align-items: center; gap: 0.25rem;">
                <span>Show ${remainingSkills.length} More Skills</span> <span id="skillsArrow">▼</span>
            </div>
        ` : ''}
    `;
    document.getElementById('skillsSection').innerHTML = html;
}

// Toggle skills visibility
function toggleSkills() {
    const moreSection = document.getElementById('skillsGridMore');
    const btn = document.getElementById('skillsToggleBtn');

    if (moreSection.style.display === 'none') {
        moreSection.style.display = 'grid';
        btn.textContent = 'Show Less';
    } else {
        moreSection.style.display = 'none';
        const hiddenCount = moreSection.querySelectorAll('.skill-badge').length;
        btn.textContent = `Show ${hiddenCount} More Skills`;
    }
}

// Load experience
function loadExperience(cvData) {
    const experience = cvData.experience || [];

    if (experience.length === 0) {
        document.getElementById('experienceSection').innerHTML = `
            <p style="color: #6b7280;">No work experience found in CV.</p>
        `;
        return;
    }

    const maxInitialExp = 5;
    const hasMore = experience.length > maxInitialExp;
    const initialExp = hasMore ? experience.slice(0, maxInitialExp) : experience;
    const remainingExp = hasMore ? experience.slice(maxInitialExp) : [];

    const renderExperience = (exp, index) => {
        // Get description from achievements array or description field
        let fullDescription = '';
        if (exp.achievements && Array.isArray(exp.achievements) && exp.achievements.length > 0) {
            fullDescription = '<ul style="margin: 0.5rem 0; padding-left: 1.5rem;">' +
                exp.achievements.map(achievement => `<li>${achievement}</li>`).join('') +
                '</ul>';
        } else {
            fullDescription = exp.description || '';
        }

        // Truncate description to 200 characters
        const maxChars = 200;
        const hasMoreDesc = fullDescription.length > maxChars;

        let descriptionHtml = '';
        if (hasMoreDesc) {
            const shortDesc = fullDescription.substring(0, maxChars).trim() + '...';
            const remainingDesc = fullDescription.substring(maxChars).trim();
            descriptionHtml = `
                <div class="experience-description">
                    <span id="expDesc${index}">${shortDesc}</span>
                    <span id="expDescMore${index}" style="display: none;">${remainingDesc}</span>
                    <div onclick="toggleExpDesc(${index})" id="expDescBtn${index}" style="color: #667eea; cursor: pointer; margin-top: 0.5rem; font-size: 0.875rem; display: inline-flex; align-items: center; gap: 0.25rem;">
                        <span>Show More</span> <span id="expDescArrow${index}">▼</span>
                    </div>
                </div>
            `;
        } else {
            descriptionHtml = `<div class="experience-description">${fullDescription}</div>`;
        }

        return `
            <div class="experience-item">
                <div class="experience-title">${exp.title || 'Position'}</div>
                <div class="experience-company">${exp.company || 'Company'}</div>
                <div class="experience-duration">
                    ${exp.start_date || 'Start'} - ${exp.end_date || 'Present'}
                    ${exp.duration ? `(${exp.duration})` : ''}
                </div>
                ${descriptionHtml}
            </div>
        `;
    };

    const html = `
        <div id="experienceInitial">
            ${initialExp.map((exp, idx) => renderExperience(exp, idx)).join('')}
        </div>
        ${hasMore ? `
            <div id="experienceMore" style="display: none;">
                ${remainingExp.map((exp, idx) => renderExperience(exp, initialExp.length + idx)).join('')}
            </div>
            <div onclick="toggleExperience()" id="experienceToggleBtn" style="color: #667eea; cursor: pointer; margin-top: 0.75rem; font-size: 0.875rem; display: inline-flex; align-items: center; gap: 0.25rem;">
                <span>Show ${remainingExp.length} More ${remainingExp.length === 1 ? 'Role' : 'Roles'}</span> <span id="experienceArrow">▼</span>
            </div>
        ` : ''}
    `;

    document.getElementById('experienceSection').innerHTML = html;
}

// Toggle individual experience description
function toggleExpDesc(index) {
    const moreSection = document.getElementById(`expDescMore${index}`);
    const btn = document.getElementById(`expDescBtn${index}`);

    if (moreSection.style.display === 'none') {
        moreSection.style.display = 'inline';
        btn.textContent = 'Show Less';
    } else {
        moreSection.style.display = 'none';
        btn.textContent = 'Show More';
    }
}

// Toggle experience visibility
function toggleExperience() {
    const moreSection = document.getElementById('experienceMore');
    const btn = document.getElementById('experienceToggleBtn');

    if (moreSection.style.display === 'none') {
        moreSection.style.display = 'block';
        btn.textContent = 'Show Less';
    } else {
        moreSection.style.display = 'none';
        const hiddenCount = moreSection.querySelectorAll('.experience-item').length;
        btn.textContent = `Show ${hiddenCount} More ${hiddenCount === 1 ? 'Role' : 'Roles'}`;
    }
}

// Load recommended roles
async function loadRecommendedRoles(cvData) {
    const roles = generateRoleRecommendations(cvData);

    if (roles.length === 0) {
        document.getElementById('recommendedRoles').innerHTML = `
            <p style="color: #6b7280; text-align: center;">
                No role recommendations available. Please ensure your CV has detailed skills and experience.
            </p>
        `;
        return;
    }

    const maxInitialRoles = 5;
    const hasMore = roles.length > maxInitialRoles;
    const initialRoles = hasMore ? roles.slice(0, maxInitialRoles) : roles;
    const remainingRoles = hasMore ? roles.slice(maxInitialRoles) : [];

    const renderRole = (role) => {
        const matchClass = role.match >= 80 ? 'match-high' :
            role.match >= 60 ? 'match-medium' : 'match-low';

        return `
            <div class="role-card">
                <div class="role-header">
                    <div class="role-title">${role.title}</div>
                    <div class="match-badge ${matchClass}">${role.match}% Match</div>
                </div>
                <div class="role-description">${role.description}</div>
                <div class="role-requirements">
                    ${role.requirements.map(req => `
                        <span class="requirement-tag ${req.matched ? 'matched' : ''}">${req.skill}</span>
                    `).join('')}
                </div>
                <div style="display: flex; gap: 0.75rem; margin-top: 1rem; flex-wrap: wrap;">
                    <button onclick="event.stopPropagation(); searchRole('${role.title.replace(/'/g, "\\'")}');" style="flex: 1; min-width: 120px; padding: 0.625rem 1rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 0.875rem; font-weight: 500; display: flex; align-items: center; justify-content: center; gap: 0.5rem;">
                        <svg style="width: 1rem; height: 1rem;" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
                        </svg>
                        Search Jobs
                    </button>
                </div>
            </div>
        `;
    };

    const html = `
        <div id="rolesInitial">
            ${initialRoles.map(renderRole).join('')}
        </div>
        ${hasMore ? `
            <div id="rolesMore" style="display: none;">
                ${remainingRoles.map(renderRole).join('')}
            </div>
            <div onclick="toggleRoles()" id="rolesToggleBtn" style="color: #667eea; cursor: pointer; margin-top: 0.75rem; font-size: 0.875rem; display: inline-flex; align-items: center; gap: 0.25rem;">
                <span>Show ${remainingRoles.length} More ${remainingRoles.length === 1 ? 'Role' : 'Roles'}</span> <span id="rolesArrow">▼</span>
            </div>
        ` : ''}
    `;

    document.getElementById('recommendedRoles').innerHTML = html;
}

// Toggle roles visibility
function toggleRoles() {
    const moreSection = document.getElementById('rolesMore');
    const btn = document.getElementById('rolesToggleBtn');

    if (moreSection.style.display === 'none') {
        moreSection.style.display = 'block';
        btn.textContent = 'Show Less';
    } else {
        moreSection.style.display = 'none';
        const hiddenCount = moreSection.querySelectorAll('.role-card').length;
        btn.textContent = `Show ${hiddenCount} More ${hiddenCount === 1 ? 'Role' : 'Roles'}`;
    }
}

// Generate role recommendations based on CV
function generateRoleRecommendations(cvData) {
    // Extract skills from both array and object formats
    let skillsArray = [];
    const skillsData = cvData.skills || [];

    if (Array.isArray(skillsData)) {
        skillsArray = skillsData;
    } else if (typeof skillsData === 'object') {
        if (skillsData.technical) skillsArray.push(...skillsData.technical);
        if (skillsData.soft) skillsArray.push(...skillsData.soft);
        if (skillsData.languages) skillsArray.push(...skillsData.languages);
    }

    const skills = skillsArray.map(s => s.toLowerCase());
    const experience = cvData.experience ? cvData.experience.length : 0;

    const roleTemplates = [
        {
            title: 'Senior Software Engineer',
            description: 'Lead development of complex software systems, mentor junior developers, and drive technical decisions.',
            requiredSkills: ['javascript', 'python', 'java', 'react', 'node.js', 'sql', 'git'],
            minExperience: 5
        },
        {
            title: 'Full Stack Developer',
            description: 'Build and maintain both frontend and backend systems, work with databases, and deploy applications.',
            requiredSkills: ['javascript', 'react', 'node.js', 'mongodb', 'express', 'html', 'css'],
            minExperience: 3
        },
        {
            title: 'Frontend Developer',
            description: 'Create responsive and interactive user interfaces using modern frameworks and best practices.',
            requiredSkills: ['javascript', 'react', 'vue', 'angular', 'html', 'css', 'typescript'],
            minExperience: 2
        },
        {
            title: 'Backend Developer',
            description: 'Design and implement server-side logic, APIs, and database systems.',
            requiredSkills: ['python', 'java', 'node.js', 'sql', 'mongodb', 'api', 'rest'],
            minExperience: 3
        },
        {
            title: 'Data Scientist',
            description: 'Analyze complex data sets, build machine learning models, and derive actionable insights.',
            requiredSkills: ['python', 'machine learning', 'pandas', 'numpy', 'sql', 'statistics', 'tensorflow'],
            minExperience: 2
        },
        {
            title: 'DevOps Engineer',
            description: 'Automate deployment processes, manage infrastructure, and ensure system reliability.',
            requiredSkills: ['docker', 'kubernetes', 'aws', 'jenkins', 'linux', 'python', 'terraform'],
            minExperience: 3
        },
        {
            title: 'Product Manager',
            description: 'Define product strategy, work with stakeholders, and guide product development.',
            requiredSkills: ['product management', 'agile', 'analytics', 'communication', 'strategy'],
            minExperience: 4
        },
        {
            title: 'UI/UX Designer',
            description: 'Design user-centered interfaces, create wireframes, and conduct user research.',
            requiredSkills: ['figma', 'sketch', 'adobe xd', 'user research', 'prototyping', 'design'],
            minExperience: 2
        }
    ];

    const recommendations = roleTemplates.map(role => {
        const matchedSkills = role.requiredSkills.filter(req =>
            skills.some(skill => skill.includes(req) || req.includes(skill))
        );

        const skillMatch = (matchedSkills.length / role.requiredSkills.length) * 100;
        const expMatch = experience >= role.minExperience ? 100 : (experience / role.minExperience) * 100;
        const overallMatch = Math.round((skillMatch * 0.7) + (expMatch * 0.3));

        return {
            title: role.title,
            description: role.description,
            match: overallMatch,
            requirements: role.requiredSkills.map(skill => ({
                skill: skill,
                matched: matchedSkills.includes(skill)
            }))
        };
    });

    return recommendations
        .sort((a, b) => b.match - a.match)
        .slice(0, 5);
}

// Update stats
function updateStats(cvData) {
    // Count skills from both array and object formats
    let skillsCount = 0;
    const skillsData = cvData.skills || [];

    if (Array.isArray(skillsData)) {
        skillsCount = skillsData.length;
    } else if (typeof skillsData === 'object') {
        if (skillsData.technical) skillsCount += skillsData.technical.length;
        if (skillsData.soft) skillsCount += skillsData.soft.length;
        if (skillsData.languages) skillsCount += skillsData.languages.length;
    }

    const experience = cvData.experience ? cvData.experience.length : 0;
    const roles = generateRoleRecommendations(cvData);

    document.getElementById('totalSkills').textContent = skillsCount;
    document.getElementById('yearsExp').textContent = experience;
    document.getElementById('matchingRoles').textContent = roles.length;
    document.getElementById('statsBar').style.display = 'flex';
}

// Search for role with filters
function searchRole(roleTitle) {
    // Build URL with search query
    let url = `/pages/jobs.html?search=${encodeURIComponent(roleTitle)}`;

    // Add common filters based on role type
    // Most tech roles prefer full-time and remote/hybrid options
    const techRoles = ['Software Engineer', 'Developer', 'Data Scientist', 'DevOps Engineer'];
    const isTechRole = techRoles.some(role => roleTitle.includes(role));

    if (isTechRole) {
        // Add employment type filter (full_time)
        url += '&employment_type=full_time';
        // Add work arrangement filter (remote, hybrid)
        url += '&work_arrangement=remote,hybrid';
    }

    // Product Manager and Designer roles
    if (roleTitle.includes('Product Manager') || roleTitle.includes('Designer')) {
        url += '&employment_type=full_time';
        url += '&work_arrangement=remote,hybrid,on_site';
    }

    window.location.href = url;
}


// Handle CV upload from centralized button
async function handleCVUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    // Validate file type
    const allowedTypes = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
    if (!allowedTypes.includes(file.type)) {
        alert('Please upload a PDF or Word document (.pdf, .doc, .docx)');
        return;
    }

    // Validate file size (10MB max)
    if (file.size > 10 * 1024 * 1024) {
        alert('File size must be less than 10MB');
        return;
    }

    try {
        // Show loading state
        const uploadBtn = event.target.previousElementSibling;
        const originalText = uploadBtn.innerHTML;
        uploadBtn.innerHTML = '<span>⏳</span> Uploading...';
        uploadBtn.disabled = true;

        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(`${API_BASE_URL}/api/v1/documents/upload`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${CVision.Utils.getToken()}`
            },
            body: formData
        });

        if (!response.ok) {
            throw new Error('Upload failed');
        }

        const data = await response.json();

        // Show success message
        uploadBtn.innerHTML = '<span>✅</span> Upload Successful!';

        // Reload page after 1 second to show new CV data
        setTimeout(() => {
            window.location.reload();
        }, 1000);

    } catch (error) {
        console.error('Error uploading CV:', error);
        alert('Failed to upload CV. Please try again.');

        // Reset button
        const uploadBtn = event.target.previousElementSibling;
        uploadBtn.innerHTML = '<span>📤</span> Upload New CV';
        uploadBtn.disabled = false;
    }

    // Reset file input
    event.target.value = '';
}

// Show empty state
function showEmptyState() {
    const sections = ['personalInfo', 'professionalSummary', 'skillsSection', 'experienceSection', 'recommendedRoles'];
    sections.forEach(id => {
        document.getElementById(id).innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">📄</div>
                <h3>No CV Data Available</h3>
                <p>Please upload your CV from your profile to get AI-powered analysis and job recommendations</p>
            </div>
        `;
    });
}

// Upload CV function
async function uploadCV(input) {
    const file = input.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
        // Show loading state
        const sections = ['personalInfo', 'professionalSummary', 'skillsSection', 'experienceSection', 'recommendedRoles'];
        sections.forEach(id => {
            document.getElementById(id).innerHTML = `
                <div class="loading">
                    <div class="spinner"></div>
                    <p>Analyzing your CV...</p>
                </div>
            `;
        });

        const response = await fetch(`${API_BASE_URL}/api/v1/documents/upload`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${CVision.Utils.getToken()}`
            },
            body: formData
        });

        if (!response.ok) {
            throw new Error('Upload failed');
        }

        // Reload the analysis after successful upload
        await loadCVAnalysis();

    } catch (error) {
        console.error('Error uploading CV:', error);
        alert('Failed to upload CV. Please try again.');
        showEmptyState();
    }
}

// Show error
function showError() {
    const sections = ['personalInfo', 'professionalSummary', 'skillsSection', 'experienceSection', 'recommendedRoles'];
    sections.forEach(id => {
        document.getElementById(id).innerHTML = `
            <p style="color: #ef4444; text-align: center;">Error loading data. Please try again.</p>
        `;
    });
}

// Automation toggle functions
let automationEnabled = false;

async function toggleAutomation() {
    const toggle = document.getElementById('automationToggle');
    const slider = document.getElementById('automationSlider');
    const status = document.getElementById('automationStatus');
    const panel = document.getElementById('automationPanel');
    const badge = document.getElementById('premiumBadge');

    // Check if user has premium
    const userTier = window.currentUser?.subscription_tier || 'free';

    if (userTier === 'free' && !automationEnabled) {
        badge.style.display = 'block';
        showPremiumModal();
        return;
    }

    automationEnabled = !automationEnabled;

    if (automationEnabled) {
        toggle.style.background = '#10b981';
        slider.style.left = '33px';
        status.textContent = 'Automation enabled';
        panel.style.display = 'block';
    } else {
        toggle.style.background = 'rgba(255,255,255,0.3)';
        slider.style.left = '3px';
        status.textContent = 'Click to enable full automation';
        panel.style.display = 'none';
        await disableAutomation();
    }
}

// Show premium modal
function showPremiumModal() {
    const modal = document.getElementById('premiumModal');
    modal.style.display = 'flex';
    modal.style.pointerEvents = 'auto';
}

// Close premium modal
function closePremiumModal() {
    const modal = document.getElementById('premiumModal');
    modal.style.display = 'none';
    modal.style.pointerEvents = 'none';
}

// Upgrade now - redirect to subscription page
function upgradeNow() {
    window.location.href = '/pages/subscription.html';
}


function updateSliderValue(type, value) {
    if (type === 'maxApps') {
        document.getElementById('maxAppsValue').textContent = value;
    } else if (type === 'minScore') {
        document.getElementById('minScoreValue').textContent = value;
    }
}

async function saveAutomationSettings() {
    const maxApps = parseInt(document.getElementById('maxAppsSlider').value);
    const minScore = parseInt(document.getElementById('minScoreSlider').value) / 100;

    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/auto-apply/enable`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${CVision.Utils.getToken()}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                max_daily_applications: maxApps,
                min_match_score: minScore
            })
        });

        if (response.ok) {
            alert(`✅ Automation Enabled!\n\nThe system will now:\n✅ Find matching jobs every 6 hours\n✅ Generate custom CVs and cover letters\n✅ Apply automatically (up to ${maxApps} jobs/day)\n✅ Notify you of all applications\n\nYou can relax while we work for you! 🚀`);
            document.getElementById('automationStatus').textContent = 'Active - Applying to jobs automatically';
        } else {
            const error = await response.json();
            alert('Error: ' + (error.detail || 'Failed to enable automation'));
        }
    } catch (error) {
        console.error('Error saving automation settings:', error);
        alert('Error saving settings. Please try again.');
    }
}

async function disableAutomation() {
    try {
        await fetch(`${API_BASE_URL}/api/v1/auto-apply/disable`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${CVision.Utils.getToken()}`
            }
        });
        alert('Automation disabled. You can re-enable it anytime.');
    } catch (error) {
        console.error('Error disabling automation:', error);
    }
}

async function loadAutomationStatus() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/auto-apply/status`, {
            headers: {
                'Authorization': `Bearer ${CVision.Utils.getToken()}`
            }
        });

        // If endpoint doesn't exist yet (404), silently ignore
        if (!response.ok) {
            if (response.status === 404) {
                console.log('Auto-apply status endpoint not available yet');
                return;
            }
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        automationEnabled = data.enabled;

        if (automationEnabled) {
            const toggle = document.getElementById('automationToggle');
            const slider = document.getElementById('automationSlider');
            const status = document.getElementById('automationStatus');
            const panel = document.getElementById('automationPanel');

            toggle.style.background = '#10b981';
            slider.style.left = '33px';
            status.textContent = 'Active - Applying to jobs automatically';
            panel.style.display = 'block';

            document.getElementById('maxAppsSlider').value = data.max_daily_applications;
            document.getElementById('maxAppsValue').textContent = data.max_daily_applications;
            document.getElementById('minScoreSlider').value = Math.round(data.min_match_score * 100);
            document.getElementById('minScoreValue').textContent = Math.round(data.min_match_score * 100);
        }
    } catch (error) {
        // Silently handle errors - automation status is not critical for page load
        console.log('Could not load automation status:', error.message);
    }
}
