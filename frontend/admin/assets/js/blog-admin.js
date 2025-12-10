// Blog Admin JavaScript
(function () {
    'use strict';



    let editor = null;
    let currentEditingPost = null;

    // DOM Elements
    const newPostBtn = document.getElementById('new-post-btn');
    const editorModal = document.getElementById('editor-modal');
    const closeModalBtn = document.getElementById('close-modal');
    const cancelBtn = document.getElementById('cancel-btn');
    const saveBtn = document.getElementById('save-btn');
    const postsTableBody = document.getElementById('posts-table-body');
    const tableLoading = document.getElementById('table-loading');
    const tableEmpty = document.getElementById('table-empty');
    const statusFilter = document.getElementById('status-filter');

    // Initialize
    async function init() {
        // Check authentication first
        if (!CVision || !CVision.Utils || !CVision.Utils.isAuthenticated()) {
            window.location.href = 'login.html';
            return;
        }

        initQuill();
        setupEventListeners();
        await loadPosts();
        loadStats();
    }

    // Replace TinyMCE functions with Quill equivalents
    function initQuill() {
        // Initialize Quill editor
        editor = new Quill('#post-content', {
            theme: 'snow',
            modules: {
                toolbar: [
                    [{ 'header': [1, 2, 3, false] }],
                    ['bold', 'italic', 'underline', 'strike'],
                    ['blockquote', 'code-block'],
                    [{ 'list': 'ordered' }, { 'list': 'bullet' }],
                    [{ 'align': [] }],
                    ['link', 'image'],
                    ['clean']
                ]
            }
        });
    }

    // Get content from Quill
    function getEditorContent() {
        return editor ? editor.root.innerHTML : '';
    }

    // Set content in Quill
    function setEditorContent(html) {
        if (editor) {
            editor.root.innerHTML = html;
        }
    }


    // Setup event listeners
    function setupEventListeners() {
        newPostBtn.addEventListener('click', openNewPostModal);
        closeModalBtn.addEventListener('click', closeModal);
        cancelBtn.addEventListener('click', closeModal);
        saveBtn.addEventListener('click', savePost);

        // Status filter
        statusFilter.addEventListener('change', () => {
            loadPosts();
        });

        // Auto-generate slug from title
        document.getElementById('post-title').addEventListener('input', (e) => {
            if (!currentEditingPost) {
                const slug = generateSlug(e.target.value);
                document.getElementById('post-slug').value = slug;
            }
        });
    }

    // Load posts
    async function loadPosts() {
        try {
            // Auth check moved to init()

            let url = '/blog/posts?page=1&size=50';
            const status = statusFilter.value;

            if (status) {
                url += `&status=${status}`;
            }

            const data = await CVision.API.request(url);

            tableLoading.classList.add('hidden');
            tableEmpty.classList.add('hidden'); // Ensure empty state is hidden first

            if (data.posts.length === 0) {
                postsTableBody.innerHTML = ''; // Clear table
                tableEmpty.classList.remove('hidden');
            } else {
                displayPosts(data.posts);
            }
        } catch (error) {
            console.error('Error loading posts:', error);
            tableLoading.classList.add('hidden');
            postsTableBody.innerHTML = '';
            tableEmpty.classList.remove('hidden');
        }
    }

    // Display posts
    function displayPosts(posts) {
        postsTableBody.innerHTML = posts.map(post => {
            const publishDate = post.published_at
                ? new Date(post.published_at).toLocaleDateString()
                : 'Not published';

            const statusColors = {
                draft: 'bg-gray-100 text-gray-800',
                published: 'bg-green-100 text-green-800',
                archived: 'bg-red-100 text-red-800'
            };

            return `
                <tr>
                    <td class="px-6 py-4 whitespace-nowrap">
                        <div class="text-sm font-medium text-gray-900">${post.title}</div>
                        <a href="../pages/blog-post.html?slug=${post.slug}" target="_blank" class="text-xs text-primary-600 hover:text-primary-800 flex items-center gap-1">
                            ${post.slug} <span class="text-xs">↗</span>
                        </a>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap">
                        <span class="px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${statusColors[post.status]}">
                            ${post.status.charAt(0).toUpperCase() + post.status.slice(1)}
                        </span>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        ${post.categories.join(', ') || 'None'}
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        ${post.views}
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        ${publishDate}
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <a href="../pages/blog-post.html?slug=${post.slug}" target="_blank" class="text-gray-600 hover:text-gray-900 mr-3">View</a>
                        <button onclick="window.blogAdmin.editPost('${post.id}')" class="text-primary-600 hover:text-primary-900 mr-3">Edit</button>
                        <button onclick="window.blogAdmin.deletePost('${post.id}')" class="text-red-600 hover:text-red-900">Delete</button>
                    </td>
                </tr>
            `;
        }).join('');
    }

    // Load stats
    async function loadStats() {
        try {
            const stats = await CVision.API.request('/blog/stats');

            document.getElementById('stat-total').textContent = stats.total_posts;
            document.getElementById('stat-published').textContent = stats.published_count;
            document.getElementById('stat-draft').textContent = stats.draft_count;
            document.getElementById('stat-views').textContent = stats.total_views.toLocaleString();
        } catch (error) {
            console.error('Error loading stats:', error);
        }
    }

    // Open new post modal
    function openNewPostModal() {
        currentEditingPost = null;
        document.getElementById('modal-title').textContent = 'New Blog Post';
        document.getElementById('post-form').reset();
        if (editor) {
            setEditorContent('');
        }
        editorModal.classList.remove('hidden');
    }

    // Edit post
    async function editPost(postId) {
        try {
            const post = await CVision.API.request(`/blog/posts/${postId}`);
            currentEditingPost = post;

            document.getElementById('modal-title').textContent = 'Edit Blog Post';
            document.getElementById('post-title').value = post.title;
            document.getElementById('post-slug').value = post.slug;
            document.getElementById('post-excerpt').value = post.excerpt || '';
            if (editor) {
                setEditorContent(post.content);
            }
            document.getElementById('post-image').value = post.featured_image || '';
            document.getElementById('post-categories').value = post.categories.join(', ');
            document.getElementById('post-tags').value = post.tags.join(', ');
            document.getElementById('seo-title').value = post.seo.meta_title || '';
            document.getElementById('seo-description').value = post.seo.meta_description || '';
            document.getElementById('seo-keywords').value = post.seo.keywords.join(', ');
            document.getElementById('post-status').value = post.status;

            editorModal.classList.remove('hidden');
        } catch (error) {
            console.error('Error loading post:', error);
            alert('Failed to load post');
        }
    }

    // Delete post
    async function deletePost(postId) {
        if (!confirm('Are you sure you want to delete this post?')) {
            return;
        }

        try {
            await CVision.API.request(`/blog/posts/${postId}`, {
                method: 'DELETE'
            });

            await loadPosts();
            loadStats();
        } catch (error) {
            console.error('Error deleting post:', error);
            alert('Failed to delete post');
        }
    }

    // Save post
    async function savePost() {
        const title = document.getElementById('post-title').value.trim();
        if (!title) {
            alert('Please enter a title');
            return;
        }

        const content = editor ? getEditorContent() : '';
        if (!content) {
            alert('Please enter content');
            return;
        }

        const postData = {
            title,
            slug: document.getElementById('post-slug').value.trim() || null,
            content,
            excerpt: document.getElementById('post-excerpt').value.trim() || null,
            featured_image: document.getElementById('post-image').value.trim() || null,
            categories: document.getElementById('post-categories').value
                .split(',')
                .map(c => c.trim())
                .filter(c => c),
            tags: document.getElementById('post-tags').value
                .split(',')
                .map(t => t.trim())
                .filter(t => t),
            seo: {
                meta_title: document.getElementById('seo-title').value.trim() || null,
                meta_description: document.getElementById('seo-description').value.trim() || null,
                keywords: document.getElementById('seo-keywords').value
                    .split(',')
                    .map(k => k.trim())
                    .filter(k => k)
            },
            status: document.getElementById('post-status').value
        };

        try {
            const endpoint = currentEditingPost
                ? `/blog/posts/${currentEditingPost.id}`
                : `/blog/posts`;

            const method = currentEditingPost ? 'PUT' : 'POST';

            await CVision.API.request(endpoint, {
                method,
                body: JSON.stringify(postData)
            });

            closeModal();
            await loadPosts();
            loadStats();
        } catch (error) {
            console.error('Error saving post:', error);
            alert(`Failed to save post: ${error.message}`);
        }
    }

    // Close modal
    function closeModal() {
        editorModal.classList.add('hidden');
        currentEditingPost = null;
    }

    // Generate slug from title
    function generateSlug(title) {
        return title
            .toLowerCase()
            .replace(/[^\w\s-]/g, '')
            .replace(/[\s_-]+/g, '-')
            .replace(/^-+|-+$/g, '');
    }

    // Create mock posts for testing
    async function createMockPosts() {
        if (!confirm('This will create 3 sample posts. Continue?')) return;

        const mockPosts = [
            {
                title: 'Getting Started with AI in 2025',
                slug: 'getting-started-with-ai-2025',
                content: '<p>Artificial Intelligence is transforming how we work...</p>',
                excerpt: 'A comprehensive guide to starting your AI journey.',
                featured_image: 'https://images.unsplash.com/photo-1677442136019-21780ecad995',
                categories: ['AI', 'Technology'],
                tags: ['future', 'innovation'],
                seo: {
                    meta_title: 'AI Guide 2025',
                    meta_description: 'Start your AI journey today.',
                    keywords: ['ai', 'tech']
                },
                status: 'published'
            },
            {
                title: 'Top 10 Resume Tips',
                slug: 'top-10-resume-tips',
                content: '<p>Your resume is your first impression...</p>',
                excerpt: 'Expert advice on crafting the perfect resume.',
                featured_image: 'https://images.unsplash.com/photo-1586281380349-632531db7ed4',
                categories: ['Career', 'Tips'],
                tags: ['resume', 'hiring'],
                seo: {
                    meta_title: 'Resume Tips 2025',
                    meta_description: 'Improve your resume now.',
                    keywords: ['resume', 'jobs']
                },
                status: 'draft'
            },
            {
                title: 'Remote Work Trends',
                slug: 'remote-work-trends',
                content: '<p>Remote work is here to stay...</p>',
                excerpt: 'Analysis of the shifting workplace landscape.',
                featured_image: 'https://images.unsplash.com/photo-1593642532973-d31b6557fa68',
                categories: ['Work', 'Remote'],
                tags: ['wfh', 'trends'],
                seo: {
                    meta_title: 'Remote Work 2025',
                    meta_description: 'Future of remote work.',
                    keywords: ['remote', 'work']
                },
                status: 'archived'
            }
        ];

        try {
            let createdCount = 0;
            for (const post of mockPosts) {
                await CVision.API.request('/blog/posts', {
                    method: 'POST',
                    body: JSON.stringify(post)
                });
                createdCount++;
            }

            alert(`Successfully created ${createdCount} mock posts!`);
            await loadPosts();
            loadStats();
        } catch (error) {
            console.error('Error creating mock posts:', error);
            alert('Failed to create mock posts');
        }
    }

    // Expose functions globally for onclick handlers
    window.blogAdmin = {
        editPost,
        deletePost,
        createMockPosts
    };

    // Start when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
