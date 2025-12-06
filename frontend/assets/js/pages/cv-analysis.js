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
        const response = await fetch(`${API_BASE_URL}/api/v1/users/me`, {
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
        cvData = data.cv_parsed;

        if (!cvData || Object.keys(cvData).length === 0) {
            showEmptyState();
            return;
        }

        // Load all sections
        loadPersonalInfo(data);
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
function loadPersonalInfo(data) {
    const html = `
        <div class="data-row">
            <span class="data-label">Full Name</span>
            <span class="data-value">${data.full_name || 'Not provided'}</span>
        </div>
        <div class="data-row">
            <span class="data-label">Email</span>
            <span class="data-value">${data.email || 'Not provided'}</span>
        </div>
        <div class="data-row">
            <span class="data-label">Phone</span>
            <span class="data-value">${cvData.phone || 'Not provided'}</span>
        </div>
        <div class="data-row">
            <span class="data-label">Location</span>
            <span class="data-value">${cvData.location || 'Not provided'}</span>
        </div>
        <div class="data-row">
            <span class="data-label">Experience</span>
            <span class="data-value">${cvData.years_of_experience || 0} years</span>
        </div>
        <div class="data-row">
            <span class="data-label">Education</span>
            <span class="data-value">${cvData.education_level || 'Not provided'}</span>
        </div>
    `;
    document.getElementById('personalInfo').innerHTML = html;
}

// Load professional summary
function loadProfessionalSummary(cvData) {
    const summary = cvData.summary || cvData.professional_summary ||
        'No professional summary available. Upload your CV to get AI-generated insights.';

    document.getElementById('professionalSummary').innerHTML = `
        <p style="color: #4b5563; line-height: 1.8;">${summary}</p>
    `;
}

// Load skills
function loadSkills(cvData) {
    const skills = cvData.skills || [];

    if (skills.length === 0) {
        document.getElementById('skillsSection').innerHTML = `
            <p style="color: #6b7280;">No skills found in CV. Please upload a detailed CV.</p>
        `;
        return;
    }

    const html = `
        <div class="skills-grid">
            ${skills.map(skill => `
                <div class="skill-badge">${skill}</div>
            `).join('')}
        </div>
    `;
    document.getElementById('skillsSection').innerHTML = html;
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

    const html = experience.map(exp => `
        <div class="experience-item">
            <div class="experience-title">${exp.title || exp.position || 'Position'}</div>
            <div class="experience-company">${exp.company || 'Company'}</div>
            <div class="experience-duration">
                ${exp.start_date || 'Start'} - ${exp.end_date || exp.is_current ? 'Present' : 'End'}
                ${exp.duration ? `(${exp.duration})` : ''}
            </div>
            <div class="experience-description">${exp.description || exp.responsibilities || ''}</div>
        </div>
    `).join('');

    document.getElementById('experienceSection').innerHTML = html;
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

    const html = roles.map(role => {
        const matchClass = role.match >= 80 ? 'match-high' :
            role.match >= 60 ? 'match-medium' : 'match-low';

        return `
            <div class="role-card" onclick="searchRole('${role.title}')">
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
            </div>
        `;
    }).join('');

    document.getElementById('recommendedRoles').innerHTML = html;
}

// Generate role recommendations based on CV
function generateRoleRecommendations(cvData) {
    const skills = (cvData.skills || []).map(s => s.toLowerCase());
    const experience = cvData.years_of_experience || 0;

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
    const skills = cvData.skills || [];
    const experience = cvData.years_of_experience || 0;
    const roles = generateRoleRecommendations(cvData);

    document.getElementById('totalSkills').textContent = skills.length;
    document.getElementById('yearsExp').textContent = experience;
    document.getElementById('matchingRoles').textContent = roles.length;
    document.getElementById('statsBar').style.display = 'flex';
}

// Search for role
function searchRole(roleTitle) {
    window.location.href = `/pages/jobs.html?search=${encodeURIComponent(roleTitle)}`;
}

// Show empty state
function showEmptyState() {
    const sections = ['personalInfo', 'professionalSummary', 'skillsSection', 'experienceSection', 'recommendedRoles'];
    sections.forEach(id => {
        document.getElementById(id).innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">📄</div>
                <h3>No CV Data Available</h3>
                <p>Upload your CV to get AI-powered analysis and job recommendations</p>
                <button class="btn-upload" onclick="window.location.href='/pages/profile.html'">
                    Upload CV
                </button>
            </div>
        `;
    });
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
