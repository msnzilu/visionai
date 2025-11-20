        const API_BASE_URL = 'http://localhost:8000';

        console.log('🚀 Dashboard initializing...');

        document.addEventListener('DOMContentLoaded', function() {
            console.log('✅ DOM Content Loaded');
            
            if (!CVision.Utils.isAuthenticated()) {
                window.location.href = 'login.html';
                return;
            }
            
            initializeDashboard();
        });

        async function initializeDashboard() {
            console.log('📊 Initializing dashboard...');
            CVision.initUserInfo();
            await loadUserProfile();
            await loadDocuments();
            await loadSavedJobs();
            setupFileUpload();
            console.log('✅ Dashboard initialized');
        }

        function setupFileUpload() {
            console.log('🔧 Setting up file upload...');
            
            const fileInput = document.getElementById('fileInput');
            const dropZone = document.getElementById('dropZone');

            if (!fileInput) {
                console.error('❌ File input not found');
                return;
            }
            
            if (!dropZone) {
                console.error('❌ Drop zone not found');
                return;
            }

            console.log('✅ Found file input and drop zone');

            // Click handler for drop zone
            dropZone.addEventListener('click', (e) => {
                console.log('🖱️ Drop zone clicked');
                e.preventDefault();
                e.stopPropagation();
                fileInput.click();
            });

            // File input change handler
            fileInput.addEventListener('change', (e) => {
                console.log('📁 File input changed');
                handleFileUpload(e);
            });

            // Drag over handler
            dropZone.addEventListener('dragover', (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropZone.classList.add('border-primary-500', 'bg-primary-50');
                console.log('📦 Dragging over drop zone');
            });

            // Drag leave handler
            dropZone.addEventListener('dragleave', (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropZone.classList.remove('border-primary-500', 'bg-primary-50');
            });

            // Drop handler
            dropZone.addEventListener('drop', (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropZone.classList.remove('border-primary-500', 'bg-primary-50');
                
                console.log('📥 File dropped');
                const files = e.dataTransfer.files;
                
                if (files.length > 0) {
                    console.log('📄 Processing dropped file:', files[0].name);
                    // Set the files to the input element
                    fileInput.files = files;
                    // Trigger the change event manually
                    const event = new Event('change', { bubbles: true });
                    fileInput.dispatchEvent(event);
                }
            });

            console.log('✅ File upload listeners attached');
        }

        async function handleFileUpload(event) {
            const file = event.target.files[0];
            
            if (!file) {
                console.log('⚠️ No file selected');
                return;
            }

            console.log('📤 Starting file upload:', {
                name: file.name,
                type: file.type,
                size: file.size
            });

            // Validate file type
            const allowedTypes = [
                'application/pdf', 
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 
                'application/msword', 
                'text/plain'
            ];
            
            if (!allowedTypes.includes(file.type)) {
                console.error('❌ Invalid file type:', file.type);
                CVision.Utils.showAlert('Invalid file type. Please upload PDF, DOCX, DOC, or TXT files.', 'error');
                event.target.value = '';
                return;
            }

            // Validate file size (10MB max)
            const maxSize = 10 * 1024 * 1024;
            if (file.size > maxSize) {
                console.error('❌ File too large:', file.size);
                CVision.Utils.showAlert('File too large. Maximum size is 10MB.', 'error');
                event.target.value = '';
                return;
            }

            console.log('✅ File validation passed');

            // Show upload progress
            const uploadLoading = document.getElementById('uploadLoading');
            uploadLoading.classList.remove('hidden');

            try {
                const formData = new FormData();
                formData.append('file', file);

                const uploadUrl = `${API_BASE_URL}/api/v1/documents/upload`;
                console.log('🌐 Uploading to:', uploadUrl);

                const response = await fetch(uploadUrl, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${CVision.Utils.getToken()}`
                    },
                    body: formData
                });

                console.log('📡 Response status:', response.status);

                if (!response.ok) {
                    const errorData = await response.json();
                    console.error('❌ Upload error:', errorData);
                    throw new Error(errorData.detail || 'Upload failed');
                }

                const result = await response.json();
                console.log('✅ Upload successful:', result);

                CVision.Utils.showAlert('CV uploaded successfully! Processing...', 'success');
                
                // Reload documents
                setTimeout(async () => {
                    await loadDocuments();
                }, 1000);
                
                // Clear the file input
                event.target.value = '';

            } catch (error) {
                console.error('❌ Upload error:', error);
                CVision.Utils.showAlert(`Upload failed: ${error.message}`, 'error');
            } finally {
                uploadLoading.classList.add('hidden');
            }
        }

        async function loadUserProfile() {
            try {
                const response = await CVision.API.getProfile();
                if (response.success) {
                    const user = response.data.user;

                    const userTierEl = document.getElementById('userTier');
                    if (userTierEl) {
                        userTierEl.textContent = user.subscription_tier.charAt(0).toUpperCase() + user.subscription_tier.slice(1);
                    }

                    if (user.usage_stats) {
                        document.getElementById('searchesUsed').textContent = user.usage_stats.monthly_searches || 0;
                        document.getElementById('applicationsCount').textContent = user.usage_stats.total_applications || 0;
                    }
                }
            } catch (error) {
                console.error('Error loading user profile:', error);
            }
        }


        // async function loadUserProfile() {
        //     try {
        //         const response = await CVision.API.getProfile();
        //         if (response.success) {
        //             const user = response.data.user;
        //             document.getElementById('userTier').textContent = 
        //                 `${user.subscription_tier.charAt(0).toUpperCase() + user.subscription_tier.slice(1)}`;

                    
        //             if (user.usage_stats) {
        //                 document.getElementById('searchesUsed').textContent = user.usage_stats.monthly_searches || 0;
        //                 document.getElementById('applicationsCount').textContent = user.usage_stats.total_applications || 0;
        //             }
        //         }
        //     } catch (error) {
        //         console.error('Error loading user profile:', error);
        //     }
        // }

        async function loadDocuments() {
            try {
                const response = await fetch(`${API_BASE_URL}/api/v1/documents/`, {
                    headers: {
                        'Authorization': `Bearer ${CVision.Utils.getToken()}`
                    }
                });

                if (!response.ok) {
                    throw new Error(`Failed to load documents`);
                }

                const data = await response.json();
                const documents = data.documents || data || [];
                
                displayDocuments(documents);
                document.getElementById('documentsCount').textContent = documents.length;
                document.getElementById('documentsCountText').textContent = 
                    `${documents.length} doc${documents.length !== 1 ? 's' : ''}`;

            } catch (error) {
                console.error('Error loading documents:', error);
                CVision.Utils.showAlert('Failed to load documents', 'error');
            }
        }

        function displayDocuments(documents) {
            const documentsList = document.getElementById('documentsList');
            
            if (documents.length === 0) {
                documentsList.innerHTML = `
                    <div class="text-center py-8 text-gray-500">
                        <svg class="w-10 h-10 sm:w-12 sm:h-12 mx-auto mb-3 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                        </svg>
                        <p class="text-sm sm:text-base">No documents yet</p>
                        <p class="text-xs sm:text-sm mt-1">Upload your CV to start</p>
                    </div>
                `;
                return;
            }

            documentsList.innerHTML = documents.map(doc => {
                const filename = doc.filename || (doc.file_info && doc.file_info.original_filename) || 'Unknown file';
                const fileSize = doc.file_size || (doc.file_info && doc.file_info.file_size) || 0;
                const uploadDate = doc.upload_date || doc.created_at || new Date().toISOString();
                const hasValidData = doc.cv_data && Object.keys(doc.cv_data).length > 0 && !doc.cv_data.error;
                
                return `
                    <div class="border border-gray-200 rounded-lg p-3 sm:p-4 hover:shadow-md transition-shadow min-w-0">
                        <div class="flex items-start justify-between gap-2 sm:gap-3">
                            <div class="flex-1 min-w-0 overflow-hidden">
                                <div class="flex items-center space-x-2 mb-2">
                                    <svg class="w-4 h-4 sm:w-5 sm:h-5 text-gray-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                                    </svg>
                                    <h3 class="text-sm sm:text-base font-medium text-gray-900 truncate" title="${filename}">${filename}</h3>
                                </div>
                                <div class="text-xs sm:text-sm text-gray-500 space-y-1 break-words">
                                    <p class="truncate">${CVision.Utils.formatFileSize(fileSize)} • ${CVision.Utils.formatDate(uploadDate)}</p>
                                    ${hasValidData ? `
                                        <p class="text-green-600 text-xs">✓ Processed</p>
                                    ` : `
                                        <p class="text-yellow-600 text-xs">⚠ Needs processing</p>
                                    `}
                                </div>
                            </div>
                            <div class="flex flex-col space-y-1.5 flex-shrink-0">
                                <button onclick="analyzeDocument('${doc.id || doc._id}')" 
                                    class="px-2 sm:px-3 py-1 text-xs font-medium text-blue-600 bg-blue-100 hover:bg-blue-200 rounded-md transition-colors whitespace-nowrap">
                                    ${hasValidData ? 'Re-analyze' : 'Analyze'}
                                </button>
                                <button onclick="deleteDocument('${doc.id || doc._id}')" 
                                    class="px-2 sm:px-3 py-1 text-xs font-medium text-red-600 bg-red-100 hover:bg-red-200 rounded-md transition-colors">
                                    Delete
                                </button>
                            </div>
                        </div>
                    </div>
                `;
            }).join('');
        }

        async function analyzeDocument(documentId) {
            try {
                const response = await fetch(`${API_BASE_URL}/api/v1/documents/${documentId}/reparse`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${CVision.Utils.getToken()}`
                    }
                });

                if (!response.ok) throw new Error('Analysis failed');

                const result = await response.json();
                
                if (result.success) {
                    CVision.Utils.showAlert('Document analyzed successfully!', 'success');
                    await loadDocuments();
                } else {
                    throw new Error(result.message || 'Analysis failed');
                }
            } catch (error) {
                console.error('Analyze error:', error);
                CVision.Utils.showAlert(`Failed to analyze: ${error.message}`, 'error');
            }
        }

        async function deleteDocument(documentId) {
            if (!confirm('Delete this document?')) return;

            try {
                const response = await fetch(`${API_BASE_URL}/api/v1/documents/${documentId}`, {
                    method: 'DELETE',
                    headers: {
                        'Authorization': `Bearer ${CVision.Utils.getToken()}`
                    }
                });

                if (!response.ok) throw new Error('Delete failed');

                CVision.Utils.showAlert('Document deleted', 'success');
                await loadDocuments();
                
            } catch (error) {
                console.error('Delete error:', error);
                CVision.Utils.showAlert(`Failed to delete: ${error.message}`, 'error');
            }
        }

        function searchJobs() {
            window.location.href = 'pages/jobs.html';
        }

        function viewApplications() {
            window.location.href = 'pages/applications.html';
        }

        function upgradeAccount() {
            window.location.href = 'pages/subscription.html';
        }

        function viewProfile() {
            window.location.href = 'pages/profile.html';
        }

        function logout() {
            CVision.logout();
        }

        async function loadSavedJobs() {
            try {
                const response = await fetch(`${API_BASE_URL}/api/v1/jobs/saved/me?page=1&size=3`, {
                    headers: {
                        'Authorization': `Bearer ${CVision.Utils.getToken()}`
                    }
                });

                if (!response.ok) throw new Error('Failed to load saved jobs');

                const jobs = await response.json();
                displaySavedJobs(jobs);
            } catch (error) {
                console.error('Error loading saved jobs:', error);
            }
        }
        
        function displaySavedJobs(jobs) {
            const container = document.getElementById('savedJobsList');
            
            if (!jobs || jobs.length === 0) {
                container.innerHTML = `
                    <div class="text-center py-8 text-gray-500">
                        <svg class="w-10 h-10 sm:w-12 sm:h-12 mx-auto mb-3 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"></path>
                        </svg>
                        <p class="text-sm sm:text-base">No saved jobs</p>
                        <p class="text-xs sm:text-sm mt-1">Save jobs while searching to view them here</p>
                    </div>
                `;
                return;
            }

            container.innerHTML = jobs.map(job => `
                <div class="border border-gray-200 rounded-lg p-3 sm:p-4 hover:shadow-md transition-shadow">
                    <div class="flex items-start justify-between gap-2">
                        <div class="flex-1 min-w-0">
                            <h3 class="text-sm sm:text-base font-medium text-gray-900 truncate">${job.title}</h3>
                            <p class="text-xs sm:text-sm text-gray-600 mt-1">${job.company_name}</p>
                            <p class="text-xs text-gray-500 mt-1">${job.location}</p>
                            ${job.match_score ? `
                                <div class="mt-2 flex items-center gap-2">
                                    <span class="text-xs font-medium text-green-600">${Math.round(job.match_score * 100)}% Match</span>
                                </div>
                            ` : ''}
                        </div>
                        <div class="flex flex-col gap-1.5">
                            <button onclick="viewJobDetails('${job.id}')" 
                                class="px-2 sm:px-3 py-1 text-xs font-medium text-primary-600 bg-primary-100 hover:bg-primary-200 rounded-md transition-colors whitespace-nowrap">
                                View
                            </button>
                            <button onclick="unsaveJob('${job.id}')" 
                                class="px-2 sm:px-3 py-1 text-xs font-medium text-red-600 bg-red-100 hover:bg-red-200 rounded-md transition-colors">
                                Remove
                            </button>
                        </div>
                    </div>
                </div>
            `).join('');
        }

        function viewJobDetails(jobId) {
            window.location.href = `pages/jobs.html?job=${jobId}`;
        }

        async function unsaveJob(jobId) {
            if (!confirm('Remove this job from saved?')) return;

            try {
                const response = await fetch(`${API_BASE_URL}/api/v1/jobs/save/${jobId}`, {
                    method: 'DELETE',
                    headers: {
                        'Authorization': `Bearer ${CVision.Utils.getToken()}`
                    }
                });

                if (!response.ok) throw new Error('Failed to unsave job');

                CVision.Utils.showAlert('Job removed from saved', 'success');
                await loadSavedJobs();
            } catch (error) {
                console.error('Error unsaving job:', error);
                CVision.Utils.showAlert('Failed to remove job', 'error');
            }
        }
