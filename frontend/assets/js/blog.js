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
        await loadCategories();
        await loadTags();
        await loadPosts();
        setupEventListeners();
        loadFromURL();
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

    // Load posts
    async function loadPosts() {
        showLoading();

        try {
            const params = new URLSearchParams({
                page: currentPage,
                size: 9
            });

            if (currentFilters.search) params.append('search', currentFilters.search);
            if (currentFilters.category) params.append('categories', currentFilters.category);
            if (currentFilters.tag) params.append('tags', currentFilters.tag);

            const response = await fetch(`${API_BASE}/blog/posts?${params}`);

            if (!response.ok) {
                throw new Error('Failed to load posts');
            }

            const data = await response.json();

            if (data.posts.length === 0) {
                showEmpty();
            } else {
                displayPosts(data.posts);
                displayPagination(data);
            }
        } catch (error) {
            console.error('Error loading posts:', error);
            showEmpty();
        }
    }

    // Display posts
    function displayPosts(posts) {
        postsGrid.innerHTML = '';

        posts.forEach(post => {
            const card = createPostCard(post);
            postsGrid.appendChild(card);
        });

        loadingState.classList.add('hidden');
        emptyState.classList.add('hidden');
        postsGrid.classList.remove('hidden');
    }

    // Create post card
    function createPostCard(post) {
        const card = document.createElement('div');
        card.className = 'blog-card';

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
                    ${post.categories.slice(0, 2).map(cat => `
                        <span class="category-badge">${cat}</span>
                    `).join('')}
                </div>
                <a href="blog-post.html?slug=${post.slug}" class="blog-card-title hover:text-primary-600 transition">
                    ${post.title}
                </a>
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
        if (data.pages <= 1) {
            pagination.classList.add('hidden');
            return;
        }

        pagination.classList.remove('hidden');

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
            btn.className = `px-4 py-2 rounded-lg ${i === currentPage ? 'bg-primary-600 text-white' : 'border border-gray-300 hover:bg-gray-50'}`;
            btn.addEventListener('click', () => goToPage(i));
            pageNumbers.appendChild(btn);
        }
    }

    // Go to page
    function goToPage(page) {
        currentPage = page;
        loadPosts();
        window.scrollTo({ top: 0, behavior: 'smooth' });
        updateURL();
    }

    // Show loading
    function showLoading() {
        loadingState.classList.remove('hidden');
        emptyState.classList.add('hidden');
        postsGrid.classList.add('hidden');
        pagination.classList.add('hidden');
    }

    // Show empty
    function showEmpty() {
        loadingState.classList.add('hidden');
        emptyState.classList.remove('hidden');
        postsGrid.classList.add('hidden');
        pagination.classList.add('hidden');
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
                loadPosts();
                updateURL();
            }, 500);
        });

        // Category filter
        categoryFilter.addEventListener('change', (e) => {
            currentFilters.category = e.target.value;
            currentPage = 1;
            loadPosts();
            updateURL();
        });

        // Tag filter
        tagFilter.addEventListener('change', (e) => {
            currentFilters.tag = e.target.value;
            currentPage = 1;
            loadPosts();
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
