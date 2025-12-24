from pymongo import MongoClient
from datetime import datetime, timedelta
import os

MONGODB_URL = "mongodb://localhost:27017"
DATABASE_NAME = "vision_ai"

def check_new_applications():
    client = MongoClient(MONGODB_URL)
    db = client[DATABASE_NAME]
    
    # Check for applications created in the last hour
    hour_ago = datetime.utcnow() - timedelta(hours=1)
    
    new_apps_count = db.applications.count_documents({"created_at": {"$gte": hour_ago}})
    total_apps_count = db.applications.count_documents({})
    
    print(f"Total applications in {DATABASE_NAME}: {total_apps_count}")
    print(f"Applications created in the last hour: {new_apps_count}")
    
    if new_apps_count > 0:
        print("\nNewest Applications:")
        apps = list(db.applications.find({"created_at": {"$gte": hour_ago}}).sort("created_at", -1))
        for app in apps:
            print(f"ID: {app.get('_id')}")
            print(f"  Title: {app.get('job_title')}")
            print(f"  Status: {app.get('status')}")
            print(f"  Email Status: {app.get('email_status')}")
            print(f"  Created At: {app.get('created_at')}")
            print(f"  Recipients: {app.get('recipient_email')}")
            print("-" * 20)
    else:
        print("\nNo applications found from the last hour.")
        print("\nLast 3 applications regardless of time:")
        apps = list(db.applications.find().sort("created_at", -1).limit(3))
        for app in apps:
             print(f"ID: {app.get('_id')}, Title: {app.get('job_title')}, CreatedAt: {app.get('created_at')}")

if __name__ == "__main__":
    check_new_applications()
