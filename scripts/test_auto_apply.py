#!/usr/bin/env python3
"""
Manual Test Script for Auto-Apply and Hybrid Monitoring
Run this script to quickly test the system without pytest

Usage:
    python scripts/test_auto_apply.py --user-id YOUR_USER_ID
    python scripts/test_auto_apply.py --test-monitoring --app-id APPLICATION_ID
"""

import asyncio
import argparse
import sys
import os
from datetime import datetime
from bson import ObjectId

# Add backend directory to path
backend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backend')
if os.path.exists(backend_path):
    sys.path.insert(0, backend_path)
else:
    # Try current directory
    sys.path.insert(0, '.')

try:
    from app.database import get_database
    from app.workers.auto_apply import process_auto_apply_for_user, calculate_match_score
    from app.services.automation_service import AutomationService
    from app.services.email_intelligence import EmailIntelligenceService
except ImportError as e:
    print(f"❌ Error: Cannot import required modules.")
    print(f"   Make sure you're running from the backend directory or Docker container.")
    print(f"   Error details: {e}")
    sys.exit(1)


async def test_auto_apply(user_id: str):
    """Test auto-apply for a specific user"""
    print("\n" + "="*60)
    print("🚀 TESTING AUTO-APPLY")
    print("="*60 + "\n")
    
    try:
        db = await get_database()
        
        # Get user
        print(f"📋 Fetching user: {user_id}")
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        
        if not user:
            print(f"❌ User not found: {user_id}")
            return False
        
        print(f"✅ Found user: {user.get('email')}")
        
        # Check prerequisites
        print("\n📝 Checking prerequisites...")
        
        has_cv = bool(user.get("cv_data"))
        has_gmail = bool(user.get("gmail_auth"))
        auto_enabled = user.get("preferences", {}).get("auto_apply_enabled", False)
        
        print(f"  CV Data: {'✅' if has_cv else '❌'}")
        print(f"  Gmail Connected: {'✅' if has_gmail else '❌'}")
        print(f"  Auto-Apply Enabled: {'✅' if auto_enabled else '❌'}")
        
        if not has_cv:
            print("\n⚠️  No CV data found. Please upload a CV first.")
            return False
        
        # Run auto-apply
        print("\n🎯 Running auto-apply process...")
        result = await process_auto_apply_for_user(user, db)
        
        print("\n📊 Results:")
        print(f"  Success: {result.get('success')}")
        print(f"  Applications Sent: {result.get('applications_sent', 0)}")
        
        if result.get("stats"):
            stats = result["stats"]
            print(f"\n📈 Statistics:")
            print(f"  Jobs Found: {stats.get('jobs_found', 0)}")
            print(f"  Jobs Analyzed: {stats.get('jobs_analyzed', 0)}")
            print(f"  Matches Found: {stats.get('matches_found', 0)}")
            print(f"  Daily Limit: {stats.get('daily_limit', 0)}")
            
            if stats.get('reason'):
                print(f"  Note: {stats['reason']}")
        
        return result.get("success", False)
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_monitoring(application_id: str):
    """Test hybrid monitoring for a specific application"""
    print("\n" + "="*60)
    print("🔍 TESTING HYBRID MONITORING")
    print("="*60 + "\n")
    
    try:
        db = await get_database()
        
        # Get application
        print(f"📋 Fetching application: {application_id}")
        app = await db.applications.find_one({"_id": ObjectId(application_id)})
        
        if not app:
            print(f"❌ Application not found: {application_id}")
            return False
        
        print(f"✅ Found application: {app.get('job_title')} at {app.get('company_name')}")
        
        # Get job
        job = await db.jobs.find_one({"_id": app.get("job_id")})
        if not job:
            print("❌ Associated job not found")
            return False
        
        job_url = job.get("external_url") or job.get("apply_url")
        print(f"🔗 Job URL: {job_url}")
        
        # Check browser service
        print("\n🌐 Checking browser automation service...")
        health = await AutomationService.check_automation_service_health()
        
        if health.get("healthy"):
            print("✅ Browser service is healthy")
        else:
            print(f"⚠️  Browser service issue: {health.get('error', 'Unknown')}")
        
        # Run hybrid check
        print("\n🔄 Running hybrid status check...")
        result = await AutomationService.check_application_status(
            application_id=application_id,
            user_id=str(app["user_id"]),
            job_url=job_url
        )
        
        print("\n📊 Results:")
        print(f"  Portal Status: {result.get('portal_status', 'unknown')}")
        print(f"  Email Status: {result.get('email_status', 'unknown')}")
        print(f"  Final Status: {result.get('final_status', 'unknown')}")
        
        if result.get("signals"):
            print(f"\n🎯 Signals Detected ({len(result['signals'])}):")
            for signal in result["signals"]:
                print(f"  - {signal['source']}: {signal['status']}")
                if signal.get('detail'):
                    print(f"    Detail: {signal['detail']}")
        
        # Verify database update
        updated_app = await db.applications.find_one({"_id": ObjectId(application_id)})
        if updated_app.get("last_response_check"):
            print(f"\n✅ Application updated at: {updated_app['last_response_check']}")
            print(f"   New status: {updated_app.get('status')}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_browser_service():
    """Test browser automation service connectivity"""
    print("\n" + "="*60)
    print("🌐 TESTING BROWSER SERVICE")
    print("="*60 + "\n")
    
    try:
        health = await AutomationService.check_automation_service_health()
        
        print(f"Service URL: {health.get('url')}")
        print(f"Status: {'✅ Healthy' if health.get('healthy') else '❌ Unhealthy'}")
        
        if health.get('response'):
            print(f"Response: {health['response']}")
        
        if health.get('error'):
            print(f"Error: {health['error']}")
        
        return health.get("healthy", False)
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False


async def quick_stats():
    """Show quick statistics"""
    print("\n" + "="*60)
    print("📊 QUICK STATISTICS")
    print("="*60 + "\n")
    
    try:
        db = await get_database()
        
        # Count applications
        total_apps = await db.applications.count_documents({})
        auto_apps = await db.applications.count_documents({"source": "auto_apply"})
        monitored_apps = await db.applications.count_documents({"email_monitoring_enabled": True})
        
        print(f"Total Applications: {total_apps}")
        print(f"Auto-Applied: {auto_apps}")
        print(f"Monitoring Enabled: {monitored_apps}")
        
        # Recent applications
        recent = await db.applications.find(
            {"source": "auto_apply"}
        ).sort("created_at", -1).limit(5).to_list(length=5)
        
        if recent:
            print(f"\n📝 Recent Auto-Applications:")
            for app in recent:
                print(f"  - {app.get('job_title')} at {app.get('company_name')}")
                print(f"    Status: {app.get('status')}, Created: {app.get('created_at')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Test Auto-Apply and Monitoring")
    parser.add_argument("--user-id", help="User ID for auto-apply test")
    parser.add_argument("--app-id", help="Application ID for monitoring test")
    parser.add_argument("--test-monitoring", action="store_true", help="Test monitoring")
    parser.add_argument("--test-browser", action="store_true", help="Test browser service")
    parser.add_argument("--stats", action="store_true", help="Show statistics")
    
    args = parser.parse_args()
    
    if args.test_browser:
        success = asyncio.run(test_browser_service())
        sys.exit(0 if success else 1)
    
    if args.stats:
        success = asyncio.run(quick_stats())
        sys.exit(0 if success else 1)
    
    if args.test_monitoring and args.app_id:
        success = asyncio.run(test_monitoring(args.app_id))
        sys.exit(0 if success else 1)
    
    if args.user_id:
        success = asyncio.run(test_auto_apply(args.user_id))
        sys.exit(0 if success else 1)
    
    # No args provided, show help
    parser.print_help()
    print("\n💡 Examples:")
    print("  python scripts/test_auto_apply.py --stats")
    print("  python scripts/test_auto_apply.py --test-browser")
    print("  python scripts/test_auto_apply.py --user-id 507f1f77bcf86cd799439011")
    print("  python scripts/test_auto_apply.py --test-monitoring --app-id 507f1f77bcf86cd799439012")


if __name__ == "__main__":
    main()
