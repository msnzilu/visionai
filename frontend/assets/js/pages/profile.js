// Use CONFIG.API_BASE_URL and CONFIG.API_PREFIX for all API calls

document.addEventListener('DOMContentLoaded', function () {
    if (!CVision.Utils.isAuthenticated()) {
        window.location.href = '../login.html';
        return;
    }

    initializeProfile();
});

async function initializeProfile() {
    await loadUserProfile();
    await loadRecentGenerations();
    setupForms();
}

async function loadUserProfile() {
    try {
        // Get user info from /users/me
        const response = await fetch(`${CONFIG.API_BASE_URL}${CONFIG.API_PREFIX}/users/me`, {
            headers: {
                'Authorization': `Bearer ${CVision.Utils.getToken()}`,
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            throw new Error('Failed to load profile');
        }

        const user = await response.json();
        console.log('[DEBUG] User data:', user);

        // Update profile display
        document.getElementById('userName').textContent = user.full_name || user.email.split('@')[0];
        document.getElementById('userEmail').textContent = user.email;
        document.getElementById('userInitial').textContent = (user.full_name || user.email)[0].toUpperCase();
        document.getElementById('subscriptionBadge').textContent =
            user.subscription_tier.charAt(0).toUpperCase() + user.subscription_tier.slice(1);

        // Update basic form fields
        document.getElementById('email').value = user.email;
        document.getElementById('fullName').value = user.full_name || '';

        // Get detailed profile if available
        try {
            const profileResponse = await fetch(`${CONFIG.API_BASE_URL}${CONFIG.API_PREFIX}/users/me/profile`, {
                headers: {
                    'Authorization': `Bearer ${CVision.Utils.getToken()}`,
                    'Content-Type': 'application/json'
                }
            });

            if (profileResponse.ok) {
                const profile = await profileResponse.json();
                console.log('[DEBUG] Profile data:', profile);

                // Update profile fields
                const personalInfo = profile.personal_info || {};
                document.getElementById('phone').value = personalInfo.phone || '';
                document.getElementById('location').value = personalInfo.location || '';
                document.getElementById('linkedin').value = personalInfo.linkedin || '';
            } else {
                console.warn('Detailed profile not available (this is OK)');
            }
        } catch (profileError) {
            console.warn('Could not load detailed profile (this is OK):', profileError);
        }

        // Update usage stats
        if (user.usage_stats) {
            const searches = user.usage_stats.monthly_searches || 0;
            const maxSearches = user.subscription_tier === 'free' ? 1 :
                user.subscription_tier === 'basic' ? 150 : 200;

            document.getElementById('searchesUsed').textContent = `${searches}/${maxSearches}`;
            document.getElementById('searchesBar').style.width = `${(searches / maxSearches) * 100}%`;
            document.getElementById('totalApps').textContent = user.usage_stats.total_applications || 0;
        }

        // Load preferences
        try {
            const prefsResponse = await fetch(`${CONFIG.API_BASE_URL}${CONFIG.API_PREFIX}/users/me/preferences`, {
                headers: {
                    'Authorization': `Bearer ${CVision.Utils.getToken()}`,
                    'Content-Type': 'application/json'
                }
            });

            if (prefsResponse.ok) {
                const preferences = await prefsResponse.json();
                console.log('[DEBUG] Preferences:', preferences);

                document.getElementById('defaultTemplate').value = preferences.default_template || 'professional';
                document.getElementById('defaultTone').value = preferences.default_tone || 'professional';
                document.getElementById('autoGenerateCover').checked = preferences.auto_generate_cover || false;
                document.getElementById('notifyGeneration').checked = preferences.notify_generation || false;
            }
        } catch (prefsError) {
            console.warn('Could not load preferences:', prefsError);
        }

    } catch (error) {
        console.error('Error loading profile:', error);
        CVision.Utils.showAlert('Failed to load profile', 'error');
    }
}

async function loadRecentGenerations() {
    try {
        // TODO: Implement generation history API
        // const history = await CVision.API.request('/generation/history?page=1');
        // if (history && history.documents && history.documents.length > 0) {
        //     displayRecentGenerations(history.documents.slice(0, 5));
        // }
        console.log('[INFO] Generation history not yet implemented');
    } catch (error) {
        console.error('Error loading generations:', error);
    }
}

function displayRecentGenerations(generations) {
    const container = document.getElementById('recentGenerations');

    if (generations.length === 0) return;

    container.innerHTML = generations.map(gen => `
        <div class="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
            <div class="flex items-center justify-between">
                <div class="flex items-center space-x-3">
                    <div class="text-2xl">${gen.type === 'customized_cv' ? '📄' : '✉️'}</div>
                    <div>
                        <h4 class="text-sm font-medium text-gray-900">${gen.job_title || 'Unknown Job'}</h4>
                        <p class="text-xs text-gray-500">${formatDate(gen.generated_at)}</p>
                    </div>
                </div>
                <button onclick="GenerationModule.downloadDocument('${gen._id}', '${gen.type}')" 
                    class="px-3 py-1 text-xs font-medium text-primary-600 bg-primary-100 hover:bg-primary-200 rounded-md transition-colors">
                    Download
                </button>
            </div>
        </div>
    `).join('');
}

function setupForms() {
    // SECTION 1: Personal Information Form (Name + Contact Info)
    document.getElementById('personalInfoForm').addEventListener('submit', async (e) => {
        e.preventDefault();

        const fullName = document.getElementById('fullName').value;
        const phone = document.getElementById('phone').value;
        const location = document.getElementById('location').value;
        const linkedin = document.getElementById('linkedin').value;

        console.log('[PERSONAL INFO] Saving:', { fullName, phone, location, linkedin });

        try {
            // Step 1: Update full_name using existing PUT /me endpoint
            if (fullName) {
                console.log('[PERSONAL INFO] Step 1: Updating name via PUT /me');
                const nameResponse = await fetch(`${CONFIG.API_BASE_URL}${CONFIG.API_PREFIX}/users/me`, {
                    method: 'PUT',
                    headers: {
                        'Authorization': `Bearer ${CVision.Utils.getToken()}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        full_name: fullName
                    })
                });

                if (!nameResponse.ok) {
                    const error = await nameResponse.json();
                    console.error('[PERSONAL INFO] Name update error:', error);
                    throw new Error(error.detail || 'Failed to update name');
                }
                console.log('[PERSONAL INFO] ✓ Name updated');
            }

            // Step 2: Update contact info - get current user data first
            if (phone || location || linkedin) {
                console.log('[PERSONAL INFO] Step 2: Getting current profile data');

                // Get current profile to preserve existing data
                const currentProfileResponse = await fetch(`${CONFIG.API_BASE_URL}${CONFIG.API_PREFIX}/users/me/profile`, {
                    headers: {
                        'Authorization': `Bearer ${CVision.Utils.getToken()}`,
                        'Content-Type': 'application/json'
                    }
                });

                let existingProfile = {};
                if (currentProfileResponse.ok) {
                    existingProfile = await currentProfileResponse.json();
                    console.log('[PERSONAL INFO] Current profile:', existingProfile);
                }

                // Get current user for first_name and last_name
                const userResponse = await fetch(`${CONFIG.API_BASE_URL}${CONFIG.API_PREFIX}/users/me`, {
                    headers: {
                        'Authorization': `Bearer ${CVision.Utils.getToken()}`,
                        'Content-Type': 'application/json'
                    }
                });

                let userData = {};
                if (userResponse.ok) {
                    userData = await userResponse.json();
                }

                console.log('[PERSONAL INFO] Step 3: Updating contact info via PUT /me/profile');

                // Merge with existing profile data and include required fields
                const profileData = {
                    personal_info: {
                        first_name: userData.first_name || '',
                        last_name: userData.last_name || '',
                        phone: phone || existingProfile.personal_info?.phone || '',
                        location: location || existingProfile.personal_info?.location || '',
                        linkedin: linkedin || existingProfile.personal_info?.linkedin || ''
                    }
                };

                console.log('[PERSONAL INFO] Sending profile data:', profileData);

                const profileResponse = await fetch(`${CONFIG.API_BASE_URL}${CONFIG.API_PREFIX}/users/me/profile`, {
                    method: 'PUT',
                    headers: {
                        'Authorization': `Bearer ${CVision.Utils.getToken()}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(profileData)
                });

                if (!profileResponse.ok) {
                    const error = await profileResponse.json();
                    console.error('[PERSONAL INFO] Profile update error:', error);
                    console.error('[PERSONAL INFO] Error details:', JSON.stringify(error, null, 2));

                    // Parse validation errors if they exist
                    if (Array.isArray(error.detail)) {
                        const errorMessages = error.detail.map(err =>
                            `${err.loc ? err.loc.join('.') : 'unknown'}: ${err.msg}`
                        ).join(', ');
                        throw new Error(errorMessages);
                    }

                    throw new Error(error.detail || 'Failed to update contact information');
                }
                console.log('[PERSONAL INFO] ✓ Contact info updated');
            }

            console.log('[PERSONAL INFO] ✓ All fields saved successfully');
            CVision.Utils.showAlert('Personal information updated successfully', 'success');

            // Refresh navbar to show updated name
            if (window.CVisionNavbar && window.CVisionNavbar.refreshUserInfo) {
                await window.CVisionNavbar.refreshUserInfo();
            }

        } catch (error) {
            console.error('[PERSONAL INFO] Error:', error);
            CVision.Utils.showAlert(error.message || 'Failed to update personal information', 'error');
        }
    });

    // SECTION 2: Generation Preferences Form
    document.getElementById('generationPrefsForm').addEventListener('submit', async (e) => {
        e.preventDefault();

        const preferencesData = {
            default_template: document.getElementById('defaultTemplate').value,
            default_tone: document.getElementById('defaultTone').value,
            auto_generate_cover: document.getElementById('autoGenerateCover').checked,
            notify_generation: document.getElementById('notifyGeneration').checked
        };

        console.log('[PREFERENCES] Saving:', preferencesData);

        try {
            const response = await fetch(`${CONFIG.API_BASE_URL}${CONFIG.API_PREFIX}/users/me/preferences`, {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${CVision.Utils.getToken()}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(preferencesData)
            });

            if (!response.ok) {
                const error = await response.json();
                console.error('[PREFERENCES] Error:', error);
                throw new Error(error.detail || 'Failed to save preferences');
            }

            console.log('[PREFERENCES] ✓ Successfully saved');
            CVision.Utils.showAlert('Preferences saved successfully', 'success');

        } catch (error) {
            console.error('[PREFERENCES] Error:', error);
            CVision.Utils.showAlert(error.message || 'Failed to save preferences', 'error');
        }
    });
}

function showChangePassword() {
    CVision.Utils.showAlert('Password change feature coming soon', 'info');
}

function deleteAccount() {
    const confirmed = confirm('Are you sure you want to delete your account? This action cannot be undone.');
    if (confirmed) {
        CVision.Utils.showAlert('Account deletion feature coming soon', 'info');
    }
}

function upgradeAccount() {
    window.location.href = './subscription.html';
}

function logout() {
    CVision.Utils.logout();
}

function formatDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffDays = Math.floor((now - date) / (1000 * 60 * 60 * 24));

    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;

    return date.toLocaleDateString();
}
