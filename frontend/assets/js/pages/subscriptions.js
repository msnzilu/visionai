// frontend/assets/js/subscriptions.js
const API_BASE_URL = 'http://localhost:8000';
let STRIPE_PUBLISHABLE_KEY = null;

let stripe;
let elements;
let cardElement;
let selectedPlan = null;
let currentSubscription = null;

// Load Stripe configuration from backend
async function loadStripeConfig() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/subscriptions/config/stripe`);
        if (response.ok) {
            const config = await response.json();
            STRIPE_PUBLISHABLE_KEY = config.publishable_key;
            
            // Initialize Stripe once we have the key
            if (STRIPE_PUBLISHABLE_KEY) {
                stripe = Stripe(STRIPE_PUBLISHABLE_KEY);
            }
        } else {
            console.error('Failed to load Stripe config');
        }
    } catch (error) {
        console.error('Failed to load Stripe config:', error);
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
    
    // Load Stripe config first
    await loadStripeConfig();
    
    if (!stripe) {
        CVision.Utils.showAlert('Payment system unavailable. Please check configuration.', 'error');
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
        if (manageBtn) manageBtn.style.display = 'inline-block';
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
        card.className = `bg-white rounded-xl shadow-lg border-2 p-8 relative ${
            plan.is_popular ? 'border-blue-500' : 'border-gray-200'
        }`;
        
        if (plan.is_popular) {
            card.innerHTML += `
                <div class="absolute top-0 right-0 bg-blue-500 text-white px-4 py-1 rounded-bl-lg rounded-tr-lg text-sm font-semibold">
                    Most Popular
                </div>
            `;
        }
        
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
                    <button onclick="selectPlan('${plan.id}', '${plan.name}', ${plan.price.amount})" 
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

function selectPlan(planId, planName, price) {
    selectedPlan = { id: planId, name: planName, price: price };
    
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
    
    if (!elements && stripe) {
        elements = stripe.elements();
        cardElement = elements.create('card', {
            style: {
                base: {
                    fontSize: '16px',
                    color: '#32325d',
                    '::placeholder': {
                        color: '#aab7c4',
                    },
                },
            },
        });
        cardElement.mount('#card-element');
        
        cardElement.on('change', (event) => {
            const displayError = document.getElementById('card-errors');
            if (event.error) {
                displayError.textContent = event.error.message;
            } else {
                displayError.textContent = '';
            }
        });
        
        document.getElementById('payment-form').addEventListener('submit', handlePaymentSubmit);
    }
}

function closeSubscriptionModal() {
    document.getElementById('subscriptionModal').classList.add('hidden');
    document.getElementById('subscriptionModal').classList.remove('flex');
}

async function handlePaymentSubmit(e) {
    e.preventDefault();
    
    const submitButton = document.getElementById('submit-payment');
    submitButton.disabled = true;
    submitButton.textContent = 'Processing...';
    
    try {
        const { paymentMethod, error } = await stripe.createPaymentMethod({
            type: 'card',
            card: cardElement,
        });
        
        if (error) {
            throw new Error(error.message);
        }
        
        const referralCode = document.getElementById('referralCodeInput').value.trim();
        
        await subscribeToPlan(selectedPlan.id, paymentMethod.id, referralCode);
        
        closeSubscriptionModal();
        CVision.Utils.showAlert('Subscription successful!', 'success');
        
        setTimeout(() => window.location.reload(), 2000);
        
    } catch (error) {
        console.error('Payment error:', error);
        CVision.Utils.showAlert(error.message || 'Payment failed', 'error');
        submitButton.disabled = false;
        submitButton.textContent = 'Subscribe Now';
    }
}

async function subscribeToPlan(planId, paymentMethodId, referralCode) {
    const response = await authenticatedFetch(`${API_BASE_URL}/api/v1/subscriptions/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            plan_id: planId,
            payment_method_id: paymentMethodId,
            referral_code: referralCode
        })
    });
    
    if (!response || !response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Subscription failed' }));
        throw new Error(error.detail || 'Subscription failed');
    }
    
    return await response.json();
}

async function openCustomerPortal() {
    try {
        const response = await authenticatedFetch(`${API_BASE_URL}/api/v1/subscriptions/portal-session`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                return_url: window.location.href
            })
        });
        
        if (!response) {
            throw new Error('Failed to connect to server');
        }
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => null);
            const errorMessage = errorData?.detail || 'Failed to create portal session';
            throw new Error(errorMessage);
        }
        
        const data = await response.json();
        
        if (!data.url) {
            throw new Error('Invalid portal session response');
        }
        
        window.location.href = data.url;
        
    } catch (error) {
        console.error('Portal error:', error);
        
        let message = 'Failed to open billing portal';
        
        if (error.message.includes('No billing account') || error.message.includes('No Stripe customer')) {
            message = 'Please subscribe to a paid plan first to access the billing portal.';
        } else if (error.message) {
            message = error.message;
        }
        
        CVision.Utils.showAlert(message, 'error');
    }
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
            <span class="px-3 py-1 rounded-full text-xs font-semibold ${
                ref.status === 'completed' ? 'bg-green-100 text-green-700' : 
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
window.openCustomerPortal = openCustomerPortal;
window.showCancelModal = showCancelModal;
window.closeCancelModal = closeCancelModal;
window.confirmCancel = confirmCancel;
window.showReferralModal = showReferralModal;
window.closeReferralModal = closeReferralModal;
window.copyReferralCode = copyReferralCode;
window.showSubscriptionModal = showSubscriptionModal;
window.closeSubscriptionModal = closeSubscriptionModal;
window.showUpgradeOptions = showUpgradeOptions;