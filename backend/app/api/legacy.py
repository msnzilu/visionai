# app/api/legacy.py
"""
Legacy endpoints to prevent 404 errors from frontend requests
"""
from fastapi import APIRouter, Depends
from app.api.deps import get_current_user

router = APIRouter()

@router.get("/support/status/")
async def support_status(current_user: dict = Depends(get_current_user)):
    return {
        "status": "active", 
        "support_tier": "premium",
        "user_id": str(current_user["_id"])
    }

@router.get("/notifications/api/unread-count/")
async def unread_count(current_user: dict = Depends(get_current_user)):
    return {"unread_count": 0}

@router.get("/support/stats/")
async def support_stats():
    return {
        "total_tickets": 0,
        "open_tickets": 0, 
        "average_response_time": "0h"
    }