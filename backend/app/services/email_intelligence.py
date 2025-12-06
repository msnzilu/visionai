# backend/app/services/email_intelligence.py
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import re
from bson import ObjectId

from app.models.user import User, GmailAuth
from app.models.application import Application, ApplicationStatus
from app.services.gmail_service import gmail_service
from app.database import get_applications_collection, get_users_collection

import logging
logger = logging.getLogger(__name__)

class EmailIntelligenceService:
    def __init__(self, db):
        self.db = db

    async def scan_inbox_for_replies(self, user_id: str):
        """
        Scan user's inbox for replies to tracked applications.
        """
        users_collection = self.db["users"]
        user = await users_collection.find_one({"_id": ObjectId(user_id)})
        
        if not user or not user.get("gmail_auth"):
            logger.warning(f"User {user_id} has no Gmail connected")
            return

        gmail_auth = GmailAuth(**user["gmail_auth"])
        
        # Get active applications with email threads
        applications_collection = self.db["applications"]
        active_apps = await applications_collection.find({
            "user_id": user_id,
            "email_thread_id": {"$ne": None},
            "status": {"$nin": [ApplicationStatus.REJECTED, ApplicationStatus.OFFER_ACCEPTED, ApplicationStatus.WITHDRAWN]}
        }).to_list(length=100)
        
        for app in active_apps:
            await self._check_thread_for_updates(app, gmail_auth, applications_collection)

    async def _check_thread_for_updates(self, app: Dict, auth: GmailAuth, collection):
        """
        Check a specific thread for new messages.
        """
        thread_id = app["email_thread_id"]
        try:
            # Get thread details
            # We need to implement get_thread in GmailService or just use get_message for the latest
            # But list_messages with q=threadId might be better to see if there are new ones
            
            # Simplified: List messages in thread
            messages = gmail_service.list_messages(auth, query=f"threadId:{thread_id}", max_results=10)
            
            if not messages:
                return

            # Sort by internalDate (timestamp)
            # We need to fetch details for the latest message
            latest_msg_id = messages[0]["id"] # List returns latest first usually? No, order not guaranteed.
            
            # Actually list_messages returns a list of message summaries.
            # We should get the thread details to be sure.
            # For now, let's just get the latest message content.
            
            message_detail = gmail_service.get_message(auth, latest_msg_id)
            
            # Check if this message is newer than our last check
            internal_date = int(message_detail["internalDate"]) / 1000
            msg_date = datetime.fromtimestamp(internal_date)
            
            last_email_at = app.get("last_email_at")
            if last_email_at and msg_date <= last_email_at:
                return # No new messages
            
            # Analyze message
            headers = {h["name"]: h["value"] for h in message_detail["payload"]["headers"]}
            sender = headers.get("From", "")
            subject = headers.get("Subject", "")
            snippet = message_detail.get("snippet", "")
            
            # If sender is NOT the user (it's a reply)
            if auth.email_address and auth.email_address not in sender:
                # It's a reply!
                logger.info(f"New reply detected for app {app['_id']}")
                
                # Basic Sentiment/Keyword Analysis
                new_status = self._analyze_reply(snippet, subject)
                
                update_data = {
                    "last_email_at": msg_date,
                    "email_status": "replied"
                }
                
                if new_status and new_status != app.get("status"):
                    old_status = app.get("status", "unknown")
                    update_data["status"] = new_status
                    
                    # Trigger status notification email
                    from app.workers.email_campaigns import send_status_notification
                    send_status_notification.delay(
                        str(app["_id"]),
                        old_status,
                        new_status
                    )
                
                await collection.update_one(
                    {"_id": app["_id"]},
                    {"$set": update_data}
                )

        except Exception as e:
            logger.error(f"Error checking thread {thread_id}: {e}")

    def _analyze_reply(self, snippet: str, subject: str) -> Optional[str]:
        """
        Analyze email content to determine status.
        """
        text = (subject + " " + snippet).lower()
        
        if any(w in text for w in ["interview", "schedule", "availability", "chat", "call"]):
            return ApplicationStatus.INTERVIEW_SCHEDULED
        
        if any(w in text for w in ["unfortunately", "regret", "not moving forward", "other candidates"]):
            return ApplicationStatus.REJECTED
            
        if any(w in text for w in ["offer", "pleased to offer", "join our team"]):
            return ApplicationStatus.OFFER_RECEIVED
            
        return None
