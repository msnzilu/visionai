# PowerShell script to replace hardcoded sidebars with reusable component
$pages = @("tickets.html", "subscriptions.html", "settings.html", "referrals.html", "applications.html")

foreach ($page in $pages) {
    $filePath = "g:\Desktop\visionai\frontend\admin\$page"
    Write-Host "Processing $page..."
    
    # Read file
    $content = Get-Content $filePath -Raw
    
    # Replace hardcoded sidebar with reusable component
    $content = $content -replace '(?s)<aside class="w-64 bg-gray-900.*?</aside>', '<div id="admin-sidebar"></div>'
    
    # Add sidebar script if not present
    if ($content -notmatch 'admin-sidebar\.js') {
        $content = $content -replace '(<script src="../assets/js/main\.js">)', '<script src="assets/js/admin-sidebar.js"></script>`r`n    $1'
    }
    
    # Write back
    Set-Content $filePath -Value $content -NoNewline
    Write-Host "✓ $page updated"
}

Write-Host "`nAll pages updated with reusable sidebar component!"
