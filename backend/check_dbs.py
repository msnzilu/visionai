from pymongo import MongoClient
import os
from pprint import pprint

MONGODB_URL = "mongodb://localhost:27017"

def check_databases():
    client = MongoClient(MONGODB_URL)
    dbs = client.list_database_names()
    print(f"Databases: {dbs}")
    
    for db_name in ["vision_ai", "visionai"]:
        if db_name in dbs:
            db = client[db_name]
            count = db.applications.count_documents({})
            print(f"Total applications in {db_name}: {count}")
            if count > 0:
                print(f"\nLast 3 applications in {db_name}:")
                apps = list(db.applications.find().sort("created_at", -1).limit(3))
                for app in apps:
                    pprint(app)

if __name__ == "__main__":
    check_databases()
