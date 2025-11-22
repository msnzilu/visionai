# Script to update jobs.js loadJobsFromDB function
# This script modifies the function to load all jobs instead of just saved jobs

$filePath = "g:\Desktop\visionai\frontend\assets\js\pages\jobs.js"
$content = Get-Content $filePath -Raw

# Define the old function
$oldFunction = @'
async function loadJobsFromDB() {
    try {
        showLoading();

        // First, try to load user's saved jobs
        const savedResponse = await fetch(`${API_BASE_URL}/api/v1/jobs/saved/me?page=1&size=20`, {
            headers: {
                'Authorization': `Bearer ${CVision.Utils.getToken()}`
            }
        });

        if (savedResponse.ok) {
            const savedJobs = await savedResponse.json();
            currentJobs = savedJobs || [];

            document.getElementById('loadingState').classList.add('hidden');

            if (currentJobs.length === 0) {
                // Show message encouraging user to search
                document.getElementById('resultsCount').textContent = 'No saved jobs yet. Search for jobs to get started!';
                showEmptyStateWithSearchPrompt();
            } else {
                displayJobs(currentJobs);
                updateResultsCount(currentJobs.length, currentJobs.length);
                document.getElementById('resultsCount').textContent = `Showing ${currentJobs.length} saved job${currentJobs.length !== 1 ? 's' : ''}`;
                document.getElementById('pagination').classList.add('hidden');
            }
        } else {
            throw new Error('Failed to load saved jobs');
        }
    } catch (error) {
        console.error('Error loading jobs:', error);
        document.getElementById('loadingState').classList.add('hidden');
        showEmptyStateWithSearchPrompt();
    }
}
'@

# Define the new function
$newFunction = @'
async function loadJobsFromDB() {
    try {
        showLoading();

        // Load recent jobs from database (browse all)
        const response = await fetch(`${API_BASE_URL}/api/v1/jobs/search`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${CVision.Utils.getToken()}`
            },
            body: JSON.stringify({
                page: 1,
                size: 20,
                sort_by: 'created_at',
                sort_order: 'desc'
            })
        });

        if (response.ok) {
            const data = await response.json();
            currentJobs = data.jobs || [];

            document.getElementById('loadingState').classList.add('hidden');

            if (currentJobs.length === 0) {
                // Show message encouraging user to add jobs
                document.getElementById('resultsCount').textContent = 'No jobs in database yet.';
                showEmptyStateWithSearchPrompt();
            } else {
                displayJobs(currentJobs);
                updateResultsCount(data.total || currentJobs.length, currentJobs.length);
                if (data.pages > 1) {
                    updatePagination(data.page || 1, data.pages);
                }
            }
        } else {
            throw new Error('Failed to load jobs');
        }
    } catch (error) {
        console.error('Error loading jobs:', error);
        document.getElementById('loadingState').classList.add('hidden');
        showEmptyStateWithSearchPrompt();
    }
}
'@

# Replace the function
$newContent = $content -replace [regex]::Escape($oldFunction), $newFunction

# Write back to file
Set-Content -Path $filePath -Value $newContent -NoNewline

Write-Host "Successfully updated loadJobsFromDB function in jobs.js"
