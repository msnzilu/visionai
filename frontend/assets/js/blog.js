// Blog listing page JavaScript
(function () {
    'use strict';

    const API_BASE = window.location.hostname === 'localhost'
        ? 'http://localhost:8000/api/v1'
        : 'https://visionsai.store/api/v1';

    let currentPage = 1;
    let currentFilters = {
        search: '',
        category: '',
        tag: ''
    };

    // DOM Elements
    const searchInput = document.getElementById('search-input');
    const categoryFilter = document.getElementById('category-filter');
    const tagFilter = document.getElementById('tag-filter');
    const postsGrid = document.getElementById('blog-posts-grid');
    const loadingState = document.getElementById('loading-state');
    const emptyState = document.getElementById('empty-state');
    const pagination = document.getElementById('pagination');
    const prevPageBtn = document.getElementById('prev-page');
    const nextPageBtn = document.getElementById('next-page');
    const pageNumbers = document.getElementById('page-numbers');

    // Initialize
    async function init() {
        try {
            await loadCategories();
            await loadTags();

            // Parallel loads
            await Promise.all([
                loadFeaturedPost(),
                loadRecentPosts(),
                loadTopPosts()
            ]);

            // Show content after all loads attempt to finish
            document.getElementById('loading-state').classList.add('hidden');
            document.getElementById('blog-content').classList.remove('hidden');

            // If main js didn't load footer for some reason, try again
            if (typeof loadFooter === 'function' && document.getElementById('footer-container').innerHTML === '') {
                loadFooter();
            }

        } catch (error) {
            console.error('Initialization error:', error);
            document.getElementById('loading-state').classList.add('hidden');
            document.getElementById('empty-state').classList.remove('hidden');
        }

        setupEventListeners();
        loadFromURL();
    }

    // Load Featured Post (Latest 1)
    async function loadFeaturedPost() {
        try {
            const response = await fetch(`${API_BASE}/blog/posts?size=1&page=1&status=published`);
            if (!response.ok) return;
            const data = await response.json();

            if (data.posts && data.posts.length > 0) {
                renderFeaturedPost(data.posts[0]);
            } else {
                // If no featured post, hide container
                document.getElementById('featured-post-container').classList.add('hidden');
            }
        } catch (error) {
            console.error('Error loading featured post:', error);
            document.getElementById('featured-post-container').classList.add('hidden');
        }
    }

    // Render Featured Post
    function renderFeaturedPost(post) {
        const container = document.getElementById('featured-post-container');
        if (!container) return;

        const imageUrl = post.featured_image || '/assets/images/blog/default-hero.jpg';
        const date = new Date(post.published_at).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' });

        container.innerHTML = `
            <div class="featured-hero relative rounded-2xl overflow-hidden group cursor-pointer" onclick="window.location.href='/info/blog-post?slug=${post.slug}'">
                <img src="${imageUrl}" alt="${post.title}" class="featured-hero-image absolute inset-0 w-full h-full object-cover transition-transform duration-700 group-hover:scale-105">
                <div class="absolute inset-0 bg-gradient-to-t from-gray-900/90 via-gray-900/40 to-transparent"></div>
                
                <div class="featured-hero-content relative z-10 p-8 md:p-12 w-full max-w-4xl mt-auto">
                    <span class="inline-block px-3 py-1 bg-primary-600 text-white text-xs font-bold uppercase tracking-wider rounded-full mb-4">Featured</span>
                    <h1 class="text-3xl md:text-5xl font-bold text-white mb-4 leading-tight group-hover:text-primary-200 transition-colors">${post.title}</h1>
                    <p class="text-gray-200 text-lg md:text-xl mb-6 line-clamp-2 max-w-2xl">${post.excerpt || ''}</p>
                    
                    <div class="flex items-center gap-4 text-white/80 text-sm">
                        <div class="flex items-center gap-2">
                             <div class="w-8 h-8 rounded-full bg-primary-500/30 flex items-center justify-center text-white font-bold text-xs border border-white/20">
                                ${post.author.name.charAt(0)}
                            </div>
                            <span>${post.author.name}</span>
                        </div>
                        <span>•</span>
                        <span>${date}</span>
                        <span>•</span>
                        <span>${post.reading_time} min read</span>
                    </div>
                </div>
            </div>
        `;
    }

    // Load recent posts (List View)
    async function loadRecentPosts() {
        const container = document.getElementById('recent-posts-container');
        // If sorting or filtering is active, we treat "Recent" as the main results area
        // We might want to skip the first one if it's the same as featured, but for now simplistic is okay
        // Or strictly page 1, size 10 to start

        try {
            const params = new URLSearchParams({
                page: currentPage,
                size: 7, // Getting 7 for the list
                status: 'published'
            });

            if (currentFilters.search) params.append('search', currentFilters.search);
            if (currentFilters.category) params.append('categories', currentFilters.category);
            if (currentFilters.tag) params.append('tags', currentFilters.tag);

            // If filtering, we just use the main recent list validation
            const response = await fetch(`${API_BASE}/blog/posts?${params}`);
            if (!response.ok) throw new Error('Failed');

            const data = await response.json();

            if (data.posts.length === 0 && currentPage === 1) {
                container.innerHTML = '<p class="text-gray-500 text-center py-8">No matching posts found.</p>';
                return;
            }

            renderRecentPosts(data.posts);
            displayPagination(data);

        } catch (error) {
            console.error('Error loading recent posts:', error);
        }
    }

    function renderRecentPosts(posts) {
        const container = document.getElementById('recent-posts-container');
        container.innerHTML = '';

        posts.forEach(post => {
            const card = createPostCard(post); // Uses existing list-view style logic
            container.appendChild(card);
        });
    }

    // Load Top Posts (Sidebar)
    async function loadTopPosts() {
        const container = document.getElementById('top-posts-container');
        try {
            const response = await fetch(`${API_BASE}/blog/posts?size=5&sort_by=views&status=published`);
            if (!response.ok) return;
            const data = await response.json();

            container.innerHTML = '';

            if (data.posts.length === 0) {
                container.innerHTML = '<p class="text-gray-500 text-sm">No top posts yet.</p>';
                return;
            }

            data.posts.forEach((post, index) => {
                const imageUrl = post.featured_image || '/assets/images/blog/default-thumb.jpg';
                const el = document.createElement('a');
                el.href = `/info/blog-post?slug=${post.slug}`;
                el.className = 'top-post-card group block hover:bg-gray-50 transition p-2 rounded-lg';
                el.innerHTML = `
                    <span class="top-post-number text-gray-200 font-black text-3xl leading-none w-8 group-hover:text-primary-200 transition-colors">${index + 1}</span>
                    <div class="flex-1">
                        <h4 class="font-bold text-gray-900 text-sm mb-1 line-clamp-2 group-hover:text-primary-600 transition-colors leading-snug">${post.title}</h4>
                        <span class="text-xs text-gray-500">${post.views} views</span>
                    </div>
                `;
                container.appendChild(el);
            });

        } catch (error) {
            console.error('Error loading top posts:', error);
        }
    }

    // Load categories
    async function loadCategories() {
        try {
            const response = await fetch(`${API_BASE}/blog/categories`);
            if (!response.ok) return;

            const categories = await response.json();

            categories.forEach(cat => {
                const option = document.createElement('option');
                option.value = cat.name;
                option.textContent = `${cat.name} (${cat.count})`;
                categoryFilter.appendChild(option);
            });
        } catch (error) {
            console.error('Error loading categories:', error);
        }
    }

    // Load tags
    async function loadTags() {
        try {
            const response = await fetch(`${API_BASE}/blog/tags`);
            if (!response.ok) return;

            const tags = await response.json();

            tags.forEach(tag => {
                const option = document.createElement('option');
                option.value = tag.name;
                option.textContent = `${tag.name} (${tag.count})`;
                tagFilter.appendChild(option);
            });
        } catch (error) {
            console.error('Error loading tags:', error);
        }
    }

    // Legacy loadPosts redirect
    async function loadPosts() {
        return loadRecentPosts();
    }

    // Create post card (List View style matches CSS)
    function createPostCard(post) {
        const card = document.createElement('div');
        card.className = 'blog-card group cursor-pointer';
        card.onclick = () => window.location.href = `/info/blog-post?slug=${post.slug}`;

        const imageUrl = post.featured_image || 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="400" height="200"%3E%3Cdefs%3E%3ClinearGradient id="grad" x1="0%25" y1="0%25" x2="100%25" y2="100%25"%3E%3Cstop offset="0%25" style="stop-color:%23667eea;stop-opacity:1" /%3E%3Cstop offset="100%25" style="stop-color:%23764ba2;stop-opacity:1" /%3E%3C/linearGradient%3E%3C/defs%3E%3Crect width="400" height="200" fill="url(%23grad)" /%3E%3C/svg%3E';

        const publishDate = post.published_at ? new Date(post.published_at).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        }) : 'Draft';

        card.innerHTML = `
            <img src="${imageUrl}" alt="${post.title}" class="blog-card-image" loading="lazy">
            <div class="blog-card-content">
                <div class="flex flex-wrap gap-2 mb-3">
                    ${post.categories.slice(0, 1).map(cat => `
                        <span class="category-badge">${cat}</span>
                    `).join('')}
                </div>
                <h3 class="blog-card-title group-hover:text-primary-600 transition">
                    ${post.title}
                </h3>
                <p class="blog-card-excerpt">${post.excerpt || ''}</p>
                <div class="blog-card-meta">
                    <span>${publishDate}</span>
                    <span>${post.reading_time} min read</span>
                </div>
            </div>
        `;

        return card;
    }

    // Display pagination
    function displayPagination(data) {
        const paginationContainer = document.getElementById('pagination');
        if (data.pages <= 1) {
            paginationContainer.classList.add('hidden');
            return;
        }

        paginationContainer.classList.remove('hidden');

        // Update buttons
        prevPageBtn.disabled = currentPage === 1;
        nextPageBtn.disabled = currentPage === data.pages;

        // Generate page numbers
        pageNumbers.innerHTML = '';

        const maxPages = 5;
        let startPage = Math.max(1, currentPage - Math.floor(maxPages / 2));
        let endPage = Math.min(data.pages, startPage + maxPages - 1);

        if (endPage - startPage < maxPages - 1) {
            startPage = Math.max(1, endPage - maxPages + 1);
        }

        for (let i = startPage; i <= endPage; i++) {
            const btn = document.createElement('button');
            btn.textContent = i;
            btn.className = i === currentPage ? 'pagination-btn-active' : 'pagination-btn';
            btn.addEventListener('click', () => goToPage(i));
            pageNumbers.appendChild(btn);
        }
    }

    // Go to page
    function goToPage(page) {
        currentPage = page;
        loadRecentPosts();
        document.getElementById('recent-posts-container').scrollIntoView({ behavior: 'smooth' });
        updateURL();
    }

    // Setup event listeners
    function setupEventListeners() {
        // Search with debounce
        let searchTimeout;
        searchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                currentFilters.search = e.target.value;
                currentPage = 1;
                loadRecentPosts();
                updateURL();
            }, 500);
        });

        // Category filter
        categoryFilter.addEventListener('change', (e) => {
            currentFilters.category = e.target.value;
            currentPage = 1;
            loadRecentPosts();
            updateURL();
        });

        // Tag filter
        tagFilter.addEventListener('change', (e) => {
            currentFilters.tag = e.target.value;
            currentPage = 1;
            loadRecentPosts();
            updateURL();
        });

        // Pagination
        prevPageBtn.addEventListener('click', () => {
            if (currentPage > 1) {
                goToPage(currentPage - 1);
            }
        });

        nextPageBtn.addEventListener('click', () => {
            goToPage(currentPage + 1);
        });
    }

    // Load from URL parameters
    function loadFromURL() {
        const params = new URLSearchParams(window.location.search);

        if (params.has('search')) {
            currentFilters.search = params.get('search');
            searchInput.value = currentFilters.search;
        }

        if (params.has('category')) {
            currentFilters.category = params.get('category');
            categoryFilter.value = currentFilters.category;
        }

        if (params.has('tag')) {
            currentFilters.tag = params.get('tag');
            tagFilter.value = currentFilters.tag;
        }

        if (params.has('page')) {
            currentPage = parseInt(params.get('page')) || 1;
        }
    }

    // Update URL
    function updateURL() {
        const params = new URLSearchParams();

        if (currentFilters.search) params.set('search', currentFilters.search);
        if (currentFilters.category) params.set('category', currentFilters.category);
        if (currentFilters.tag) params.set('tag', currentFilters.tag);
        if (currentPage > 1) params.set('page', currentPage);

        const newURL = `${window.location.pathname}${params.toString() ? '?' + params.toString() : ''}`;
        window.history.replaceState({}, '', newURL);
    }

    // Start when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
