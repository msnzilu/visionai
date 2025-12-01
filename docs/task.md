# Task: Implement VisionAI Email Agent

- [ ] **Phase 1: Foundation & Auth** <!-- id: 0 -->
    - [ ] Set up Google Cloud Project & Enable Gmail API <!-- id: 1 -->
    - [ ] Configure OAuth Consent Screen (Test Mode) <!-- id: 2 -->
    - [ ] Update `User` model for Gmail tokens (`access_token`, `refresh_token`) <!-- id: 3 -->
    - [ ] Implement Backend OAuth endpoints (`/auth/gmail/connect`, `/callback`) <!-- id: 4 -->
    - [ ] Create `GmailService` for token management and API calls <!-- id: 5 -->
    - [ ] Update `Application` model with email tracking fields (`thread_id`, `message_id`) <!-- id: 6 -->

- [ ] **Phase 2: Direct Email Application** <!-- id: 7 -->
    - [ ] Implement `GmailService.send_email` with attachment support <!-- id: 8 -->
    - [ ] Create `POST /api/v1/applications/email-apply` endpoint <!-- id: 9 -->
    - [ ] Design & Implement Email Template for job applications <!-- id: 10 -->
    - [ ] Frontend: Add "Connect Gmail" button in User Profile <!-- id: 11 -->
    - [ ] Frontend: Add "Quick Apply" (Email) button on Job Listings <!-- id: 12 -->
    - [ ] Frontend: "Preview & Send" Modal for email applications <!-- id: 13 -->

- [ ] **Phase 3: Tracking & Intelligence** <!-- id: 14 -->
    - [ ] Implement `GmailService.list_messages` and `get_message` <!-- id: 15 -->
    - [ ] Create "Inbox Scanner" background task (Celery/Cron) <!-- id: 16 -->
    - [ ] Implement logic to match incoming emails to `Application` records <!-- id: 17 -->
    - [ ] Implement keyword-based status parser (e.g., "Interview", "Reject") <!-- id: 18 -->
    - [ ] Create `POST /api/v1/applications/track` for manual external link tracking <!-- id: 19 -->

- [ ] **Phase 4: Dashboard & UI** <!-- id: 20 -->
    - [ ] Update "My Applications" page to show Email Status <!-- id: 21 -->
    - [ ] Add "Last Email" snippet/preview to Application card <!-- id: 22 -->
    - [ ] Implement "Sync Inbox" button for manual refresh <!-- id: 23 -->
    - [ ] Add "I Applied" button for external jobs to trigger tracking <!-- id: 24 -->

- [ ] **Verification & Polish** <!-- id: 25 -->
    - [ ] Test OAuth flow (Connect/Disconnect/Refresh) <!-- id: 26 -->
    - [ ] Verify Email Sending with attachments <!-- id: 27 -->
    - [ ] Verify Reply Detection and Status Update <!-- id: 28 -->
    - [ ] Security Review (Token storage, Scopes) <!-- id: 29 -->
