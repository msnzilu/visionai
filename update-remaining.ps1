# Update remaining admin pages with reusable sidebar
$pages = @("subscriptions.html", "settings.html", "referrals.html", "applications.html")

foreach ($page in $pages) {
    $filePath = "g:\Desktop\visionai\frontend\admin\$page"
    Write-Host "Processing $page..."
    
    # Read file
    $content = Get-Content $filePath -Raw
    
    # Replace hardcoded sidebar - use regex to match the entire aside block
    $pattern = '(?s)<aside class="w-64 bg-gray-900.*?</aside>'
    $replacement = '<div id="admin-sidebar"></div>'
    $content = $content -replace $pattern, $replacement
    
    # Add sidebar script if not present
    if ($content -notmatch 'admin-sidebar\.js') {
        $content = $content -replace '(<script src="../assets/js/main\.js">)', ('<script src="assets/js/admin-sidebar.js"></script>' + "`r`n    " + '$1')
    }
    
    # Write back
    Set-Content $filePath -Value $content -NoNewline
    Write-Host "Done: $page"
}

Write-Host "`nAll pages updated!"
