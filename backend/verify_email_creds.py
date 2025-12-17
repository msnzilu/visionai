
import asyncio
import logging
from app.core.config import settings
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def verify_credentials():
    print("="*50)
    print("EMAIL CONFIGURATION DEBUGGER")
    print("="*50)
    
    print(f"MAIL_SERVER: {settings.MAIL_SERVER}")
    print(f"MAIL_PORT: {settings.MAIL_PORT}")
    print(f"MAIL_USERNAME: {settings.MAIL_USERNAME}")
    
    if settings.MAIL_PASSWORD:
        masked_pwd = settings.MAIL_PASSWORD[:2] + "*" * (len(settings.MAIL_PASSWORD) - 2) if len(settings.MAIL_PASSWORD) > 2 else "***"
        print(f"MAIL_PASSWORD: {masked_pwd} (Length: {len(settings.MAIL_PASSWORD)})")
    else:
        print("MAIL_PASSWORD: [NOT SET]")
        
    print(f"MAIL_STARTTLS: {settings.MAIL_STARTTLS}")
    print(f"MAIL_SSL_TLS: {settings.MAIL_SSL_TLS}")
    
    if not (settings.MAIL_SERVER and settings.MAIL_USERNAME and settings.MAIL_PASSWORD):
        print("\nERROR: Missing required email settings.")
        return

    conf = ConnectionConfig(
        MAIL_USERNAME=settings.MAIL_USERNAME,
        MAIL_PASSWORD=settings.MAIL_PASSWORD,
        MAIL_FROM=settings.MAIL_FROM,
        MAIL_PORT=settings.MAIL_PORT,
        MAIL_SERVER=settings.MAIL_SERVER,
        MAIL_STARTTLS=settings.MAIL_STARTTLS,
        MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
        USE_CREDENTIALS=True,
        VALIDATE_CERTS=True
    )

    print("\nAttempting connection to SMTP server...")
    
    try:
        print(f"Connecting to {settings.MAIL_SERVER}:{settings.MAIL_PORT}...")
        
        # Use simple SMTP to test connection and auth
        import smtplib
        
        server = smtplib.SMTP(settings.MAIL_SERVER, settings.MAIL_PORT)
        server.set_debuglevel(0)
        
        if settings.MAIL_STARTTLS:
            server.starttls()
            
        try:
            server.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)
            print("AUTH SUCCESS: Login successful!")
        except Exception as e:
            print(f"AUTH FAILED: {e}")
        finally:
            server.quit()

    except Exception as e:
        print(f"CONNECTION FAILED: {e}")

if __name__ == "__main__":
    asyncio.run(verify_credentials())
