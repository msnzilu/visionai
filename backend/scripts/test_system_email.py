import asyncio
import os
import sys

# Add backend directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.email_service import EmailService
from app.core.config import settings

async def main():
    print("Testing Email Service Configuration...")
    if not EmailService.is_configured():
        print("WARNING: Email service is NOT configured (missing credentials).")
        print("Emails will be logged but not sent.")
    else:
        print("Email service IS configured.")

    recipient = "test@example.com"
    print(f"\nSending Verification Email to {recipient}...")
    success = await EmailService.send_verification_email(
        email=recipient,
        full_name="Test User",
        verification_token="dummy-token-12345"
    )
    print(f"Verification Email Sent: {success}")

    print(f"\nSending Password Reset Email to {recipient}...")
    success = await EmailService.send_password_reset_email(
        email=recipient,
        reset_token="dummy-reset-token-67890"
    )
    print(f"Password Reset Email Sent: {success}")

    print(f"\nSending Notification Email to {recipient}...")
    success = await EmailService.send_custom_notification(
        email=recipient,
        subject="System Test Notification",
        message_body="<p>This is a <b>test notification</b> from the system.</p>"
    )
    print(f"Notification Email Sent: {success}")

if __name__ == "__main__":
    asyncio.run(main())
