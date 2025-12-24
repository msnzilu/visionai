@echo off
REM Simple MongoDB queries for testing

echo ========================================
echo Auto-Apply Quick Stats
echo ========================================
echo.

if "%1"=="" (
    echo Usage:
    echo   test.bat stats     - Show application statistics
    echo   test.bat users     - List users
    echo   test.bat apps      - List recent applications
    goto :eof
)

if "%1"=="stats" (
    echo Querying database...
    docker exec -it synovae_db_mongo mongosh visionai --quiet --eval "print('Total Applications:', db.applications.countDocuments({})); print('Auto-Applied:', db.applications.countDocuments({source: 'auto_apply'})); print('With Monitoring:', db.applications.countDocuments({email_monitoring_enabled: true}));"
    goto :eof
)

if "%1"=="users" (
    echo Querying users...
    docker exec -it synovae_db_mongo mongosh visionai --quiet --eval "db.users.find({'preferences.auto_apply_enabled': true}, {email: 1, full_name: 1}).forEach(u => print('User:', u.email, '(ID:', u._id + ')'));"
    goto :eof
)

if "%1"=="apps" (
    echo Recent applications...
    docker exec -it synovae_db_mongo mongosh visionai --quiet --eval "db.applications.find({source: 'auto_apply'}).sort({created_at: -1}).limit(5).forEach(a => print('-', a.job_title, 'at', a.company_name, '(' + a.status + ')'));"
    goto :eof
)

echo Unknown command: %1
