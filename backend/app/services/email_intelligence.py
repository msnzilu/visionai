# backend/app/services/email_intelligence.py
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import re
from bson import ObjectId

from app.models.user import User, GmailAuth
from app.models.application import Application, ApplicationStatus
from app.services.gmail_service import gmail_service
from app.services.email_response_analyzer import email_response_analyzer
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
        Check a specific thread for new messages and analyze them.
        """
        thread_id = app["email_thread_id"]
        try:
            # List messages in thread
            messages = gmail_service.list_messages(auth, query=f"threadId:{thread_id}", max_results=10)
            
            if not messages:
                return

            # Get the latest message
            latest_msg_id = messages[0]["id"]
            message_detail = gmail_service.get_message(auth, latest_msg_id)
            
            # Check if this message is newer than our last check
            internal_date = int(message_detail["internalDate"]) / 1000
            msg_date = datetime.fromtimestamp(internal_date)
            
            last_email_at = app.get("last_email_at")
            if last_email_at and msg_date <= last_email_at:
                return  # No new messages
            
            # Extract email details
            headers = {h["name"]: h["value"] for h in message_detail["payload"]["headers"]}
            sender = headers.get("From", "")
            subject = headers.get("Subject", "")
            snippet = message_detail.get("snippet", "")
            
            # If sender is NOT the user (it's a reply)
            if auth.email_address and auth.email_address not in sender:
                # It's a reply!
                logger.info(f"New reply detected for app {app['_id']} from {sender}")
                
                # Analyze email using new analyzer
                analysis = await email_response_analyzer.analyze_email_response(
                    email_content=snippet,
                    email_subject=subject,
                    sender_email=sender,
                    application_id=str(app["_id"]),
                    use_ai=True
                )
                
                logger.info(
                    f"Email analysis: category={analysis.category}, "
                    f"confidence={analysis.confidence:.2f}, "
                    f"ai_used={analysis.ai_used}"
                )
                
                # Update last email timestamp
                update_data = {
                    "last_email_at": msg_date,
                    "email_status": "replied"
                }
                
                # Process analysis results if confidence is high enough
                if analysis.confidence >= email_response_analyzer.MIN_CONFIDENCE_FOR_STATUS_UPDATE and analysis.requires_action:
                    logger.info(f"Processing analysis actions for app {app['_id']}")
                    
                    # Use analyzer to update application
                    update_result = await email_response_analyzer.update_application_from_analysis(
                        application_id=str(app["_id"]),
                        analysis_result=analysis,
                        user_id=app["user_id"]
                    )
                    
                    if update_result.success:
                        logger.info(
                            f"Successfully updated application {app['_id']}: "
                            f"{', '.join(update_result.actions_taken)}"
                        )
                    else:
                        logger.error(
                            f"Failed to update application {app['_id']}: "
                            f"{update_result.error_message}"
                        )
                else:
                    # Low confidence or no action required, just update timestamp
                    logger.info(
                        f"Low confidence ({analysis.confidence:.2f}) or no action required "
                        f"for app {app['_id']}, updating timestamp only"
                    )
                    await collection.update_one(
                        {"_id": app["_id"]},
                        {"$set": update_data}
                    )

        except Exception as e:
            logger.error(f"Error checking thread {thread_id}: {e}")
