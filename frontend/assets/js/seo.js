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
        twitterHandle: '@synovae',
        locale: 'en_US',

        // Social media links for structured data
        socialLinks: [
            'https://twitter.com/synovae',
            'https://linkedin.com/company/synovae',
            'https://facebook.com/synovae'
        ],
        contactEmail: 'support@synovae.io',

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

    // Helper: Set or update meta tag by name (prevents duplicates)
    function setOrUpdateMeta(name, content) {
        let meta = document.querySelector(`meta[name="${name}"]`);
        if (!meta) {
            meta = document.createElement('meta');
            meta.setAttribute('name', name);
            document.head.appendChild(meta);
        }
        meta.setAttribute('content', content);
    }

    // Helper: Set or update meta property (for Open Graph)
    function setOrUpdateMetaProperty(property, content) {
        let meta = document.querySelector(`meta[property="${property}"]`);
        if (!meta) {
            meta = document.createElement('meta');
            meta.setAttribute('property', property);
            document.head.appendChild(meta);
        }
        meta.setAttribute('content', content);
    }

    // Helper: Set or update link tag
    function setOrUpdateLink(rel, href, type = null) {
        let link = document.querySelector(`link[rel="${rel}"]`);
        if (!link) {
            link = document.createElement('link');
            link.setAttribute('rel', rel);
            document.head.appendChild(link);
        }
        link.setAttribute('href', href);
        if (type) {
            link.setAttribute('type', type);
        }
    }

    // Legacy create functions for backward compatibility
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

        // Primary Meta Tags (using setOrUpdate to prevent duplicates)
        setOrUpdateMeta('title', seo.title);
        setOrUpdateMeta('description', seo.description);
        if (seo.keywords) {
            setOrUpdateMeta('keywords', seo.keywords);
        }
        setOrUpdateMeta('author', seoConfig.author);
        // Enhanced robots meta with more directives
        setOrUpdateMeta('robots', 'index, follow, max-snippet:-1, max-image-preview:large, max-video-preview:-1');

        // Canonical URL
        setOrUpdateLink('canonical', seo.url);

        // Open Graph / Facebook
        setOrUpdateMetaProperty('og:type', seo.type);
        setOrUpdateMetaProperty('og:url', seo.url);
        setOrUpdateMetaProperty('og:title', seo.title);
        setOrUpdateMetaProperty('og:description', seo.description);
        setOrUpdateMetaProperty('og:image', seo.image);
        setOrUpdateMetaProperty('og:image:width', '1200');
        setOrUpdateMetaProperty('og:image:height', '630');
        setOrUpdateMetaProperty('og:site_name', seoConfig.siteName);
        setOrUpdateMetaProperty('og:locale', seoConfig.locale);

        // Twitter Card
        setOrUpdateMeta('twitter:card', 'summary_large_image');
        setOrUpdateMeta('twitter:url', seo.url);
        setOrUpdateMeta('twitter:title', seo.title);
        setOrUpdateMeta('twitter:description', seo.description);
        setOrUpdateMeta('twitter:image', seo.image);
        if (seoConfig.twitterHandle) {
            setOrUpdateMeta('twitter:site', seoConfig.twitterHandle);
        }

        // Favicon - Modern approach with multiple formats
        head.appendChild(createLink('icon', '/assets/images/favicon.ico', 'image/x-icon'));
        head.appendChild(createLink('icon', '/assets/images/favicon/android-chrome-192x192.png', 'image/png'));
        head.appendChild(createLink('icon', '/assets/images/favicon/android-chrome-512x512.png', 'image/png'));
        head.appendChild(createLink('apple-touch-icon', '/assets/images/favicon/apple-touch-icon'));

        // Structured Data (JSON-LD)
        injectStructuredData(seo);
    }

    // Helper: Insert or update structured data script
    function insertStructuredData(id, data) {
        let script = document.getElementById(id);
        if (!script) {
            script = document.createElement('script');
            script.id = id;
            script.type = 'application/ld+json';
            document.head.appendChild(script);
        }
        script.textContent = JSON.stringify(data, null, 2);
    }

    // Inject Structured Data
    function injectStructuredData(seo) {
        const currentPage = getCurrentPage();

        // Enhanced Organization schema with social links and contact
        const organizationSchema = {
            "@context": "https://schema.org",
            "@type": "Organization",
            "name": seoConfig.siteName,
            "url": seoConfig.baseUrl,
            "logo": `${seoConfig.baseUrl}/assets/images/my-logo.png`,
            "description": seoConfig.defaultDescription,
            "sameAs": seoConfig.socialLinks,
            "contactPoint": {
                "@type": "ContactPoint",
                "contactType": "Customer Support",
                "email": seoConfig.contactEmail
            }
        };

        // Website schema with search action
        const websiteSchema = {
            "@context": "https://schema.org",
            "@type": "WebSite",
            "name": seoConfig.siteName,
            "url": seoConfig.baseUrl,
            "potentialAction": {
                "@type": "SearchAction",
                "target": `${seoConfig.baseUrl}/dashboard?search={search_term_string}`,
                "query-input": "required name=search_term_string"
            }
        };

        // Page-specific structured data
        let pageSchema = null;

        if (currentPage === 'index') {
            pageSchema = {
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
        } else if (currentPage === 'how-it-works') {
            // HowTo schema for how-it-works page
            pageSchema = {
                "@context": "https://schema.org",
                "@type": "HowTo",
                "name": "How to Use Synovae for Job Applications",
                "description": seo.description,
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
        } else {
            pageSchema = {
                "@context": "https://schema.org",
                "@type": "WebPage",
                "name": seo.title,
                "url": seo.url,
                "description": seo.description,
                "publisher": organizationSchema
            };
        }

        // Insert all schemas (using IDs to prevent duplicates)
        insertStructuredData('organization-schema', organizationSchema);
        insertStructuredData('website-schema', websiteSchema);
        if (pageSchema) {
            insertStructuredData('page-schema', pageSchema);
        }
    }

    // Initialize SEO when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', injectSEO);
    } else {
        injectSEO();
    }

})();