/**
 * CV Loader Component
 * Reusable utility to fetch parsed CV data from user profile or documents.
 */

window.CVLoader = {
    /**
     * Get parsed CV data from user profile or most recent document.
     * @returns {Promise<{cvData: Object|null, source: 'profile'|'document'|null, userInfo: Object|null}>}
     */
    async getParsedCV() {
        const token = localStorage.getItem('access_token');
        if (!token) {
            console.warn('CVLoader: No access token found.');
            return { cvData: null, source: null, userInfo: null };
        }

        const headers = { 'Authorization': `Bearer ${token}` };

        // 1. Try user profile first
        try {
            const profileRes = await fetch('/api/v1/users/me', { headers });
            if (profileRes.ok) {
                const profileData = await profileRes.json();
                const cvData = profileData.cv_data;

                if (cvData && Object.keys(cvData).length > 0) {
                    console.log('CVLoader: CV data found in user profile.');
                    return {
                        cvData: cvData,
                        source: 'profile',
                        userInfo: {
                            full_name: profileData.full_name,
                            email: profileData.email
                        }
                    };
                }
            }
        } catch (err) {
            console.error('CVLoader: Error fetching user profile:', err);
        }

        // 2. Fallback: Check documents
        console.log('CVLoader: Profile CV empty, checking documents...');
        try {
            const docsRes = await fetch('/api/v1/documents/', { headers });
            if (docsRes.ok) {
                const docsData = await docsRes.json();
                const documents = docsData.documents || docsData || [];

                // Sort by date (newest first)
                documents.sort((a, b) => {
                    const dateA = new Date(a.upload_date || a.created_at || 0);
                    const dateB = new Date(b.upload_date || b.created_at || 0);
                    return dateB - dateA;
                });

                // Find first document with valid cv_data
                for (const doc of documents) {
                    const cvData = doc.cv_data;
                    if (cvData && Object.keys(cvData).length > 0 && !cvData.error) {
                        console.log('CVLoader: CV data found in document:', doc.filename || doc.file_info?.original_filename || doc.id);
                        // Handle nested personal_info structure
                        const personalInfo = cvData.personal_info || {};
                        return {
                            cvData: cvData,
                            source: 'document',
                            userInfo: {
                                full_name: personalInfo.name || cvData.name || cvData.full_name || null,
                                email: personalInfo.email || cvData.email || null
                            }
                        };
                    }
                }
            }
        } catch (err) {
            console.error('CVLoader: Error fetching documents:', err);
        }

        console.log('CVLoader: No CV data found in profile or documents.');
        return { cvData: null, source: null, userInfo: null };
    },

};
