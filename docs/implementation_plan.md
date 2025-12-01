# VisionAI Email Agent Implementation Guide

## Executive Summary

This guide provides a strategic implementation plan for building an "Email Agent" system. This feature empowers users to apply to jobs directly via email (when available) and tracks their application status by monitoring their inbox for confirmations and replies, effectively acting as a personal job application assistant.

---

## The Big Picture: "Email Agent" Model

### What We Are Building
- **User-Centric**: No employer dashboards. The system works entirely for the job seeker.
- **Email-Driven**: Uses the user's email account (via Gmail API or similar) to send applications and track responses.
- **Hybrid Application Methods**:
    1.  **Direct Email**: VisionAI sends an email with the user's CV to the employer's contact address.
    2.  **External Link**: User applies on an external site, and VisionAI detects the confirmation email to track it.

### Why This Works
- **Universal Tracking**: Tracks applications regardless of where they were submitted (as long as a confirmation email is received).
- **Seamless "Quick Apply"**: For jobs with email contacts, applying is a single click.
- **Automated Status Updates**: The system reads replies (e.g., "Interview Invitation") to update status automatically.

---

## Conceptual Architecture

### Three Core Components

#### 1. **Email Integration Service**
- Connects to user's email provider (Gmail API).
- Handles OAuth authentication and token management.
- Sends emails (applications) and reads emails (tracking).

#### 2. **Application Intelligence Engine**
- **Parser**: Analyzes incoming emails to identify:
    - Application confirmations (from Indeed, LinkedIn, etc.).
    - Employer replies (interview requests, rejections).
- **Matcher**: Links incoming emails to specific Job IDs in the database.

#### 3. **User Dashboard**
- "My Applications" view showing all tracked jobs.
- Status updates derived from email activity.
- Inbox view filtered for job-related communications.

---

## Implementation Phases

### Phase 1: Foundation (Week 1-2)
**Goal**: Database updates and Email Integration setup.

**Tasks**:
1.  **Database Design**
    - Update `users` collection to store OAuth tokens (encrypted).
    - Update `applications` collection to store `message_id`, `thread_id`, and `last_email_status`.
    - Create `email_logs` collection for debugging and history.

2.  **Gmail API Integration**
    - Set up Google Cloud Project with Gmail API.
    - Implement OAuth flow (connect/disconnect email).
    - Create utility functions: `send_email`, `list_messages`, `get_message`.

### Phase 2: Core Features (Week 3-4)
**Goal**: Sending applications and basic tracking.

**Tasks**:
1.  **Direct Email Application**
    - "Quick Apply" button for jobs with `employer_email`.
    - Generates a professional email template.
    - Attaches user's default CV.
    - Sends via user's connected Gmail account.

2.  **Application Tracking (Outbound)**
    - When an application is sent, create a record in `applications`.
    - Status: `Applied`.

3.  **External Link Tracking (Inbound)**
    - "I Applied" button for external jobs.
    - System scans inbox for confirmation emails from that domain/platform.
    - Links email to the job record.

### Phase 3: Intelligence & Automation (Week 5-6)
**Goal**: Automated status updates from incoming emails.

**Tasks**:
1.  **Reply Detection**
    - Scheduled task to scan for new emails in application threads.
    - Analyze sender and subject line.

2.  **Sentiment/Status Analysis**
    - Simple keyword matching (e.g., "schedule interview", "unfortunately", "received").
    - (Optional) LLM-based analysis for higher accuracy.
    - Update application status: `Interview`, `Rejected`, `Under Review`.

### Phase 4: User Experience (Week 7-8)
**Goal**: Dashboard and Management.

**Tasks**:
1.  **"My Applications" Dashboard**
    - List of all applications.
    - Status indicators (e.g., "Replied 2 days ago").
    - "Action Required" alerts (e.g., for interview requests).

2.  **Email Preview**
    - View relevant email threads directly within VisionAI.
    - "Reply" button that opens their email client or a simple reply form.

---

## The User Journey (Step-by-Step)

### Scenario A: Direct Email Job
1.  **Browse**: User sees a job with "Quick Apply" (Email icon).
2.  **Click**: User clicks "Quick Apply".
3.  **Review**: specific modal shows the generated email preview.
4.  **Send**: User confirms. VisionAI sends the email via their Gmail.
5.  **Track**: Job added to "My Applications" as "Applied".

### Scenario B: External Link Job
1.  **Browse**: User sees a job with "Apply on Company Site".
2.  **Click**: User goes to external site and applies.
3.  **Confirm**: User returns and clicks "I Applied" (or system auto-detects confirmation email).
4.  **Track**: Job added to "My Applications".
5.  **Update**: Days later, employer replies. VisionAI detects the email and updates status to "Interview".

---

## Technical Requirements

### Database Collections Needed

1.  **users** (update)
    - Add `gmail_auth` field with the following structure:
      ```python
      class GmailAuth(BaseModel):
          access_token: str
          refresh_token: str
          token_uri: str = "https://oauth2.googleapis.com/token"
          client_id: str
          client_secret: str
          scopes: List[str]
          expiry: Optional[datetime]
          connected_at: datetime
          email_address: Optional[str]
      ```

2.  **applications** (update)
    - `application_method`: "email" | "external"
    - `email_thread_id`: String (Gmail Thread ID)
    - `last_email_at`: Timestamp
    - `email_status`: "sent" | "delivered" | "replied"

3.  **jobs** (update)
    - `application_email`: String (if available)
    - `application_url`: String

### API Endpoints Required

1.  **POST /api/v1/auth/gmail/connect**: Initiate OAuth.
2.  **POST /api/v1/applications/email-apply**: Send email application.
3.  **POST /api/v1/applications/track**: Manually track an external job.
4.  **GET /api/v1/applications/sync**: Trigger inbox scan (or use webhooks).

---

## Key Decisions to Make

1.  **Privacy & Permissions**:
    - We need `https://www.googleapis.com/auth/gmail.send` and `https://www.googleapis.com/auth/gmail.readonly`.
    - User trust is paramount. Clear explanation of *why* we need read access (to track replies).

2.  **Scanning Frequency**:
    - Real-time (Webhooks/Push Notifications) vs Polling (Cron job every X minutes).
    - Polling is easier to start; Webhooks are better for scale.

3.  **LLM vs Keywords**:
    - For analyzing email content, regex/keywords are cheap and fast.
    - LLMs are more accurate but add cost/latency. Start with keywords.

---

## Next Steps: Getting Started

### Immediate Actions (This Week)

1.  **Google Cloud Console**:
    - Create project.
    - Enable Gmail API.
    - Configure OAuth Consent Screen (Test mode).

2.  **Backend Auth**:
    - Implement `auth/gmail` endpoints.
    - Store tokens securely.

3.  **Database Update**:
    - Update `Application` model to support email tracking fields.
