/**
 * Reusable SEO Component
 * Place in: /assets/js/seo.js
 * 
 * Usage in HTML:
 * <head>
 *     <script src="/assets/js/seo.js"></script>
 * </head>
 */

(function () {
    'use strict';

    // SEO Configuration for all pages
    const seoConfig = {
        baseUrl: 'https://www.synovae.io',
        siteName: 'Synovae',
        author: 'Synovae',
        twitterHandle: '@synovae', // Optional: Add your Twitter handle

        // Default fallback values
        defaultImage: 'https://www.synovae.io/assets/images/og-default.jpg',
        defaultTitle: 'Synovae - AI-Powered Job Application Platform',
        defaultDescription: 'Land your dream job faster with Synovae. Our AI-powered platform automates job applications, creates tailored CVs, and matches you with perfect opportunities.',

        // Page-specific configurations
        pages: {
            'index': {
                title: 'Synovae - AI-Powered Job Application Platform | Automate Your Job Search',
                description: 'Land your dream job faster with Synovae. Our AI-powered platform automates job applications, creates tailored CVs, and matches you with perfect opportunities. Start free today!',
                keywords: 'job search, AI job application, automated job search, CV builder, cover letter generator, job matching, career platform, resume optimization',
                image: 'https://www.synovae.io/assets/images/og-home.jpg',
                type: 'website'
            },
            'how-it-works': {
                title: 'How It Works - Synovae | AI Job Application in 4 Simple Steps',
                description: 'Discover how Synovae streamlines your job search in 4 simple steps. Upload your CV, find perfect matches, customize applications, and apply instantly with AI.',
                keywords: 'how it works, job application process, automated job search, AI job matching, career automation',
                image: 'https://www.synovae.io/assets/images/og-how-it-works.jpg',
                type: 'article'
            },
            'features': {
                title: 'Features - Synovae | AI-Powered Job Search Tools',
                description: 'Explore powerful features including AI-powered job matching, automated applications, custom CV generation, cover letter writing, and comprehensive application tracking.',
                keywords: 'job search features, AI matching, automated applications, CV builder, cover letter generator, application tracking',
                image: 'https://www.synovae.io/assets/images/og-features.jpg',
                type: 'website'
            },
            'pricing': {
                title: 'Pricing - Synovae | Affordable Job Search Plans',
                description: 'Choose the perfect plan for your job search. From free basic access to unlimited applications with our premium plans. No hidden fees, cancel anytime.',
                keywords: 'pricing, job search plans, subscription, free trial, job application pricing',
                image: 'https://www.synovae.io/assets/images/og-pricing.jpg',
                type: 'website'
            },
            'info/contact': {
                title: 'Contact Us - Synovae | Get Support for Your Job Search',
                description: 'Get in touch with our team. We\'re here to help you succeed in your job search journey. Fast response times and dedicated support.',
                keywords: 'contact, support, help, customer service, job search help',
                image: 'https://www.synovae.io/assets/images/og-contact.jpg',
                type: 'website'
            },
            'register': {
                title: 'Sign Up - Synovae | Start Your Free Trial Today',
                description: 'Create your free Synovae account and start landing more interviews. No credit card required. Get started in under 2 minutes.',
                keywords: 'sign up, register, create account, free trial, job search registration',
                image: 'https://www.synovae.io/assets/images/og-register.jpg',
                type: 'website'
            },
            'login': {
                title: 'Login - Synovae | Access Your Job Search Dashboard',
                description: 'Login to your Synovae account to manage your job applications, track interviews, and continue your job search journey.',
                keywords: 'login, sign in, account access, job search dashboard',
                image: 'https://www.synovae.io/assets/images/og-login.jpg',
                type: 'website'
            },
            'info/blog': {
                title: 'Blog - Synovae | Job Search Tips, Career Advice & AI Insights',
                description: 'Discover expert job search strategies, career development tips, and insights on AI-powered recruitment. Stay updated with the latest trends in job hunting and career growth.',
                keywords: 'job search tips, career advice, resume tips, interview preparation, AI recruitment, career development, job hunting strategies, professional growth',
                image: 'https://www.synovae.io/assets/images/og-blog.jpg',
                type: 'website',
                canonical: 'https://www.synovae.io/info/blog'
            },

            'info/help': {
                title: 'Help Center - Synovae | FAQs, Guides & Support',
                description: 'Get answers to your questions about Synovae. Browse our comprehensive help center for tutorials, FAQs, troubleshooting guides, and customer support resources.',
                keywords: 'help center, customer support, FAQ, tutorials, troubleshooting, user guide, how to use, support docs',
                image: 'https://www.synovae.io/assets/images/og-help.jpg',
                type: 'website',
                canonical: 'https://www.synovae.io/info/help'
            },
            'info/legal/privacy': {
                title: 'Privacy Policy - Synovae | Your Data Security & Privacy',
                description: 'Learn how Synovae protects your personal information and CV data. Read our comprehensive privacy policy and data protection practices.',
                keywords: 'privacy policy, data protection, GDPR compliance, user privacy',
                canonical: 'https://www.synovae.io/info/legal/privacy',
                type: 'article'
            },
            'info/legal/terms': {
                title: 'Terms of Service - Synovae | User Agreement & Legal Terms',
                description: 'Read Synovae\'s terms of service, user agreement, and legal policies. Understand your rights and responsibilities when using our platform.',
                keywords: 'terms of service, user agreement, legal terms, terms and conditions',
                canonical: 'https://www.synovae.io/info/legal/terms',
                type: 'article'
            },
            'info/contact': {
                title: 'Contact Us - Synovae | Get Support & Answers',
                description: 'Need help? Contact Synovae\'s support team. Get answers about our AI job search platform, technical support, or partnership opportunities. We\'re here to help.',
                keywords: 'contact synovae, customer support, job search help, technical support',
                canonical: 'https://www.synovae.io/info/contact',
                image: 'https://www.synovae.io/assets/images/og-contact.jpg'
            },
        }
    };

    // Get current page
    function getCurrentPage() {
        let path = window.location.pathname;
        let parts = path.split('/').filter(Boolean);

        // Remove .html if it exists in the URL part
        let page = (parts.length > 0 ? parts.join('/') : 'index').replace(/\.html$/, '');

        return page;
    }

    // Get SEO data for current page
    function getPageSEO() {
        const currentPage = getCurrentPage();
        const pageSEO = seoConfig.pages[currentPage] || {};

        return {
            title: pageSEO.title || seoConfig.defaultTitle,
            description: pageSEO.description || seoConfig.defaultDescription,
            keywords: pageSEO.keywords || '',
            image: pageSEO.image || seoConfig.defaultImage,
            type: pageSEO.type || 'website',
            url: `${seoConfig.baseUrl}/${currentPage === 'index' ? '' : currentPage}`
        };
    }

    // Create meta tag
    function createMeta(name, content, isProperty = false) {
        const meta = document.createElement('meta');
        if (isProperty) {
            meta.setAttribute('property', name);
        } else {
            meta.setAttribute('name', name);
        }
        meta.setAttribute('content', content);
        return meta;
    }

    // Create link tag
    function createLink(rel, href, type = null) {
        const link = document.createElement('link');
        link.setAttribute('rel', rel);
        link.setAttribute('href', href);
        if (type) {
            link.setAttribute('type', type);
        }
        return link;
    }

    // Inject SEO tags
    function injectSEO() {
        const seo = getPageSEO();
        const head = document.head;

        // Set page title
        document.title = seo.title;

        // Primary Meta Tags
        head.appendChild(createMeta('title', seo.title));
        head.appendChild(createMeta('description', seo.description));
        if (seo.keywords) {
            head.appendChild(createMeta('keywords', seo.keywords));
        }
        head.appendChild(createMeta('author', seoConfig.author));
        head.appendChild(createMeta('robots', 'index, follow'));

        // Canonical URL
        head.appendChild(createLink('canonical', seo.url));

        // Open Graph / Facebook
        head.appendChild(createMeta('og:type', seo.type, true));
        head.appendChild(createMeta('og:url', seo.url, true));
        head.appendChild(createMeta('og:title', seo.title, true));
        head.appendChild(createMeta('og:description', seo.description, true));
        head.appendChild(createMeta('og:image', seo.image, true));
        head.appendChild(createMeta('og:image:width', '1200', true));
        head.appendChild(createMeta('og:image:height', '630', true));
        head.appendChild(createMeta('og:site_name', seoConfig.siteName, true));

        // Twitter Card
        head.appendChild(createMeta('twitter:card', 'summary_large_image', true));
        head.appendChild(createMeta('twitter:url', seo.url, true));
        head.appendChild(createMeta('twitter:title', seo.title, true));
        head.appendChild(createMeta('twitter:description', seo.description, true));
        head.appendChild(createMeta('twitter:image', seo.image, true));
        if (seoConfig.twitterHandle) {
            head.appendChild(createMeta('twitter:site', seoConfig.twitterHandle, true));
        }

        // Favicon
        head.appendChild(createLink('icon', '/assets/images/favicon.png', 'image/png'));
        head.appendChild(createLink('apple-touch-icon', '/assets/images/favicon.png'));

        // Structured Data (JSON-LD)
        injectStructuredData(seo);
    }

    // Inject Structured Data
    function injectStructuredData(seo) {
        const currentPage = getCurrentPage();
        let structuredData = {};

        // Base organization data
        const organization = {
            "@context": "https://schema.org",
            "@type": "Organization",
            "name": seoConfig.siteName,
            "url": seoConfig.baseUrl,
            "logo": `${seoConfig.baseUrl}/assets/images/logo.svg`,
            "description": seoConfig.defaultDescription
        };

        // Page-specific structured data
        if (currentPage === 'index') {
            structuredData = {
                "@context": "https://schema.org",
                "@type": "WebApplication",
                "name": seoConfig.siteName,
                "url": seoConfig.baseUrl,
                "description": seo.description,
                "applicationCategory": "BusinessApplication",
                "operatingSystem": "Web",
                "offers": {
                    "@type": "Offer",
                    "price": "0",
                    "priceCurrency": "USD"
                }
            };
        } else {
            structuredData = {
                "@context": "https://schema.org",
                "@type": "WebPage",
                "name": seo.title,
                "url": seo.url,
                "description": seo.description,
                "publisher": organization
            };
        }

        const script = document.createElement('script');
        script.type = 'application/ld+json';
        script.text = JSON.stringify(structuredData);
        document.head.appendChild(script);
    }

    // Initialize SEO when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', injectSEO);
    } else {
        injectSEO();
    }

})();