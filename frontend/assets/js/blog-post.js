// Single blog post page JavaScript
(function () {
    'use strict';

    const API_BASE = window.location.hostname === 'localhost'
        ? 'http://localhost:8000/api/v1'
        : 'https://visionsai.store/api/v1';

    let currentPost = null;

    // DOM Elements
    const loadingState = document.getElementById('loading-state');
    const errorState = document.getElementById('error-state');
    const articleContent = document.getElementById('article-content');

    // Initialize
    async function init() {
        const slug = getSlugFromURL();

        if (!slug) {
            showError();
            return;
        }

        await loadPost(slug);
    }

    // Get slug from URL
    function getSlugFromURL() {
        const params = new URLSearchParams(window.location.search);
        return params.get('slug');
    }

    // Load post
    async function loadPost(slug) {
        try {
            const response = await fetch(`${API_BASE}/blog/posts/${slug}`);

            if (!response.ok) {
                throw new Error('Post not found');
            }

            currentPost = await response.json();
            displayPost(currentPost);
            await loadRelatedPosts(currentPost.id);
        } catch (error) {
            console.error('Error loading post:', error);
            showError();
        }
    }

    // Display post
    function displayPost(post) {
        // Update page title and meta tags
        document.getElementById('page-title').textContent = `${post.title} - VisionAI Blog`;
        document.getElementById('meta-description').setAttribute('content', post.seo.meta_description || post.excerpt || '');
        document.getElementById('meta-keywords').setAttribute('content', post.seo.keywords.join(', '));

        // Open Graph
        document.getElementById('og-title').setAttribute('content', post.seo.og_title || post.title);
        document.getElementById('og-description').setAttribute('content', post.seo.og_description || post.excerpt || '');
        document.getElementById('og-url').setAttribute('content', window.location.href);
        if (post.featured_image) {
            document.getElementById('og-image').setAttribute('content', post.featured_image);
        }

        // Breadcrumb
        document.getElementById('breadcrumb-title').textContent = post.title;

        // Categories
        const categoriesContainer = document.getElementById('article-categories');
        categoriesContainer.innerHTML = post.categories.map(cat => `
            <a href="blog.html?category=${cat}" class="category-badge">${cat}</a>
        `).join('');

        // Title
        document.getElementById('article-title').textContent = post.title;

        // Author (Handle missing author data safely)
        const authorName = post.author && post.author.name ? post.author.name : 'VisionAI Team';
        const authorAvatarUrl = post.author ? post.author.avatar_url : null;

        const authorAvatar = document.getElementById('author-avatar');
        if (authorAvatarUrl) {
            authorAvatar.innerHTML = `<img src="${authorAvatarUrl}" alt="${authorName}" class="w-full h-full rounded-full object-cover">`;
        } else {
            authorAvatar.textContent = authorName.charAt(0).toUpperCase();
        }

        document.getElementById('author-name').textContent = authorName;

        // Date
        const publishDate = new Date(post.published_at).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
        document.getElementById('publish-date').textContent = publishDate;

        // Reading time
        document.getElementById('reading-time').textContent = post.reading_time;

        // Views
        document.getElementById('view-count').textContent = post.views;

        // Featured image
        if (post.featured_image) {
            const featuredImageContainer = document.getElementById('featured-image-container');
            const featuredImage = document.getElementById('featured-image');
            featuredImage.src = post.featured_image;
            featuredImage.alt = post.title;
            featuredImageContainer.classList.remove('hidden');
        }

        // Article body
        document.getElementById('article-body').innerHTML = post.content;

        // Tags
        const tagsContainer = document.getElementById('article-tags');
        tagsContainer.innerHTML = post.tags.map(tag => `
            <a href="blog.html?tag=${tag}" class="tag-badge">${tag}</a>
        `).join('');

        // Setup social sharing
        setupSocialSharing(post);

        // Show article
        loadingState.classList.add('hidden');
        articleContent.classList.remove('hidden');

        // Add JSON-LD structured data
        addStructuredData(post);
    }

    // Load related posts
    async function loadRelatedPosts(postId) {
        try {
            const response = await fetch(`${API_BASE}/blog/posts/${postId}/related?limit=3`);

            if (!response.ok) return;

            const relatedPosts = await response.json();

            if (relatedPosts.length > 0) {
                displayRelatedPosts(relatedPosts);
            }
        } catch (error) {
            console.error('Error loading related posts:', error);
        }
    }

    // Display related posts
    function displayRelatedPosts(posts) {
        const container = document.getElementById('related-posts');
        const section = document.getElementById('related-posts-section');

        container.innerHTML = posts.map(post => {
            const imageUrl = post.featured_image || 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="400" height="200"%3E%3Cdefs%3E%3ClinearGradient id="grad" x1="0%25" y1="0%25" x2="100%25" y2="100%25"%3E%3Cstop offset="0%25" style="stop-color:%23667eea;stop-opacity:1" /%3E%3Cstop offset="100%25" style="stop-color:%23764ba2;stop-opacity:1" /%3E%3C/linearGradient%3E%3C/defs%3E%3Crect width="400" height="200" fill="url(%23grad)" /%3E%3C/svg%3E';

            return `
                <div class="blog-card">
                    <img src="${imageUrl}" alt="${post.title}" class="blog-card-image" loading="lazy">
                    <div class="blog-card-content">
                        <a href="blog-post.html?slug=${post.slug}" class="blog-card-title hover:text-primary-600 transition">
                            ${post.title}
                        </a>
                        <p class="blog-card-excerpt">${post.excerpt || ''}</p>
                        <div class="blog-card-meta">
                            <span>${post.reading_time} min read</span>
                        </div>
                    </div>
                </div>
            `;
        }).join('');

        section.classList.remove('hidden');
    }

    // Setup social sharing
    function setupSocialSharing(post) {
        const url = encodeURIComponent(window.location.href);
        const title = encodeURIComponent(post.title);
        const text = encodeURIComponent(post.excerpt || '');

        // Twitter
        document.getElementById('share-twitter').addEventListener('click', () => {
            window.open(`https://twitter.com/intent/tweet?url=${url}&text=${title}`, '_blank', 'width=600,height=400');
        });

        // LinkedIn
        document.getElementById('share-linkedin').addEventListener('click', () => {
            window.open(`https://www.linkedin.com/sharing/share-offsite/?url=${url}`, '_blank', 'width=600,height=400');
        });

        // Copy link
        document.getElementById('copy-link').addEventListener('click', async () => {
            try {
                await navigator.clipboard.writeText(window.location.href);
                const btn = document.getElementById('copy-link');
                const originalText = btn.innerHTML;
                btn.innerHTML = '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg> Copied!';
                setTimeout(() => {
                    btn.innerHTML = originalText;
                }, 2000);
            } catch (error) {
                console.error('Failed to copy link:', error);
            }
        });
    }

    // Add structured data (JSON-LD)
    function addStructuredData(post) {
        const script = document.createElement('script');
        script.type = 'application/ld+json';
        script.textContent = JSON.stringify({
            "@context": "https://schema.org",
            "@type": "BlogPosting",
            "headline": post.title,
            "description": post.excerpt || '',
            "image": post.featured_image || '',
            "author": {
                "@type": "Person",
                "name": post.author && post.author.name ? post.author.name : 'VisionAI Team'
            },
            "publisher": {
                "@type": "Organization",
                "name": "VisionAI",
                "logo": {
                    "@type": "ImageObject",
                    "url": "https://visionsai.store/logo.png"
                }
            },
            "datePublished": post.published_at,
            "dateModified": post.updated_at,
            "mainEntityOfPage": {
                "@type": "WebPage",
                "@id": window.location.href
            }
        });
        document.head.appendChild(script);
    }

    // Show error
    function showError() {
        loadingState.classList.add('hidden');
        errorState.classList.remove('hidden');
    }

    // Start when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
