# backend/app/services/email_response_analyzer.py
"""
Email Response Analyzer Service
AI-powered email classification and application status management
"""

import logging
import re
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from bson import ObjectId

from app.models.email_analysis import (
    EmailResponseCategory,
    EmailAnalysisResult,
    ApplicationUpdateResult
)
from app.models.application import ApplicationStatus, ApplicationTask, ApplicationReminder
from app.database import get_database
from app.integrations.openai_client import openai_client

logger = logging.getLogger(__name__)


class EmailResponseAnalyzer:
    """
    Analyzes email responses to job applications and determines appropriate actions
    
    Features:
    - Hybrid analysis (keyword matching + AI)
    - Confidence scoring
    - Multi-category classification
    - Automatic status updates
    - Task and reminder creation
    """
    
    # Keyword patterns for fast classification
    KEYWORD_PATTERNS = {
        EmailResponseCategory.INTERVIEW_INVITATION: {
            "keywords": [
                "schedule interview", "interview invitation", "would you be available",
                "interview with", "speak with you", "discuss the position",
                "set up a time", "arrange a call", "interview opportunity",
                "next steps would be", "move forward with an interview"
            ],
            "confidence": 0.9
        },
        EmailResponseCategory.REJECTION: {
            "keywords": [
                "unfortunately", "regret to inform", "not moving forward",
                "other candidates", "decided to pursue", "not selected",
                "will not be proceeding", "chosen to move forward with other",
                "not the right fit", "position has been filled"
            ],
            "confidence": 0.95
        },
        EmailResponseCategory.OFFER: {
            "keywords": [
                "pleased to offer", "offer letter", "extend an offer",
                "congratulations", "offer of employment", "join our team",
                "accept this offer", "offer package", "compensation package"
            ],
            "confidence": 0.95
        },
        EmailResponseCategory.INFORMATION_REQUEST: {
            "keywords": [
                "additional information", "please provide", "need more details",
                "could you send", "require documentation", "clarification needed",
                "please submit", "missing information", "complete your application"
            ],
            "confidence": 0.85
        },
        EmailResponseCategory.FOLLOW_UP_REQUIRED: {
            "keywords": [
                "following up", "checking in", "status update",
                "haven't heard", "still interested", "update on your application"
            ],
            "confidence": 0.7
        },
        EmailResponseCategory.ACKNOWLEDGMENT: {
            "keywords": [
                "received your application", "thank you for applying",
                "application has been received", "reviewing your application",
                "under review", "application is being considered"
            ],
            "confidence": 0.9
        },
        EmailResponseCategory.SCHEDULING_REQUEST: {
            "keywords": [
                "confirm your availability", "schedule a time", "what times work",
                "available for", "pick a time", "calendar invite",
                "meeting request", "schedule our call"
            ],
            "confidence": 0.85
        }
    }
    
    # Confidence thresholds
    MIN_CONFIDENCE_FOR_STATUS_UPDATE = 0.7
    MIN_CONFIDENCE_FOR_AI_VERIFICATION = 0.7
    
    def __init__(self):
        self.openai_client = openai_client
    
    async def analyze_email_response(
        self,
        email_content: str,
        email_subject: str,
        sender_email: str,
        application_id: Optional[str] = None,
        use_ai: bool = True
    ) -> EmailAnalysisResult:
        """
        Analyze email response and classify it
        
        Args:
            email_content: Email body text
            email_subject: Email subject line
            sender_email: Sender's email address
            application_id: Optional application ID for context
            use_ai: Whether to use AI for analysis
            
        Returns:
            EmailAnalysisResult with classification and recommendations
        """
        try:
            # Combine subject and content for analysis
            full_text = f"{email_subject} {email_content}"
            
            # Step 1: Keyword-based analysis (fast path)
            keyword_result = self._analyze_with_keywords(full_text)
            
            # Step 2: Decide if AI verification is needed
            if keyword_result.confidence >= 0.9:
                # High confidence, use keyword result
                logger.info(
                    f"High confidence keyword match: {keyword_result.category} "
                    f"({keyword_result.confidence:.2f})"
                )
                return keyword_result
            
            elif keyword_result.confidence >= self.MIN_CONFIDENCE_FOR_AI_VERIFICATION and use_ai:
                # Medium confidence, verify with AI
                logger.info(
                    f"Verifying keyword result with AI: {keyword_result.category} "
                    f"({keyword_result.confidence:.2f})"
                )
                ai_result = await self._analyze_with_ai(
                    email_content, email_subject, sender_email
                )
                
                # Use AI result if more confident
                if ai_result.confidence > keyword_result.confidence:
                    return ai_result
                return keyword_result
            
            elif use_ai:
                # Low confidence or unknown, use AI
                logger.info("Using AI for low-confidence email analysis")
                return await self._analyze_with_ai(
                    email_content, email_subject, sender_email
                )
            
            else:
                # AI disabled, return keyword result
                return keyword_result
                
        except Exception as e:
            logger.error(f"Error analyzing email response: {e}")
            return EmailAnalysisResult(
                category=EmailResponseCategory.UNKNOWN,
                confidence=0.0,
                requires_action=False,
                ai_used=False,
                error_message=str(e)
            )
    
    def _analyze_with_keywords(self, text: str) -> EmailAnalysisResult:
        """
        Analyze email using keyword pattern matching
        
        Args:
            text: Combined email subject and content
            
        Returns:
            EmailAnalysisResult with keyword-based classification
        """
        text_lower = text.lower()
        best_match = None
        best_confidence = 0.0
        matched_keywords = []
        
        # Check each category's keywords
        for category, pattern_data in self.KEYWORD_PATTERNS.items():
            keywords = pattern_data["keywords"]
            base_confidence = pattern_data["confidence"]
            
            # Count keyword matches
            matches = [kw for kw in keywords if kw in text_lower]
            
            if matches:
                # Calculate confidence based on number of matches
                match_ratio = len(matches) / len(keywords)
                confidence = base_confidence * (0.7 + 0.3 * match_ratio)
                
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_match = category
                    matched_keywords = matches
        
        # Determine suggested status and actions
        if best_match:
            suggested_status, action_type, action_details = self._determine_actions(
                best_match, best_confidence
            )
            
            return EmailAnalysisResult(
                category=best_match,
                confidence=best_confidence,
                suggested_status=suggested_status,
                requires_action=best_confidence >= self.MIN_CONFIDENCE_FOR_STATUS_UPDATE,
                action_type=action_type,
                action_details=action_details,
                keywords_matched=matched_keywords,
                ai_used=False
            )
        
        # No match found
        return EmailAnalysisResult(
            category=EmailResponseCategory.UNKNOWN,
            confidence=0.0,
            requires_action=False,
            ai_used=False
        )
    
    async def _analyze_with_ai(
        self,
        email_content: str,
        email_subject: str,
        sender_email: str
    ) -> EmailAnalysisResult:
        """
        Analyze email using AI (GPT-4)
        
        Args:
            email_content: Email body text
            email_subject: Email subject line
            sender_email: Sender's email address
            
        Returns:
            EmailAnalysisResult with AI-based classification
        """
        try:
            # Call OpenAI for analysis
            ai_response = await self.openai_client.analyze_email_response(
                email_content=email_content,
                email_subject=email_subject,
                context={"sender_email": sender_email}
            )
            
            # Parse AI response
            category_str = ai_response.get("category", "unknown")
            try:
                category = EmailResponseCategory(category_str)
            except ValueError:
                category = EmailResponseCategory.UNKNOWN
            
            confidence = float(ai_response.get("confidence", 0.5))
            reasoning = ai_response.get("reasoning", "")
            extracted_info = ai_response.get("key_information", {})
            
            # Determine actions
            suggested_status, action_type, action_details = self._determine_actions(
                category, confidence
            )
            
            return EmailAnalysisResult(
                category=category,
                confidence=confidence,
                suggested_status=suggested_status,
                requires_action=confidence >= self.MIN_CONFIDENCE_FOR_STATUS_UPDATE,
                action_type=action_type,
                action_details=action_details,
                ai_reasoning=reasoning,
                ai_used=True,
                extracted_info=extracted_info
            )
            
        except Exception as e:
            logger.error(f"Error in AI analysis: {e}")
            # Fallback to unknown
            return EmailAnalysisResult(
                category=EmailResponseCategory.UNKNOWN,
                confidence=0.0,
                requires_action=False,
                ai_used=True,
                ai_reasoning=f"AI analysis failed: {str(e)}"
            )
    
    def _determine_actions(
        self,
        category: EmailResponseCategory,
        confidence: float
    ) -> tuple[Optional[ApplicationStatus], Optional[str], Dict[str, Any]]:
        """
        Determine what actions to take based on email category
        
        Args:
            category: Email response category
            confidence: Confidence score
            
        Returns:
            Tuple of (suggested_status, action_type, action_details)
        """
        action_map = {
            EmailResponseCategory.INTERVIEW_INVITATION: (
                ApplicationStatus.INTERVIEW_SCHEDULED,
                "update_status",
                {"priority": "high", "notification": True}
            ),
            EmailResponseCategory.REJECTION: (
                ApplicationStatus.REJECTED,
                "update_status",
                {"priority": "high", "notification": True}
            ),
            EmailResponseCategory.OFFER: (
                ApplicationStatus.OFFER_RECEIVED,
                "update_status",
                {"priority": "urgent", "notification": True}
            ),
            EmailResponseCategory.INFORMATION_REQUEST: (
                None,
                "create_task",
                {
                    "task_title": "Provide additional information to employer",
                    "priority": "high",
                    "due_days": 3
                }
            ),
            EmailResponseCategory.FOLLOW_UP_REQUIRED: (
                None,
                "create_reminder",
                {
                    "reminder_title": "Follow up on application",
                    "remind_days": 7
                }
            ),
            EmailResponseCategory.ACKNOWLEDGMENT: (
                ApplicationStatus.UNDER_REVIEW,
                "update_status",
                {"priority": "medium", "notification": False}
            ),
            EmailResponseCategory.SCHEDULING_REQUEST: (
                None,
                "create_task",
                {
                    "task_title": "Confirm interview availability",
                    "priority": "urgent",
                    "due_days": 1
                }
            ),
            EmailResponseCategory.UNKNOWN: (
                None,
                None,
                {}
            )
        }
        
        return action_map.get(category, (None, None, {}))
    
    async def update_application_from_analysis(
        self,
        application_id: str,
        analysis_result: EmailAnalysisResult,
        user_id: str
    ) -> ApplicationUpdateResult:
        """
        Update application based on email analysis results
        
        Args:
            application_id: Application ID to update
            analysis_result: Analysis result from analyze_email_response
            user_id: User ID for authorization
            
        Returns:
            ApplicationUpdateResult with update details
        """
        try:
            db = await get_database()
            applications_collection = db["applications"]
            
            # Get current application
            app = await applications_collection.find_one({
                "_id": ObjectId(application_id),
                "user_id": user_id
            })
            
            if not app:
                return ApplicationUpdateResult(
                    success=False,
                    application_id=application_id,
                    error_message="Application not found"
                )
            
            old_status = app.get("status")
            actions_taken = []
            update_data = {}
            
            # Add analysis to history
            analysis_history_entry = {
                "analyzed_at": analysis_result.analyzed_at,
                "category": analysis_result.category.value,
                "confidence": analysis_result.confidence,
                "action_taken": analysis_result.action_type,
                "ai_used": analysis_result.ai_used
            }
            
            update_data["$push"] = {
                "email_analysis_history": analysis_history_entry
            }
            update_data["$set"] = {
                "last_email_analysis": analysis_history_entry
            }
            
            # Process based on action type
            if analysis_result.action_type == "update_status" and analysis_result.suggested_status:
                # Update status
                new_status = analysis_result.suggested_status.value
                update_data["$set"]["status"] = new_status
                actions_taken.append(f"Updated status to {new_status}")
                
                # Create timeline event
                timeline_event = {
                    "event_type": "status_change",
                    "status_from": old_status,
                    "status_to": new_status,
                    "description": f"Status updated based on email analysis: {analysis_result.category.value}",
                    "details": {
                        "confidence": analysis_result.confidence,
                        "ai_used": analysis_result.ai_used,
                        "reasoning": analysis_result.ai_reasoning
                    },
                    "created_by": "system",
                    "timestamp": datetime.utcnow(),
                    "is_milestone": True
                }
                
                if "$push" not in update_data:
                    update_data["$push"] = {}
                update_data["$push"]["timeline"] = timeline_event
                actions_taken.append("Created timeline event")
                
                # Send notification if required
                if analysis_result.action_details.get("notification"):
                    # Trigger notification (will be handled by email campaigns worker)
                    from app.workers.email_campaigns import send_status_notification
                    send_status_notification.delay(
                        application_id,
                        old_status,
                        new_status
                    )
                    actions_taken.append("Notification queued")
            
            elif analysis_result.action_type == "create_task":
                # Create task
                task_details = analysis_result.action_details
                task = {
                    "title": task_details.get("task_title", "Action required"),
                    "description": f"Based on email: {analysis_result.category.value}",
                    "priority": task_details.get("priority", "medium"),
                    "due_date": datetime.utcnow() + timedelta(days=task_details.get("due_days", 3)),
                    "is_completed": False,
                    "category": "follow_up",
                    "created_at": datetime.utcnow()
                }
                
                if "$push" not in update_data:
                    update_data["$push"] = {}
                update_data["$push"]["tasks"] = task
                actions_taken.append("Created task")
            
            elif analysis_result.action_type == "create_reminder":
                # Create reminder
                reminder_details = analysis_result.action_details
                reminder = {
                    "title": reminder_details.get("reminder_title", "Follow up required"),
                    "description": f"Based on email: {analysis_result.category.value}",
                    "remind_at": datetime.utcnow() + timedelta(days=reminder_details.get("remind_days", 7)),
                    "is_sent": False,
                    "reminder_type": "email",
                    "created_at": datetime.utcnow()
                }
                
                if "$push" not in update_data:
                    update_data["$push"] = {}
                update_data["$push"]["reminders"] = reminder
                actions_taken.append("Created reminder")
            
            # Update application
            if update_data:
                await applications_collection.update_one(
                    {"_id": ObjectId(application_id)},
                    update_data
                )
            
            logger.info(
                f"Updated application {application_id}: {', '.join(actions_taken)}"
            )
            
            return ApplicationUpdateResult(
                success=True,
                application_id=application_id,
                old_status=ApplicationStatus(old_status) if old_status else None,
                new_status=analysis_result.suggested_status,
                actions_taken=actions_taken,
                timeline_event_created="timeline" in update_data.get("$push", {}),
                notification_sent=analysis_result.action_details.get("notification", False),
                task_created=analysis_result.action_type == "create_task",
                reminder_created=analysis_result.action_type == "create_reminder"
            )
            
        except Exception as e:
            logger.error(f"Error updating application from analysis: {e}")
            return ApplicationUpdateResult(
                success=False,
                application_id=application_id,
                error_message=str(e)
            )


# Singleton instance
email_response_analyzer = EmailResponseAnalyzer()
