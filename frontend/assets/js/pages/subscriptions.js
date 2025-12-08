// frontend/assets/js/subscriptions.js
const API_BASE_URL = `${CONFIG.API_BASE_URL}`;
let PAYSTACK_PUBLIC_KEY = null;
let USER_EMAIL = null;

let selectedPlan = null;
let currentSubscription = null;

// Load Paystack configuration from backend
async function loadPaystackConfig() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/subscriptions/config/paystack`);
        if (response.ok) {
            const config = await response.json();
            PAYSTACK_PUBLIC_KEY = config.public_key;
            USER_EMAIL = config.user_email; // Might be null here, better to get from profile

            if (!PAYSTACK_PUBLIC_KEY) {
                console.error('Paystack public key missing');
            }
        } else {
            console.error('Failed to load Paystack config');
        }
    } catch (error) {
        console.error('Failed to load Paystack config:', error);
    }
}

// Helper function to handle API errors
async function handleApiError(response) {
    if (response.status === 401) {
        CVision.Utils.showAlert('Session expired. Please login again.', 'error');
        setTimeout(() => {
            window.location.href = '../login.html';
        }, 2000);
        return null;
    }

    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'An error occurred' }));
        throw new Error(error.detail || 'Request failed');
    }

    return response;
}

// Helper function to make authenticated requests
async function authenticatedFetch(url, options = {}) {
    const token = CVision.Utils.getToken();

    if (!token) {
        window.location.href = '../login.html';
        return null;
    }

    const headers = {
        'Authorization': `Bearer ${token}`,
        ...options.headers
    };

    const response = await fetch(url, { ...options, headers });
    return handleApiError(response);
}

document.addEventListener('DOMContentLoaded', async () => {
    if (!CVision.Utils.isAuthenticated()) {
        window.location.href = '../login.html';
        return;
    }

    // Load config
    await loadPaystackConfig();

    // Get user email from profile if not in config
    if (!USER_EMAIL) {
        try {
            const user = CVision.Utils.getUser();
            if (user) USER_EMAIL = user.email;
        } catch (e) { console.warn("Could not load user email from local storage"); }
    }

    // Load data
    await Promise.all([
        loadCurrentSubscription(),
        loadPlans(),
        loadReferralStats()
    ]).catch(error => {
        console.error('Failed to load initial data:', error);
    });
});

async function loadCurrentSubscription() {
    try {
        const response = await authenticatedFetch(`${API_BASE_URL}/api/v1/subscriptions/me`);
        console.log(response);

        if (!response) return;


        if (response.ok) {
            currentSubscription = await response.json();
            displayCurrentPlan(currentSubscription);
            await loadUsageStats();
        } else if (response.status === 404) {
            document.getElementById('currentTierName').textContent = 'Free Plan';
            document.getElementById('currentTierStatus').textContent = 'Status: Active';
            document.getElementById('currentUsage').textContent = '0 searches used';
        }
    } catch (error) {
        if (error.message.includes('No subscription found') || error.message.includes('404')) {
            // User has no subscription yet, treat as Free Plan
            console.log('No active subscription found, defaulting to Free Plan');
            document.getElementById('currentTierName').textContent = 'Free Plan';
            document.getElementById('currentTierStatus').textContent = 'Status: Active';
            document.getElementById('currentUsage').textContent = '0 searches used';
            return;
        }
        console.error('Failed to load subscription:', error);
        CVision.Utils.showAlert('Failed to load subscription information', 'warning');
    }
}

function displayCurrentPlan(subscription) {
    const tierName = subscription.plan_id.replace('plan_', '').toUpperCase();
    document.getElementById('currentTierName').textContent = `${tierName} Plan`;
    document.getElementById('currentTierStatus').textContent = `Status: ${subscription.status}`;

    // Show/hide buttons based on plan tier
    const isFree = subscription.plan_id === 'plan_free';
    const isBasic = subscription.plan_id === 'plan_basic';
    const isPremium = subscription.plan_id === 'plan_premium';

    // Get buttons
    const manageBtn = document.getElementById('manageBillingBtn');
    const cancelBtn = document.getElementById('cancelSubscriptionBtn');
    const upgradeBtn = document.getElementById('upgradeBtn');

    if (isFree) {
        // Free tier: Show upgrade button only
        if (manageBtn) manageBtn.style.display = 'none';
        if (cancelBtn) cancelBtn.style.display = 'none';
        if (upgradeBtn) upgradeBtn.style.display = 'inline-block';
    } else {
        // Paid tiers: Show manage and cancel buttons
        // Hide Manage Billing for Paystack as there isn't a direct portal
        if (manageBtn) manageBtn.style.display = 'none';
        if (cancelBtn) cancelBtn.style.display = 'inline-block';

        // Show upgrade only if not on premium
        if (upgradeBtn) {
            upgradeBtn.style.display = isPremium ? 'none' : 'inline-block';
        }
    }
}

function showUpgradeOptions() {
    // Scroll to pricing plans
    const plansSection = document.getElementById('pricingPlans');
    if (plansSection) {
        plansSection.scrollIntoView({ behavior: 'smooth', block: 'start' });

        // Add a highlight effect
        plansSection.classList.add('ring-2', 'ring-blue-500', 'ring-offset-4');
        setTimeout(() => {
            plansSection.classList.remove('ring-2', 'ring-blue-500', 'ring-offset-4');
        }, 2000);
    }
}

async function loadUsageStats() {
    try {
        const response = await authenticatedFetch(`${API_BASE_URL}/api/v1/subscriptions/usage`);

        if (!response || !response.ok) return;

        const data = await response.json();
        const usage = data.current_usage || {};

        const searches = usage.searches || 0;
        const applications = usage.applications || 0;

        document.getElementById('currentUsage').textContent =
            `${searches} searches, ${applications} applications`;

    } catch (error) {
        console.error('Failed to load usage:', error);
    }
}

async function loadPlans() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/subscriptions/plans`);

        if (!response.ok) throw new Error('Failed to load plans');

        const plans = await response.json();
        displayPlans(plans);
    } catch (error) {
        console.error('Failed to load plans:', error);
        CVision.Utils.showAlert('Failed to load subscription plans', 'error');
        displayFallbackPlans();
    }
}

function displayFallbackPlans() {
    const container = document.getElementById('pricingPlans');
    container.innerHTML = `
        <div class="col-span-3 text-center p-8">
            <p class="text-gray-600 mb-4">Unable to load plans at this moment.</p>
            <button onclick="loadPlans()" class="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                Retry
            </button>
        </div>
    `;
}

function displayPlans(plans) {
    const container = document.getElementById('pricingPlans');
    container.innerHTML = '';

    plans.forEach(plan => {
        const isCurrentPlan = currentSubscription &&
            currentSubscription.plan_id === plan.id;

        const card = document.createElement('div');
        card.className = `bg-white rounded-xl shadow-lg border-2 p-8 relative ${plan.is_popular ? 'border-blue-500' : 'border-gray-200'
            }`;

        if (plan.is_popular) {
            card.innerHTML += `
                <div class="absolute top-0 right-0 bg-blue-500 text-white px-4 py-1 rounded-bl-lg rounded-tr-lg text-sm font-semibold">
                    Most Popular
                </div>
            `;
        }

        // Pass plan code (paystack_plan_code) if available
        const planCode = plan.paystack_plan_code || '';

        card.innerHTML += `
            <div class="text-center">
                <h3 class="text-2xl font-bold mb-2">${plan.name}</h3>
                <p class="text-gray-600 mb-6">${plan.description}</p>
                
                <div class="mb-6">
                    <span class="text-4xl font-bold">$${(plan.price.amount / 100).toFixed(0)}</span>
                    <span class="text-gray-600">/month</span>
                </div>
                
                <ul class="text-left space-y-3 mb-8">
                    ${plan.features.map(feature => `
                        <li class="flex items-start">
                            <svg class="w-5 h-5 text-green-500 mr-2 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                                <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"/>
                            </svg>
                            <span class="text-gray-700">${feature}</span>
                        </li>
                    `).join('')}
                </ul>
                
                ${isCurrentPlan ? `
                    <button class="w-full bg-gray-200 text-gray-600 rounded-lg px-6 py-3 font-semibold cursor-not-allowed">
                        Current Plan
                    </button>
                ` : `
                    <button onclick="selectPlan('${plan.id}', '${plan.name}', ${plan.price.amount}, '${planCode}')" 
                        class="w-full ${plan.is_popular ? 'btn-gradient' : 'border-2 border-gray-300 hover:border-blue-500'} 
                        text-white rounded-lg px-6 py-3 font-semibold hover:shadow-lg transition-all">
                        ${plan.tier === 'free' ? 'Get Started' : 'Subscribe Now'}
                    </button>
                `}
            </div>
        `;

        container.appendChild(card);
    });
}

function selectPlan(planId, planName, price, planCode) {
    selectedPlan = { id: planId, name: planName, price: price, planCode: planCode };

    if (planId === 'plan_free') {
        subscribeToPlan(planId, null);
    } else {
        showSubscriptionModal(planName);
    }
}

function showSubscriptionModal(planName) {
    document.getElementById('selectedPlanName').textContent = planName;
    document.getElementById('subscriptionModal').classList.remove('hidden');
    document.getElementById('subscriptionModal').classList.add('flex');

    document.getElementById('payment-form').addEventListener('submit', handlePaymentSubmit);
}

function closeSubscriptionModal() {
    document.getElementById('subscriptionModal').classList.add('hidden');
    document.getElementById('subscriptionModal').classList.remove('flex');
}

async function handlePaymentSubmit(e) {
    e.preventDefault();

    if (!PAYSTACK_PUBLIC_KEY) {
        CVision.Utils.showAlert('Payment configuration error', 'error');
        return;
    }

    const submitButton = document.getElementById('submit-payment');
    submitButton.disabled = true;
    submitButton.textContent = 'Processing...';

    const referralCode = document.getElementById('referralCodeInput').value.trim();

    // Validation
    if (!USER_EMAIL) {
        console.error('User email not found for payment');
        CVision.Utils.showAlert('User account error: Email missing. Please re-login.', 'error');
        submitButton.disabled = false;
        submitButton.textContent = 'Subscribe Now';
        return;
    }

    if (!selectedPlan.price || isNaN(selectedPlan.price)) {
        console.error('Invalid plan price:', selectedPlan.price);
        CVision.Utils.showAlert('Plan configuration error: Invalid price.', 'error');
        submitButton.disabled = false;
        submitButton.textContent = 'Subscribe Now';
        return;
    }

    try {
        if (typeof PaystackPop === 'undefined') {
            throw new Error('Paystack library not loaded. Please disable ad blockers and refresh.');
        }

        // Sanitize inputs
        const cleanKey = PAYSTACK_PUBLIC_KEY.trim();
        const cleanEmail = USER_EMAIL.trim();

        console.log('Initializing Paystack with:', {
            email: cleanEmail,
            amount: selectedPlan.price,
            plan: selectedPlan.planCode
        });

        // Initialize Paystack Popup
        const paystackConfig = {
            key: cleanKey,
            email: cleanEmail,
            // currency: 'USD', 
            currency: 'USD',
            metadata: {
                custom_fields: [
                    {
                        display_name: "Plan",
                        variable_name: "plan_name",
                        value: selectedPlan.name
                    }
                ]
            },
            callback: function (transaction) {
                (async () => {
                    try {
                        console.log('Payment complete, verifying:', transaction);
                        // Transaction successful, verify on backend
                        await subscribeToPlan(selectedPlan.id, transaction.reference, referralCode);

                        closeSubscriptionModal();
                        CVision.Utils.showAlert('Subscription successful!', 'success');
                        setTimeout(() => window.location.reload(), 2000);

                    } catch (error) {
                        console.error('Backend verification failed:', error);
                        CVision.Utils.showAlert(error.message || 'Verification failed', 'error');
                        submitButton.disabled = false;
                        submitButton.textContent = 'Subscribe Now';
                    }
                })();
            },
            onClose: () => {
                submitButton.disabled = false;
                submitButton.textContent = 'Subscribe Now';
            }
        };

        // If plan exists, use it and DO NOT send amount (let Paystack handle it)
        if (selectedPlan.planCode && selectedPlan.planCode.trim() !== '') {
            paystackConfig.plan = selectedPlan.planCode.trim();
        } else {
            // Only send amount if no plan code (one-time payment)
            paystackConfig.amount = Math.ceil(selectedPlan.price);
        }

        const handler = PaystackPop.setup(paystackConfig);

        handler.openIframe();
    } catch (error) {
        console.error('Payment initialization failed:', error);
        CVision.Utils.showAlert(error.message, 'error');
        submitButton.disabled = false;
        submitButton.textContent = 'Subscribe Now';
    }
}

async function subscribeToPlan(planId, reference, referralCode) {
    const response = await authenticatedFetch(`${API_BASE_URL}/api/v1/subscriptions/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            plan_id: planId,
            reference: reference, // Pass transaction reference
            referral_code: referralCode
        })
    });

    if (!response || !response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Subscription failed' }));
        throw new Error(error.detail || 'Subscription failed');
    }

    return await response.json();
}

function showCancelModal() {
    document.getElementById('cancelModal').classList.remove('hidden');
    document.getElementById('cancelModal').classList.add('flex');
}

function closeCancelModal() {
    document.getElementById('cancelModal').classList.add('hidden');
    document.getElementById('cancelModal').classList.remove('flex');
}

async function confirmCancel() {
    const reason = document.getElementById('cancelReason').value;

    try {
        const response = await authenticatedFetch(`${API_BASE_URL}/api/v1/subscriptions/cancel`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                cancel_immediately: false,
                reason: reason
            })
        });

        if (!response || !response.ok) throw new Error('Cancellation failed');

        CVision.Utils.showAlert('Subscription will be cancelled at the end of your billing period', 'success');
        closeCancelModal();

        setTimeout(() => window.location.reload(), 2000);

    } catch (error) {
        console.error('Cancel error:', error);
        CVision.Utils.showAlert('Failed to cancel subscription', 'error');
    }
}

async function loadReferralStats() {
    try {
        const response = await authenticatedFetch(`${API_BASE_URL}/api/v1/subscriptions/referrals/stats`);

        if (!response || !response.ok) return;

        const stats = await response.json();
        displayReferralStats(stats);
    } catch (error) {
        console.error('Failed to load referral stats:', error);
    }
}

function displayReferralStats(stats) {
    const container = document.getElementById('referralStats');
    container.innerHTML = `
        <div class="bg-white rounded-lg shadow-sm p-6 border border-gray-100">
            <div class="text-3xl font-bold text-blue-600">${stats.total_referrals || 0}</div>
            <div class="text-gray-600 mt-1">Total Referrals</div>
        </div>
        <div class="bg-white rounded-lg shadow-sm p-6 border border-gray-100">
            <div class="text-3xl font-bold text-green-600">${stats.successful_referrals || 0}</div>
            <div class="text-gray-600 mt-1">Successful</div>
        </div>
        <div class="bg-white rounded-lg shadow-sm p-6 border border-gray-100">
            <div class="text-3xl font-bold text-purple-600">${stats.bonus_searches_earned || 0}</div>
            <div class="text-gray-600 mt-1">Bonus Searches</div>
        </div>
        <div class="bg-white rounded-lg shadow-sm p-6 border border-gray-100">
            <div class="text-3xl font-bold text-orange-600">${stats.next_reward_in || 0}</div>
            <div class="text-gray-600 mt-1">Until Next Reward</div>
        </div>
    `;
}

async function showReferralModal() {
    document.getElementById('referralModal').classList.remove('hidden');
    document.getElementById('referralModal').classList.add('flex');

    await loadReferralInfo();
}

function closeReferralModal() {
    document.getElementById('referralModal').classList.add('hidden');
    document.getElementById('referralModal').classList.remove('flex');
}

async function loadReferralInfo() {
    try {
        const statsResponse = await authenticatedFetch(`${API_BASE_URL}/api/v1/subscriptions/referrals/stats`);

        if (statsResponse && statsResponse.ok) {
            const stats = await statsResponse.json();
            document.getElementById('referralCodeDisplay').textContent =
                stats.referral_code || 'N/A';
        }

        const listResponse = await authenticatedFetch(`${API_BASE_URL}/api/v1/subscriptions/referrals`);

        if (listResponse && listResponse.ok) {
            const data = await listResponse.json();
            displayReferralList(data.referrals || []);
        }

        // Also ensure user email is set for payment if not already
        if (!USER_EMAIL) {
            try {
                const user = CVision.Utils.getUser();
                if (user) USER_EMAIL = user.email;
            } catch (e) { }
        }

    } catch (error) {
        console.error('Failed to load referral info:', error);
    }
}

function displayReferralList(referrals) {
    const container = document.getElementById('referralList');

    if (!referrals || referrals.length === 0) {
        container.innerHTML = '<p class="text-gray-500 text-sm">No referrals yet. Share your code to get started!</p>';
        return;
    }

    container.innerHTML = referrals.map(ref => `
        <div class="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
            <div>
                <div class="font-medium">${ref.referee_email}</div>
                <div class="text-sm text-gray-500">${new Date(ref.referred_at).toLocaleDateString()}</div>
            </div>
            <span class="px-3 py-1 rounded-full text-xs font-semibold ${ref.status === 'completed' ? 'bg-green-100 text-green-700' :
            ref.status === 'pending' ? 'bg-yellow-100 text-yellow-700' :
                'bg-gray-100 text-gray-700'
        }">
                ${ref.status}
            </span>
        </div>
    `).join('');
}

function copyReferralCode() {
    const code = document.getElementById('referralCodeDisplay').textContent;
    if (code && code !== 'N/A' && code !== 'LOADING...') {
        navigator.clipboard.writeText(code).then(() => {
            CVision.Utils.showAlert('Referral code copied!', 'success');
        }).catch(() => {
            CVision.Utils.showAlert('Failed to copy code', 'error');
        });
    }
}

// Make functions globally available
window.selectPlan = selectPlan;
// window.openCustomerPortal = openCustomerPortal; // Removed
window.showCancelModal = showCancelModal;
window.closeCancelModal = closeCancelModal;
window.confirmCancel = confirmCancel;
window.showReferralModal = showReferralModal;
window.closeReferralModal = closeReferralModal;
window.copyReferralCode = copyReferralCode;
window.showSubscriptionModal = showSubscriptionModal;
window.closeSubscriptionModal = closeSubscriptionModal;
window.showUpgradeOptions = showUpgradeOptions;
window.handlePaymentSubmit = handlePaymentSubmit;