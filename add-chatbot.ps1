# PowerShell script to add chatbot to all authenticated pages
$pages = @(
    "g:\Desktop\visionai\frontend\pages\notifications.html",
    "g:\Desktop\visionai\frontend\pages\profile.html",
    "g:\Desktop\visionai\frontend\pages\referrals.html",
    "g:\Desktop\visionai\frontend\pages\documents.html",
    "g:\Desktop\visionai\frontend\pages\subscription.html",
    "g:\Desktop\visionai\frontend\pages\cv-analysis.html",
    "g:\Desktop\visionai\frontend\pages\applications.html",
    "g:\Desktop\visionai\frontend\pages\auto-apply.html"
)

$chatbotCode = @"

    <!-- Chatbot -->
    <link rel="stylesheet" href="../assets/css/chatbot.css">
    <script src="../assets/js/chatbot.js"></script>
"@

foreach ($page in $pages) {
    if (Test-Path $page) {
        $content = Get-Content $page -Raw
        if ($content -notmatch "chatbot\.js") {
            $content = $content -replace '(</body>)', "$chatbotCode`r`n`$1"
            Set-Content -Path $page -Value $content -NoNewline
            Write-Host "Added chatbot to: $page"
        } else {
            Write-Host "Chatbot already exists in: $page"
        }
    }
}
