# backend/app/services/email_service.py

import logging
from typing import Optional, Dict, Any

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import EmailStr

from app.core.config import settings

logger = logging.getLogger(__name__)

# Email configuration
conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
)


class EmailService:
    """Comprehensive email sending service"""

    fm = FastMail(conf)

    @classmethod
    async def send_email(
        cls,
        subject: str,
        recipients: list[str],
        body: str,
        subtype: str = "html",
        attachments: Optional[list[Any]] = None,
        template_name: Optional[str] = None,
        template_body: Optional[dict] = None,
    ) -> bool:
        """
        Send an email with optional Jinja2 template support.

        Args:
            subject (str): Email subject line.
            recipients (list[str]): List of recipient emails.
            body (str): Email body content (used if no template).
            subtype (str): Email content type, 'html' or 'plain'.
            attachments (list): List of attachments (optional).
            template_name (str): Jinja2 template filename (optional).
            template_body (dict): Context for the template (optional).

        Returns:
            bool: True if email was sent successfully, False otherwise.
        """
        try:
            message = MessageSchema(
                subject=subject,
                recipients=recipients,
                body=body if not template_name else None,
                subtype=subtype,
                attachments=attachments,
            )

            if template_name and template_body:
                await cls.fm.send_message(
                    message,
                    template_name=template_name,
                    template_body=template_body,
                )
            else:
                await cls.fm.send_message(message)

            logger.info(f"Email sent to {recipients} with subject '{subject}'")
            return True
        except Exception as e:
            logger.error(f"Failed to send email to {recipients}: {e}")
            return False

    @classmethod
    async def send_verification_email(
        cls,
        email: EmailStr,
        full_name: Optional[str],  # full name or first name to personalize email
        verification_token: str
    ) -> bool:
        """Send email verification message with personalization"""
        subject = "Verify your email address"
        verify_url = f"{settings.FRONTEND_URL}/verify-email?token={verification_token}"
        template_name = "verify_email.html"
        template_body = {
            "verify_url": verify_url,
            "email": email,
            "full_name": full_name or "",  # pass to template for greeting
            "support_email": settings.SUPPORT_EMAIL,
            "company_name": settings.COMPANY_NAME,
        }
        return await cls.send_email(
            subject=subject,
            recipients=[email],
            body="",
            template_name=template_name,
            template_body=template_body,
        )

    @classmethod
    async def send_password_reset_email(cls, email: EmailStr, reset_token: str) -> bool:
        """Send password reset email"""
        subject = "Reset your password"
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
        template_name = "reset_password.html"
        template_body = {
            "reset_url": reset_url,
            "email": email,
            "support_email": settings.SUPPORT_EMAIL,
            "company_name": settings.COMPANY_NAME,
        }
        return await cls.send_email(
            subject=subject,
            recipients=[email],
            body="",
            template_name=template_name,
            template_body=template_body,
        )

    @classmethod
    async def send_custom_notification(
        cls,
        email: EmailStr,
        subject: str,
        message_body: str,
    ) -> bool:
        """Send a generic notification email"""
        return await cls.send_email(
            subject=subject,
            recipients=[email],
            body=message_body,
            subtype="html",
        )
