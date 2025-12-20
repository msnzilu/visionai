// SEO Meta Tags Manager
// Place in: /assets/js/seo-meta.js

const SEO = {
    // Default site-wide settings
    defaults: {
        siteName: 'Synovae',
        siteUrl: 'https://www.synovae.io',
        defaultImage: 'https://www.synovae.io/assets/images/og-default.jpg',
        twitterHandle: '@synovae',
        locale: 'en_US',
        type: 'website'
    },

    // Page-specific configurations
    pages: {
        'index': {
            title: 'Synovae - AI-Powered Job Application Assistant | Get Hired Faster',
            description: 'Land your dream job 10x faster with Synovae\'s AI-powered job application platform. Automated CV optimization, smart job matching, and one-click applications. Start your free trial today.',
            keywords: 'AI job search, automated job applications, CV optimization, resume builder, job matching, ATS optimization, career tools',
            canonical: 'https://www.synovae.io/',
            image: 'https://www.synovae.io/assets/images/og-home.jpg'
        },
        'how-it-works': {
            title: 'How It Works - Synovae | 4 Simple Steps to Your Dream Job',
            description: 'Discover how Synovae\'s AI-powered platform helps you land your dream job in 4 simple steps: Upload CV, Find Jobs, Customize Applications, Apply Instantly. Get started in 2 minutes.',
            keywords: 'how synovae works, AI job application process, automated job search, CV customization, job application steps',
            canonical: 'https://www.synovae.io/how-it-works',
            image: 'https://www.synovae.io/assets/images/og-how-it-works.jpg'
        },
        'features': {
            title: 'Features - Synovae | AI-Powered Job Search Tools & Automation',
            description: 'Explore Synovae\'s powerful features: AI CV optimization, smart job matching, automated applications, interview prep, and application tracking. See why 10,000+ users trust us.',
            keywords: 'job search features, AI resume optimization, automated job applications, job tracking, interview preparation, ATS checker',
            canonical: 'https://www.synovae.io/features',
            image: 'https://www.synovae.io/assets/images/og-features.jpg'
        },
        'pricing': {
            title: 'Pricing - Synovae | Affordable Plans for Every Job Seeker',
            description: 'Choose the perfect plan for your job search. Free tier available. Premium plans start at $29/month with unlimited applications, AI customization, and priority support.',
            keywords: 'synovae pricing, job search subscription, affordable job search tools, premium job application service',
            canonical: 'https://www.synovae.io/pricing',
            image: 'https://www.synovae.io/assets/images/og-pricing.jpg'
        },
        'contact': {
            title: 'Contact Us - Synovae | Get Support & Answers',
            description: 'Need help? Contact Synovae\'s support team. Get answers about our AI job search platform, technical support, or partnership opportunities. We\'re here to help.',
            keywords: 'contact synovae, customer support, job search help, technical support',
            canonical: 'https://www.synovae.io/info/contact',
            image: 'https://www.synovae.io/assets/images/og-contact.jpg'
        },
        'help': {
            title: 'Help Center - Synovae | FAQs & Support Documentation',
            description: 'Find answers to common questions about Synovae. Learn how to use AI job matching, optimize your CV, automate applications, and maximize your job search success.',
            keywords: 'synovae help, job search FAQs, how to use synovae, troubleshooting, user guide',
            canonical: 'https://www.synovae.io/info/help',
            image: 'https://www.synovae.io/assets/images/og-help.jpg'
        },
        'register': {
            title: 'Sign Up - Synovae | Start Your Free Trial Today',
            description: 'Create your free Synovae account and start landing more interviews. No credit card required. Get instant access to AI-powered job search tools.',
            keywords: 'sign up synovae, create account, free trial, register job search platform',
            canonical: 'https://www.synovae.io/register',
            image: 'https://www.synovae.io/assets/images/og-register.jpg'
        },
        'login': {
            title: 'Login - Synovae | Access Your Job Search Dashboard',
            description: 'Log in to your Synovae account to continue your job search, track applications, and access AI-powered career tools.',
            keywords: 'synovae login, sign in, access account',
            canonical: 'https://www.synovae.io/login',
            image: 'https://www.synovae.io/assets/images/og-login.jpg'
        },
        'privacy': {
            title: 'Privacy Policy - Synovae | Your Data Security & Privacy',
            description: 'Learn how Synovae protects your personal information and CV data. Read our comprehensive privacy policy and data protection practices.',
            keywords: 'privacy policy, data protection, GDPR compliance, user privacy',
            canonical: 'https://www.synovae.io/info/legal/privacy',
            type: 'article'
        },
        'terms': {
            title: 'Terms of Service - Synovae | User Agreement & Legal Terms',
            description: 'Read Synovae\'s terms of service, user agreement, and legal policies. Understand your rights and responsibilities when using our platform.',
            keywords: 'terms of service, user agreement, legal terms, terms and conditions',
            canonical: 'https://www.synovae.io/info/legal/terms',
            type: 'article'
        }
    },

    // Initialize SEO for current page
    init() {
        // Get path, remove leading/trailing slashes, and remove .html
        let path = window.location.pathname.replace(/^\/+|\/+$/g, '');
        let currentPage = path.split('/').pop().replace(/\.html$/, '') || 'index';

        const pageConfig = this.pages[currentPage] || this.pages['index'];

        this.setMetaTags(pageConfig);
        this.setStructuredData(pageConfig);
    },

    // Set all meta tags
    setMetaTags(config) {
        const { title, description, keywords, canonical, image, type } = config;
        const fullImage = image || this.defaults.defaultImage;
        const pageType = type || this.defaults.type;

        // Set document title
        document.title = title;

        // Basic meta tags
        this.setOrUpdateMeta('description', description);
        this.setOrUpdateMeta('keywords', keywords);

        // Canonical URL
        this.setCanonical(canonical);

        // Open Graph tags
        this.setOrUpdateMetaProperty('og:site_name', this.defaults.siteName);
        this.setOrUpdateMetaProperty('og:type', pageType);
        this.setOrUpdateMetaProperty('og:title', title);
        this.setOrUpdateMetaProperty('og:description', description);
        this.setOrUpdateMetaProperty('og:url', canonical);
        this.setOrUpdateMetaProperty('og:image', fullImage);
        this.setOrUpdateMetaProperty('og:image:width', '1200');
        this.setOrUpdateMetaProperty('og:image:height', '630');
        this.setOrUpdateMetaProperty('og:locale', this.defaults.locale);

        // Twitter Card tags
        this.setOrUpdateMetaName('twitter:card', 'summary_large_image');
        this.setOrUpdateMetaName('twitter:site', this.defaults.twitterHandle);
        this.setOrUpdateMetaName('twitter:title', title);
        this.setOrUpdateMetaName('twitter:description', description);
        this.setOrUpdateMetaName('twitter:image', fullImage);

        // Additional SEO tags
        this.setOrUpdateMetaName('robots', 'index, follow, max-snippet:-1, max-image-preview:large, max-video-preview:-1');
        this.setOrUpdateMetaName('author', this.defaults.siteName);
    },

    // Helper: Set or update meta tag by name
    setOrUpdateMeta(name, content) {
        let meta = document.querySelector(`meta[name="${name}"]`);
        if (!meta) {
            meta = document.createElement('meta');
            meta.setAttribute('name', name);
            document.head.appendChild(meta);
        }
        meta.setAttribute('content', content);
    },

    // Helper: Set or update meta property (for Open Graph)
    setOrUpdateMetaProperty(property, content) {
        let meta = document.querySelector(`meta[property="${property}"]`);
        if (!meta) {
            meta = document.createElement('meta');
            meta.setAttribute('property', property);
            document.head.appendChild(meta);
        }
        meta.setAttribute('content', content);
    },

    // Helper: Set or update meta name (for Twitter)
    setOrUpdateMetaName(name, content) {
        let meta = document.querySelector(`meta[name="${name}"]`);
        if (!meta) {
            meta = document.createElement('meta');
            meta.setAttribute('name', name);
            document.head.appendChild(meta);
        }
        meta.setAttribute('content', content);
    },

    // Set canonical URL
    setCanonical(url) {
        let link = document.querySelector('link[rel="canonical"]');
        if (!link) {
            link = document.createElement('link');
            link.setAttribute('rel', 'canonical');
            document.head.appendChild(link);
        }
        link.setAttribute('href', url);
    },

    // Set JSON-LD structured data
    setStructuredData(config) {
        let path = window.location.pathname.replace(/^\/+|\/+$/g, '');
        let currentPage = path.split('/').pop().replace(/\.html$/, '') || 'index';

        // Organization schema (for all pages)
        const organizationSchema = {
            "@context": "https://schema.org",
            "@type": "Organization",
            "name": this.defaults.siteName,
            "url": this.defaults.siteUrl,
            "logo": `${this.defaults.siteUrl}/assets/images/logo.png`,
            "description": "AI-powered job application platform helping job seekers land their dream jobs faster",
            "sameAs": [
                "https://twitter.com/synovae",
                "https://linkedin.com/company/synovae",
                "https://facebook.com/synovae"
            ],
            "contactPoint": {
                "@type": "ContactPoint",
                "contactType": "Customer Support",
                "email": "support@synovae.io"
            }
        };

        // Website schema
        const websiteSchema = {
            "@context": "https://schema.org",
            "@type": "WebSite",
            "name": this.defaults.siteName,
            "url": this.defaults.siteUrl,
            "potentialAction": {
                "@type": "SearchAction",
                "target": `${this.defaults.siteUrl}/dashboard.html?search={search_term_string}`,
                "query-input": "required name=search_term_string"
            }
        };

        // Page-specific schemas
        let pageSchema = null;

        if (currentPage === 'index') {
            pageSchema = {
                "@context": "https://schema.org",
                "@type": "WebPage",
                "name": config.title,
                "description": config.description,
                "url": config.canonical
            };
        } else if (currentPage === 'how-it-works') {
            pageSchema = {
                "@context": "https://schema.org",
                "@type": "HowTo",
                "name": "How to Use Synovae for Job Applications",
                "description": config.description,
                "step": [
                    {
                        "@type": "HowToStep",
                        "name": "Upload Your CV",
                        "text": "Upload your resume and our AI analyzes your skills instantly"
                    },
                    {
                        "@type": "HowToStep",
                        "name": "Find Perfect Jobs",
                        "text": "Get matched with relevant job opportunities based on your profile"
                    },
                    {
                        "@type": "HowToStep",
                        "name": "Customize Applications",
                        "text": "AI generates tailored CVs and cover letters for each application"
                    },
                    {
                        "@type": "HowToStep",
                        "name": "Apply Instantly",
                        "text": "One-click application or fully automated submission"
                    }
                ]
            };
        }

        // Insert schemas into page
        this.insertStructuredData('organization-schema', organizationSchema);
        this.insertStructuredData('website-schema', websiteSchema);
        if (pageSchema) {
            this.insertStructuredData('page-schema', pageSchema);
        }
    },

    // Helper: Insert or update structured data script
    insertStructuredData(id, data) {
        let script = document.getElementById(id);
        if (!script) {
            script = document.createElement('script');
            script.id = id;
            script.type = 'application/ld+json';
            document.head.appendChild(script);
        }
        script.textContent = JSON.stringify(data, null, 2);
    }
};

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => SEO.init());
} else {
    SEO.init();
}