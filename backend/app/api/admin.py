from fastapi import APIRouter, Depends, HTTPException, Query
from app.api.deps import require_admin
from app.database import get_database
from app.models.user import UserResponse, SubscriptionTier
from app.models.subscription import SubscriptionStats
from typing import List, Optional
from datetime import datetime, timedelta
from bson import ObjectId

router = APIRouter()

# Add imports for login logic
from pydantic import BaseModel, EmailStr
from app.core.security import verify_password, create_access_token
from app.core.config import settings

class AdminLogin(BaseModel):
    email: EmailStr
    password: str

@router.post("/login")
async def admin_login(
    login_data: AdminLogin,
    db = Depends(get_database)
):
    """Admin login endpoint"""
    try:
        # Find user
        user = await db.users.find_one({"email": login_data.email})
        
        # Verify credentials
        if not user or not verify_password(login_data.password, user["password"]):
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )
            
        # Strict Admin Check
        if user.get("role") != "admin":
            raise HTTPException(
                status_code=403,
                detail="Access denied. Admin privileges required."
            )
            
        # Create access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            str(user["_id"]), 
            expires_delta=access_token_expires
        )
        
        # Prepare response
        user_response = {
            "id": str(user["_id"]),
            "email": user["email"],
            "first_name": user.get("first_name", ""),
            "last_name": user.get("last_name", ""),
            "role": user.get("role"),
            "subscription_tier": user.get("subscription_tier", "free")
        }
        
        return {
            "success": True,
            "message": "Admin login successful",
            "data": {
                "access_token": access_token,
                "token_type": "bearer",
                "user": user_response
            }
        }
        
    except HTTPException as he:
        # Re-raise HTTP exceptions
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Login failed: {str(e)}"
        )


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
        "pages": (total + limit - 1) # limit
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

# ==================== NEW ADMIN ENDPOINTS ====================

@router.get("/documents")
async def list_all_documents(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    current_admin = Depends(require_admin),
    db = Depends(get_database)
):
    """List all documents for admin"""
    query = {}
    if search:
        query["$or"] = [
            {"file_info.original_filename": {"$regex": search, "$options": "i"}},
            {"document_type": {"$regex": search, "$options": "i"}}
        ]
        
    skip = (page - 1) * limit
    
    total = await db.documents.count_documents(query)
    
    cursor = db.documents.find(query).sort("created_at", -1).skip(skip).limit(limit)
    documents = await cursor.to_list(length=limit)
    
    # Enhance with user email
    for doc in documents:
        doc["id"] = str(doc.pop("_id"))
        if "user_id" in doc:
            user = await db.users.find_one({"_id": ObjectId(doc["user_id"])})
            if user:
                doc["user_email"] = user.get("email")
                doc["user_name"] = f"{user.get('first_name', '')} {user.get('last_name', '')}"
                
    return {
        "documents": documents,
        "total": total,
        "page": page,
        "pages": (total + limit - 1) # limit
    }

@router.delete("/documents/{document_id}")
async def delete_document_admin(
    document_id: str,
    current_admin = Depends(require_admin),
    db = Depends(get_database)
):
    """Admin delete document"""
    try:
        # Use document service if possible to handle file cleanup, 
        # but for now direct DB delete + standard service likely safer if available.
        # We'll stick to DB delete for simple admin action or try to reuse service logic.
        # Since we don't have the user_id easily for the service call without fetching,
        # we'll fetch first.
        
        doc = await db.documents.find_one({"_id": ObjectId(document_id)})
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
            
        # We should ideally delete the physical file too.
        # For this implementation, we will perform a soft delete or just DB delete.
        # Real implementation should cleanup S3/Local storage.
        
        await db.documents.delete_one({"_id": ObjectId(document_id)})
        
        return {"message": "Document deleted successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/applications")
async def list_all_applications(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[str] = None,
    current_admin = Depends(require_admin),
    db = Depends(get_database)
):
    """List all applications for admin"""
    query = {}
    if status and status != 'all':
        query["status"] = status
        
    skip = (page - 1) * limit
    total = await db.applications.count_documents(query)
    
    cursor = db.applications.find(query).sort("created_at", -1).skip(skip).limit(limit)
    apps = await cursor.to_list(length=limit)
    
    for app in apps:
        app["id"] = str(app.pop("_id"))
        if "user_id" in app:
            user = await db.users.find_one({"_id": ObjectId(app["user_id"])})
            if user:
                app["user_email"] = user.get("email")

    return {
        "applications": apps,
        "total": total,
        "page": page,
        "pages": (total + limit - 1) # limit
    }

@router.get("/referrals")
async def list_all_referrals(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    current_admin = Depends(require_admin),
    db = Depends(get_database)
):
    """List all referrals for admin"""
    skip = (page - 1) * limit
    total = await db.referrals.count_documents({})
    
    cursor = db.referrals.find({}).sort("referred_at", -1).skip(skip).limit(limit)
    refs = await cursor.to_list(length=limit)
    
    for ref in refs:
        ref["id"] = str(ref.pop("_id"))
        # Enhance with referrer info
        if "referrer_user_id" in ref:
            referrer = await db.users.find_one({"_id": ObjectId(ref["referrer_user_id"])})
            if referrer:
                 ref["referrer_email"] = referrer.get("email")
                 
    return {
        "referrals": refs,
        "total": total,
        "page": page,
        "pages": (total + limit - 1) 
    }
