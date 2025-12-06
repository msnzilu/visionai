# Restart Celery Services - Email Automation Deployment
# Run this script to activate the new email monitoring features

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Vision.AI - Email Automation Deployment" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "📋 Stopping Celery services..." -ForegroundColor Yellow
docker-compose stop celery_worker celery_beat

Write-Host ""
Write-Host "🔄 Rebuilding Celery services..." -ForegroundColor Yellow
docker-compose build celery_worker celery_beat

Write-Host ""
Write-Host "🚀 Starting Celery services..." -ForegroundColor Green
docker-compose up -d celery_worker celery_beat

Write-Host ""
Write-Host "⏳ Waiting for services to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

Write-Host ""
Write-Host "📊 Checking service status..." -ForegroundColor Cyan
docker-compose ps celery_worker celery_beat

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "✅ Deployment Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📝 New Features Activated:" -ForegroundColor White
Write-Host "  ✓ Email monitoring (every 15-30 minutes)" -ForegroundColor Green
Write-Host "  ✓ Automatic status updates from emails" -ForegroundColor Green
Write-Host "  ✓ Async email sending with retry" -ForegroundColor Green
Write-Host "  ✓ Failed email retry (daily)" -ForegroundColor Green
Write-Host ""
Write-Host "📖 View logs:" -ForegroundColor White
Write-Host "  docker logs vision_ai_worker -f" -ForegroundColor Gray
Write-Host "  docker logs vision_ai_beat -f" -ForegroundColor Gray
Write-Host ""
Write-Host "📚 Documentation:" -ForegroundColor White
Write-Host "  docs/email_automation_implementation.md" -ForegroundColor Gray
Write-Host ""
