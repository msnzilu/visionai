# backend/app/services/gmail_service.py
import os
import base64
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.core.config import settings
from app.models.user import GmailAuth

# Scopes required for the application
SCOPES = [
    'openid',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send'
]

class GmailService:
    def __init__(self):
        self.client_id = settings.GOOGLE_CLIENT_ID
        self.client_secret = settings.GOOGLE_CLIENT_SECRET
        self.redirect_uri = f"http://localhost:8000{settings.API_V1_STR}/auth/gmail/callback"
        
        # In development, allow HTTP for Oauth
        if settings.ENVIRONMENT == "development":
            os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

    def get_authorization_url(self, redirect_uri: Optional[str] = None, state: Optional[str] = None) -> str:
        """Generate the authorization URL for the user"""
        flow = Flow.from_client_config(
            self._get_client_config(),
            scopes=SCOPES,
            redirect_uri=redirect_uri or self.redirect_uri
        )
        
        # Build authorization URL parameters
        auth_params = {
            'access_type': 'offline',
            'include_granted_scopes': 'true',
            'prompt': 'consent'
        }
        
        # Add state if provided
        if state:
            auth_params['state'] = state
        
        auth_url, _ = flow.authorization_url(**auth_params)
        
        return auth_url

    def exchange_code_for_token(self, code: str, redirect_uri: Optional[str] = None) -> Dict[str, Any]:
        """Exchange the authorization code for tokens"""
        flow = Flow.from_client_config(
            self._get_client_config(),
            scopes=SCOPES,
            redirect_uri=redirect_uri or self.redirect_uri
        )
        
        flow.fetch_token(code=code)
        creds = flow.credentials
        
        return {
            "access_token": creds.token,
            "refresh_token": creds.refresh_token,
            "token_uri": creds.token_uri,
            "client_id": creds.client_id,
            "client_secret": creds.client_secret,
            "scopes": creds.scopes,
            "expiry": creds.expiry,
            "connected_at": datetime.utcnow()
        }

    def get_service(self, auth: GmailAuth):
        """Get the Gmail API service instance"""
        creds = Credentials(
            token=auth.access_token,
            refresh_token=auth.refresh_token,
            token_uri=auth.token_uri,
            client_id=auth.client_id,
            client_secret=auth.client_secret,
            scopes=auth.scopes
        )
        
        return build('gmail', 'v1', credentials=creds)

    def send_email(self, auth: GmailAuth, to: str, subject: str, body: str, attachments: List[str] = []) -> Dict[str, Any]:
        """Send an email via Gmail API"""
        service = self.get_service(auth)
        
        message = MIMEMultipart()
        message['to'] = to
        message['subject'] = subject
        
        msg = MIMEText(body)
        message.attach(msg)
        
        for file_path in attachments:
            if os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    file_data = f.read()
                    filename = os.path.basename(file_path)
                    attachment = MIMEApplication(file_data, _subtype="pdf")
                    attachment.add_header('Content-Disposition', 'attachment', filename=filename)
                    message.attach(attachment)
        
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        
        try:
            message = service.users().messages().send(userId='me', body={'raw': raw_message}).execute()
            return message
        except HttpError as error:
            print(f'An error occurred: {error}')
            raise error

    def list_messages(self, auth: GmailAuth, query: str = "", max_results: int = 10) -> List[Dict[str, Any]]:
        """List messages matching the query"""
        service = self.get_service(auth)
        
        try:
            results = service.users().messages().list(userId='me', q=query, maxResults=max_results).execute()
            messages = results.get('messages', [])
            return messages
        except HttpError as error:
            print(f'An error occurred: {error}')
            return []

    def get_message(self, auth: GmailAuth, message_id: str) -> Dict[str, Any]:
        """Get full message details"""
        service = self.get_service(auth)
        
        try:
            message = service.users().messages().get(userId='me', id=message_id).execute()
            return message
        except HttpError as error:
            print(f'An error occurred: {error}')
            raise error
            
    def get_profile(self, auth: GmailAuth) -> Dict[str, Any]:
        """Get user's email profile"""
        service = self.get_service(auth)
        try:
            profile = service.users().getProfile(userId='me').execute()
            return profile
        except HttpError as error:
            print(f'An error occurred: {error}')
            raise error

    def _get_client_config(self) -> Dict[str, Any]:
        """Construct client config for google-auth-oauthlib"""
        return {
            "web": {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        }

gmail_service = GmailService()
