/**
 * Landing Page Configuration & Logic
 */

const LandingConfig = {
    stats: [
        { value: '10K+', label: 'Jobs Matched' },
        { value: '85%', label: 'Success Rate' },
        { value: '2Min', label: 'Setup Time' }
    ],
    features: [
        {
            icon: '🤖',
            title: 'AI CV Analysis',
            description: 'Upload your CV and get instant AI-powered analysis with suggestions for improvement and optimization'
        },
        {
            icon: '🎯',
            title: 'Smart Job Matching',
            description: 'Find perfect job matches based on your skills, experience, and preferences using advanced algorithms'
        },
        {
            icon: '📝',
            title: 'Custom CV Generation',
            description: 'Generate tailored CVs for each application, optimized for ATS systems and specific job requirements'
        },
        {
            icon: '✉️',
            title: 'AI Cover Letters',
            description: 'Create personalized cover letters that highlight your relevant experience for each position'
        },
        {
            icon: '🚀',
            title: 'One-Click Apply',
            description: 'Apply to jobs instantly with browser automation and intelligent form filling technology'
        },
        {
            icon: '📊',
            title: 'Application Tracking',
            description: 'Monitor all applications, interviews, and responses in one comprehensive dashboard'
        }
    ],
    pricing: [
        {
            name: 'Free',
            priceInCents: 0,
            features: [
                { text: '1 manual application per day', included: true },
                { text: 'Basic job search', included: true },
                { text: 'CV upload & analysis', included: true },
                { text: 'Watermarked documents', included: false }
            ],
            buttonText: 'Get Started Free',
            buttonLink: '/register',
            highlight: false
        },
        {
            name: 'Basic',
            priceInCents: 1999,
            features: [
                { text: '10 automated applications daily', included: true },
                { text: 'Up to 20 manual applications daily', included: true },
                { text: 'Premium CV templates', included: true },
                { text: 'No watermarks', included: true },
                { text: 'Basic auto-fill', included: true }
            ],
            buttonText: 'Start Free Trial',
            buttonLink: '/register',
            highlight: true,
            highlightText: 'Most Popular'
        },
        {
            name: 'Premium',
            priceInCents: 3999,
            features: [
                { text: '30 automated applications daily', included: true },
                { text: 'Up to 50 manual applications daily', included: true },
                { text: 'Priority support', included: true },
                { text: 'Advanced analytics', included: true },
                { text: 'Full automation', included: true }
            ],
            buttonText: 'Go Premium',
            buttonLink: '/register',
            highlight: false
        }
    ]
};

const Landing = {
    // Format price based on user's currency
    formatPrice(amountInCents) {
        if (window.CVision && window.CVision.Currency) {
            return CVision.Currency.format(amountInCents);
        }
        // Fallback to USD
        return `$${(amountInCents / 100).toFixed(2)}`;
    },

    async init() {
        // Detect currency from geolocation first
        if (window.CVision && window.CVision.Currency) {
            await CVision.Currency.initFromGeolocation();
        }

        this.renderStats();
        this.renderFeatures();
        this.renderPricing();
        this.initMobileMenu();
        this.initUpload();
        this.initSmoothScroll();
    },

    initSmoothScroll() {
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                const targetId = this.getAttribute('href');
                if (targetId === '#') return;

                const target = document.querySelector(targetId);
                if (target) {
                    target.scrollIntoView({ behavior: 'smooth' });
                }
            });
        });
    },

    initUpload() {
        // CV Upload functionality
        const uploadZone = document.getElementById('cv-upload-zone');
        const fileInput = document.getElementById('cv-file-input');
        const getStartedBtn = document.getElementById('get-started-btn');
        const preferencesContainer = document.getElementById('preferences-container');
        let uploadedFile = null;

        if (!uploadZone || !fileInput) return;

        // File upload handlers
        uploadZone.addEventListener('click', () => fileInput.click());

        uploadZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadZone.classList.add('border-white/60', 'bg-white/10');
        });

        uploadZone.addEventListener('dragleave', () => {
            uploadZone.classList.remove('border-white/60', 'bg-white/10');
        });

        uploadZone.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadZone.classList.remove('border-white/60', 'bg-white/10');
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                handleFileUpload(files[0]);
            }
        });

        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                handleFileUpload(e.target.files[0]);
            }
        });

        function handleFileUpload(file) {
            // Validate file
            const allowedTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain'];
            if (!allowedTypes.includes(file.type)) {
                CVision.Utils.showAlert('Please upload a PDF, DOCX, or TXT file', 'error');
                return;
            }

            if (file.size > 10 * 1024 * 1024) {
                CVision.Utils.showAlert('File size must be less than 10MB', 'error');
                return;
            }

            uploadedFile = file;
            uploadZone.innerHTML = `
                <div class="text-4xl mb-4">✅</div>
                <div class="text-gray-900 font-bold mb-2">${file.name}</div>
                <div class="text-gray-500 text-sm">Ready to analyze • Click to change</div>
            `;

            // Reveal preferences with animation
            preferencesContainer.classList.remove('hidden');
            // Small delay to allow display:block to apply before adding opacity
            setTimeout(() => {
                preferencesContainer.classList.remove('opacity-0', 'translate-y-4');
            }, 10);

            getStartedBtn.disabled = false;
            getStartedBtn.innerHTML = '<span class="button-text">Analyze CV & Find Jobs</span>';
        }

        // Get started button handler
        if (getStartedBtn) {
            getStartedBtn.addEventListener('click', function () {
                if (uploadedFile) {
                    // Store form data temporarily
                    const jobTitle = document.getElementById('job-title').value;
                    const location = document.getElementById('location').value;
                    const salaryRange = document.getElementById('salary-range').value;

                    localStorage.setItem('landing_preferences', JSON.stringify({
                        jobTitle,
                        location,
                        salaryRange,
                        fileName: uploadedFile.name
                    }));

                    // Redirect to login with file upload intent
                    window.location.href = '/login';
                } else {
                    CVision.Utils.showAlert('Please upload your CV first', 'warning');
                }
            });
        }
    },

    renderStats() {
        const container = document.getElementById('stats-container');
        if (!container) return;

        container.innerHTML = LandingConfig.stats.map(stat => `
            <div class="text-left">
                <div class="text-3xl font-bold text-gray-900 mb-1">${stat.value}</div>
                <div class="text-sm text-gray-500 uppercase tracking-wide font-medium">${stat.label}</div>
            </div>
        `).join('');
    },

    renderFeatures() {
        const container = document.getElementById('features-container');
        if (!container) return;

        container.innerHTML = LandingConfig.features.map(feature => `
            <div class="feature-card bg-gray-50 p-8 rounded-2xl border border-gray-100 hover:shadow-lg transition-all hover:bg-white group">
                <div class="w-14 h-14 bg-white rounded-xl shadow-sm flex items-center justify-center text-3xl mb-6 group-hover:scale-110 transition-transform duration-300">
                    ${feature.icon}
                </div>
                <h3 class="text-xl font-bold text-gray-900 mb-3">${feature.title}</h3>
                <p class="text-gray-600 leading-relaxed">${feature.description}</p>
            </div>
        `).join('');
    },

    renderPricing() {
        const container = document.getElementById('pricing-container');
        if (!container) return;

        container.innerHTML = LandingConfig.pricing.map(plan => {
            const formattedPrice = this.formatPrice(plan.priceInCents);

            return `
            <div class="bg-white rounded-2xl p-8 relative ${plan.highlight ? 'border-2 border-primary-500 shadow-xl scale-105 z-10' : 'border border-gray-200 shadow-md hover:shadow-lg transition-all'}">
                ${plan.highlight ? `
                <div class="absolute -top-4 left-1/2 transform -translate-x-1/2 bg-gradient-to-r from-primary-600 to-primary-500 text-white px-4 py-1 rounded-full text-sm font-bold shadow-md">
                    ${plan.highlightText}
                </div>
                ` : ''}
                
                <div class="text-center mb-8">
                    <h3 class="text-2xl font-bold text-gray-900 mb-4">${plan.name}</h3>
                    <div class="flex justify-center items-baseline mb-2">
                        <span class="text-4xl font-extrabold text-gray-900">${formattedPrice}</span>
                        <span class="text-gray-500 ml-1">/month</span>
                    </div>
                </div>
                
                <ul class="space-y-4 mb-8">
                    ${plan.features.map(feature => `
                        <li class="flex items-start space-x-3">
                            <span class="${feature.included ? 'text-green-500' : 'text-gray-300'} mt-1 text-lg">
                                ${feature.included ? '✓' : '✗'}
                            </span>
                            <span class="${feature.included ? 'text-gray-700' : 'text-gray-400'}">
                                ${feature.text}
                            </span>
                        </li>
                    `).join('')}
                </ul>
                
                <a href="${plan.buttonLink}" class="block w-full py-4 px-6 ${plan.highlight ? 'btn-gradient text-white shadow-lg hover:shadow-xl' : 'bg-gray-100 text-gray-800 hover:bg-gray-200'} rounded-xl font-bold text-center transition-all">
                    ${plan.buttonText}
                </a>
            </div>
        `}).join('');
    },

    initMobileMenu() {
        const btn = document.getElementById('mobile-menu-button');
        const menu = document.getElementById('mobile-menu');

        if (btn && menu) {
            btn.addEventListener('click', () => {
                menu.classList.toggle('hidden');
            });
        }
    }
};

document.addEventListener('DOMContentLoaded', () => {
    Landing.init();
});
