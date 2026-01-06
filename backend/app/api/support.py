from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, EmailStr
from typing import Optional
import logging

from app.services.emails.email_service import email_service
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

class ContactRequest(BaseModel):
    name: str
    email: EmailStr
    subject: str
    category: Optional[str] = "General"
    message: str

@router.post("/contact")
async def contact_form_submission(
    request: ContactRequest,
    background_tasks: BackgroundTasks
):
    """
    Handle contact form submissions by sending an email to support
    """
    try:
        # Prepare email template context
        template_body = {
            "name": request.name,
            "email": request.email,
            "category": request.category,
            "subject": request.subject,
            "message": request.message
        }

        # Send email in background to avoid blocking the response
        background_tasks.add_task(
            email_service.send_email,
            subject=f"Contact Form: {request.subject}",
            recipients=[settings.SUPPORT_EMAIL],
            body="",  # Use template
            subtype="html",
            template_name="contact_form.html",
            template_body=template_body,
            reply_to=request.email
        )

        return {"success": True, "message": "Thank you for your message! Our support team will get back to you within 24 hours."}

    except Exception as e:
        logger.error(f"Error processing contact form: {e}")
        raise HTTPException(
            status_code=500,
            detail="There was an error processing your request. Please try again later."
        )
