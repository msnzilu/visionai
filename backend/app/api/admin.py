from fastapi import APIRouter, Depends, HTTPException, Query
from app.api.deps import require_admin
from app.database import get_database
from app.models.user import UserResponse, SubscriptionTier
from app.models.subscription import SubscriptionStats
from typing import List, Optional
from datetime import datetime, timedelta
from bson import ObjectId

router = APIRouter()

@router.get("/stats")
async def get_platform_stats(
    current_admin = Depends(require_admin),
    db = Depends(get_database)
):
    """Platform statistics"""
    
    total_users = await db.users.count_documents({})
    active_users = await db.users.count_documents({"is_active": True})
    total_documents = await db.documents.count_documents({})
    
    # Users by tier
    pipeline = [
        {"$group": {"_id": "$subscription_tier", "count": {"$sum": 1}}}
    ]
    tier_counts = await db.users.aggregate(pipeline).to_list(None)
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "total_documents": total_documents,
        "users_by_tier": {item["_id"]: item["count"] for item in tier_counts}
    }

@router.get("/users")
async def list_users(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    tier: Optional[SubscriptionTier] = None,
    is_active: Optional[bool] = None,
    current_admin = Depends(require_admin),
    db = Depends(get_database)
):
    """List all users with filters"""
    
    query = {}
    
    if search:
        query["$or"] = [
            {"email": {"$regex": search, "$options": "i"}},
            {"first_name": {"$regex": search, "$options": "i"}},
            {"last_name": {"$regex": search, "$options": "i"}}
        ]
    
    if tier:
        query["subscription_tier"] = tier
    
    if is_active is not None:
        query["is_active"] = is_active
    
    skip = (page - 1) * limit
    
    users = await db.users.find(query, {"password": 0})\
        .skip(skip)\
        .limit(limit)\
        .sort("created_at", -1)\
        .to_list(None)
    
    total = await db.users.count_documents(query)
    
    for user in users:
        user["id"] = str(user.pop("_id"))
    
    return {
        "users": users,
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit
    }

@router.get("/users/{user_id}")
async def get_user(
    user_id: str,
    current_admin = Depends(require_admin),
    db = Depends(get_database)
):
    """Get single user details"""
    from bson import ObjectId
    
    try:
        user = await db.users.find_one({"_id": ObjectId(user_id)}, {"password": 0})
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user["id"] = str(user.pop("_id"))
        
        # Get user's documents count
        doc_count = await db.documents.count_documents({"user_id": user_id})
        user["document_count"] = doc_count
        
        return user
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/users/{user_id}/status")
async def update_user_status(
    user_id: str,
    is_active: bool,
    current_admin = Depends(require_admin),
    db = Depends(get_database)
):
    """Toggle user active status"""
    
    result = await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"is_active": is_active, "updated_at": datetime.utcnow()}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": f"User {'activated' if is_active else 'deactivated'}"}

@router.patch("/users/{user_id}/tier")
async def update_user_tier(
    user_id: str,
    tier: SubscriptionTier,
    current_admin = Depends(require_admin),
    db = Depends(get_database)
):
    """Update user subscription tier"""
    
    result = await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"subscription_tier": tier, "updated_at": datetime.utcnow()}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "Subscription tier updated"}

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_admin = Depends(require_admin),
    db = Depends(get_database)
):
    """Delete user and all associated data"""
    
    # Delete documents
    await db.documents.delete_many({"user_id": user_id})
    
    # Delete applications
    await db.applications.delete_many({"user_id": user_id})
    
    # Delete user
    result = await db.users.delete_one({"_id": ObjectId(user_id)})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "User deleted"}

@router.get("/analytics/registrations")
async def get_registration_analytics(
    days: int = Query(30, ge=1, le=365),
    current_admin = Depends(require_admin),
    db = Depends(get_database)
):
    """Get daily registration counts"""
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    pipeline = [
        {"$match": {"created_at": {"$gte": start_date}}},
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}},
            "count": {"$sum": 1}
        }},
        {"$sort": {"_id": 1}}
    ]
    
    results = await db.users.aggregate(pipeline).to_list(None)
    
    return {
        "labels": [r["_id"] for r in results],
        "data": [r["count"] for r in results]
    }

@router.get("/analytics/uploads")
async def get_upload_analytics(
    days: int = Query(30, ge=1, le=365),
    current_admin = Depends(require_admin),
    db = Depends(get_database)
):
    """Get daily document upload counts"""
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    pipeline = [
        {"$match": {"created_at": {"$gte": start_date}}},
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}},
            "count": {"$sum": 1}
        }},
        {"$sort": {"_id": 1}}
    ]
    
    results = await db.documents.aggregate(pipeline).to_list(None)
    
    return {
        "labels": [r["_id"] for r in results],
        "data": [r["count"] for r in results]
    }