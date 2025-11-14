# Norvalt Product Requirements Document (PRD)

## Document Control

**Version:** 1.0
**Last Updated:** November 4, 2025
**Owner:** Nikolai Skorodihin (Founder) & Helios (CTO)
**Status:** Active Development
**Target Completion:** January 12, 2026 (Week 12)

---

## Executive Summary

### MVP Scope

Norvalt is an AI-powered lead management platform that captures leads from all sources (website forms, email, Facebook) and responds with AI in under 90 seconds, 24/7. The MVP enables Norwegian car dealerships to never lose another lead due to slow response times.

### Business Goals

- **Week 12 (Jan 12):** Production-ready MVP
- **Week 14 (Jan 26):** First paying customer
- **Week 20 (Mar 9):** 8-10 customers, profitable (36-45K NOK MRR)

### Success Criteria

1. All three lead sources (website, email, Facebook) capture leads successfully
2. AI responds to 95%+ of new leads within 90 seconds
3. Multi-tenant architecture with proper data isolation
4. Dashboard allows sales reps to manage leads end-to-end
5. Platform achieves 99.5% uptime
6. Zero critical security vulnerabilities

### Timeline Overview

```
Week 3-4:   Foundation (Auth, Database, Basic API)
Week 5-6:   Lead Capture (All Sources Working)
Week 7-9:   AI Engine (Auto-Response System)
Week 10-12: Dashboard & Polish (Production-Ready)
```

---

## User Stories by Epic

### Epic 1: Authentication & Multi-Tenancy

**Business Value:** Secure, scalable foundation for B2B SaaS platform

#### US-1.1: Dealership Owner Registration

**Priority:** MUST-HAVE
**Story:** As a dealership owner, I want to create an account for my dealership so that my team can access Norvalt.

**Acceptance Criteria:**

- [x] Owner can sign up using email/password or OAuth (Google)
- [x] Owner creates an organization (dealership) during signup
- [x] Owner receives email verification
- [x] Owner is automatically made admin of their organization
- [x] System generates unique `dealership_id` and `clerk_org_id`

**Implementation Notes:**

- Use Clerk Organizations feature
- Map each Clerk organization to one `dealerships` table row
- **✅ IMPLEMENTED:** Clerk webhook (`/webhooks/clerk`) automatically creates dealership and user records when organization membership is created
- Send welcome email with next steps

**Validated Pain Point:** Dealerships need simple onboarding (from Customer Profiles doc)

---

#### US-1.2: Team Member Invitation

**Priority:** MUST-HAVE
**Story:** As a dealership admin, I want to invite sales reps to join my organization so they can access leads.

**Acceptance Criteria:**

- [x] Admin can invite users via email
- [x] Invited users receive email with join link
- [x] Invited users complete signup and are added to organization
- [x] Admin can assign roles (admin, sales_rep, manager)
- [x] Users can only see data for their dealership

**Implementation Notes:**

- Use Clerk Invitations API
- Store user role in `users` table
- **✅ IMPLEMENTED:** Clerk webhook automatically creates user records when membership is created, assigns roles based on membership role
- Implement role-based access control (RBAC) in API

---

#### US-1.3: Data Isolation

**Priority:** MUST-HAVE
**Story:** As a dealership, I want to ensure my leads are private and not visible to other dealerships.

**Acceptance Criteria:**

- [ ] All database queries filtered by `dealership_id`
- [ ] API extracts `dealership_id` from Clerk JWT
- [ ] Users cannot access resources from other dealerships
- [ ] Automated tests verify data isolation
- [ ] Row-level security (RLS) policies enforced in database

**Implementation Notes:**

- Implement middleware in FastAPI to extract and validate `dealership_id`
- Add RLS policies in Supabase
- Create comprehensive integration tests

**Validated Pain Point:** B2B SaaS security requirement (from Architecture doc)

---

### Epic 2: Lead Capture System

**Business Value:** Capture leads from all sources without manual work

#### US-2.1: Website Form Webhook

**Priority:** MUST-HAVE
**Story:** As a dealership, I want leads from my website to automatically appear in Norvalt so I never miss an inquiry.

**Acceptance Criteria:**

- [ ] Public webhook endpoint accepts POST requests
- [ ] Endpoint validates required fields (name, email, message)
- [ ] Lead is created in database with source='website'
- [ ] Returns 200 OK on success, 400 on validation error
- [ ] Handles duplicate submissions gracefully
- [ ] Logs all webhook requests for debugging

**API Specification:**

```
POST /webhooks/form/:dealership_id
Content-Type: application/json

Request Body:
{
  "name": "string (required)",
  "email": "string (required, email format)",
  "phone": "string (optional)",
  "vehicle_interest": "string (optional)",
  "message": "string (required)",
  "source_url": "string (optional)"
}

Response: 200 OK
{
  "lead_id": "uuid",
  "status": "created"
}
```

**Implementation Steps:**

1. Create `/webhooks/form/:dealership_id` endpoint in FastAPI
2. Add Pydantic model for request validation
3. Implement duplicate detection (check email + dealership)
4. Create lead record in `leads` table
5. Queue AI response job
6. Return success response
7. Test with curl/Postman

**Edge Cases:**

- Duplicate submission within 5 minutes (update existing lead)
- Missing optional fields (handle gracefully)
- Invalid email format (return 400 error)
- Malformed JSON (return 400 error)

**Validated Pain Point:** Website forms go to generic inbox, slow response (Customer Profiles, Pain #1)

---

#### US-2.2: Email Monitoring (Importer Portals)

**Priority:** MUST-HAVE
**Story:** As a dealership, I want leads from Toyota.no, VW.no, etc. to automatically appear in Norvalt without checking email manually.

**Acceptance Criteria:**

- [x] System receives emails via SendGrid Inbound Parse webhook
- [x] Detects new emails and deduplicates via Message-ID
- [x] AI classifies emails (sales_inquiry, spam, other, uncertain) using Claude API
- [x] Pre-filters obvious spam using rule-based detection
- [x] Extracts: customer name, email, phone, vehicle interest, message, urgency
- [x] Creates lead with source='email'
- [x] Handles processing errors gracefully with retry capability
- [x] Email forwarding to dealership-specific addresses (e.g., dealership-abc123@leads.autolead.no)

**Database Schema:**

```sql
-- emails table (new)
CREATE TABLE emails (
    id UUID PRIMARY KEY,
    dealership_id UUID REFERENCES dealerships(id),
    lead_id UUID REFERENCES leads(id),
    message_id VARCHAR(255) UNIQUE NOT NULL,
    from_email VARCHAR(255) NOT NULL,
    from_name VARCHAR(255),
    subject VARCHAR(500),
    body_text TEXT,
    body_html TEXT,
    processing_status VARCHAR(50) DEFAULT 'pending',
    classification VARCHAR(50), -- sales_inquiry, spam, other, uncertain
    classification_confidence FLOAT,
    extracted_data JSONB,
    received_at TIMESTAMP WITH TIME ZONE,
    processed_at TIMESTAMP WITH TIME ZONE
);

-- Add to dealerships table
email_integration_enabled BOOLEAN DEFAULT FALSE,
email_forwarding_address VARCHAR(255) UNIQUE,
email_integration_settings JSONB
```

**Implementation Steps:**

✅ **COMPLETED - Modern Architecture:**

1. SendGrid Inbound Parse webhook endpoint (`POST /api/v1/emails/webhook/inbound`)
2. Email forwarding to unique dealership addresses (e.g., `dealership-abc123@leads.autolead.no`)
3. Background processing with FastAPI BackgroundTasks
4. Pre-filtering for spam (rule-based: domains, keywords, link count)
5. AI classification using Claude 3.5 Sonnet (sales_inquiry, spam, other, uncertain)
6. Lead data extraction from sales inquiries
7. Automatic lead creation with source='email'
8. Deduplication via Message-ID
9. Error handling with retry capability
10. Management endpoints for listing, viewing, and reprocessing emails

**AI Classification & Extraction:**

Using Claude API to:
- Classify emails into categories with confidence scores
- Extract structured data: customer name, email, phone, car interest, urgency, summary
- Automatically determine lead source (toyota.no, volkswagen.no, direct_email, other)
- Score leads based on urgency (high=70, medium=60, low=50)

**Edge Cases:**

- Duplicate emails (handled via Message-ID deduplication)
- Spam/marketing emails (pre-filtered + AI classification)
- Missing fields (extracted with AI, fallback to sender info)
- Processing failures (stored in error_message, retry with `/reprocess` endpoint)
- SendGrid webhook failures (returns 200 OK immediately, processes in background)

**Validated Pain Point:** Importer portal leads require manual email checking (Customer Profiles, 40% of leads)

---

#### US-2.3: Facebook Lead Ads Integration

**Priority:** MUST-HAVE
**Story:** As a dealership, I want leads from my Facebook Lead Ads campaigns to automatically appear in Norvalt immediately after a customer submits the form.

**Scope Note:** This integration focuses on **Facebook Lead Ads** (lead capture forms shown in ads). This is NOT Facebook Messenger integration (two-way chat). Messenger integration may be considered in future phases if market demand increases.

**Acceptance Criteria:**

- [x] Webhook receives Facebook leadgen notifications in real-time (Session 1: Backend implemented)
- [x] Webhook verifies Facebook signature using App Secret (Session 1: HMAC SHA256 verification)
- [x] Retrieves full lead data via Graph API using Page Access Token (Session 1: FacebookClient implemented)
- [x] Maps Facebook form fields to Norvalt lead schema (Session 1: FacebookLeadData class)
- [x] Creates lead with source='facebook' and stores metadata (Session 1: Lead processing logic)
- [x] Handles duplicate submissions gracefully (dedupe by facebook_lead_id) (Session 1: Deduplication check)
- [x] Passes Facebook webhook verification challenge (GET request) (Session 1: GET endpoint implemented)
- [ ] Supports multiple Pages per dealership (Session 2: Pending Meta App setup)
- [x] Background processing with error handling and retry (Session 1: BackgroundTasks + error handling)

**API Specification:**

```
GET /api/v1/webhooks/facebook
  - Facebook webhook verification endpoint
  - Validates hub.verify_token
  - Returns hub.challenge to confirm subscription

POST /api/v1/webhooks/facebook
  - Receives leadgen events from Facebook
  - Validates X-Hub-Signature-256 header
  - Processes lead asynchronously (background task)
  - Returns 200 immediately to prevent timeout
```

**Implementation Steps:**

1. **Meta App Setup:**
   - Create Facebook App in Meta for Developers
   - Add Webhooks and Lead Ads products
   - Configure webhook subscriptions for leadgen events
   - Generate Page Access Tokens for each dealership's page

2. **Backend Implementation:**
   - Create `/api/v1/webhooks/facebook` endpoint
   - Implement GET handler for webhook verification
   - Implement POST handler for leadgen events
   - Add signature verification middleware
   - Integrate Graph API client for lead retrieval
   - Map Facebook fields to Lead model
   - Store facebook_lead_id in source_metadata for deduplication

3. **Configuration:**
   - Add FACEBOOK_APP_ID, FACEBOOK_APP_SECRET to settings
   - Add FACEBOOK_VERIFY_TOKEN to settings
   - Store Page Access Tokens per dealership (encrypted)

4. **Testing:**
   - Test webhook verification with Meta
   - Test lead submission with Facebook Test Tools
   - Verify lead creation in database
   - Test duplicate lead handling
   - Test error scenarios (Graph API failures)

**Graph API Integration:**

```
GET https://graph.facebook.com/v21.0/{leadgen-id}
  ?access_token={page-access-token}

Response:
{
  "created_time": "2024-11-13T10:30:00+0000",
  "id": "123456789",
  "field_data": [
    {"name": "full_name", "values": ["Ola Nordmann"]},
    {"name": "email", "values": ["ola@example.com"]},
    {"name": "phone_number", "values": ["+4712345678"]},
    {"name": "vehicle_interest", "values": ["Tesla Model 3"]}
  ]
}
```

**Field Mapping:**
- `full_name` → `customer_name`
- `email` → `customer_email`
- `phone_number` → `customer_phone`
- `vehicle_interest` / `which_car` → `vehicle_interest`
- Any custom questions → `initial_message` (concatenated)
- Store raw `field_data` in `source_metadata` for debugging

**Requirements:**
- App ID and App Secret (from Meta App Dashboard)
- Page Access Token (generated per Facebook Page)
- Webhook Verify Token (random string we generate)
- Pages must subscribe to App's webhook

**Rate Limits:**
- Facebook Graph API: 200 calls per hour per user
- Webhook deliveries: Real-time, no rate limits on receiving
- Retry policy: Exponential backoff for Graph API failures

**Edge Cases:**

- **Webhook signature mismatch:** Reject with 401, log security alert
- **Graph API timeout:** Queue retry job with exponential backoff (2s, 4s, 8s)
- **Missing form fields:** Map to null, store warning in logs
- **Test leads:** Facebook sends test leads with `is_test: true` flag - skip AI response
- **Duplicate leads:** Check `source_metadata.facebook_lead_id`, update if exists
- **Invalid Page Access Token:** Alert dealership, provide token refresh instructions
- **Multiple pages per dealership:** Support array of page tokens in settings

**Security Considerations:**

- Always verify `X-Hub-Signature-256` header using HMAC SHA256
- Store Page Access Tokens encrypted in database
- Validate `hub.verify_token` matches our secret
- Rate limit webhook endpoint to prevent abuse
- Log all webhook requests for audit trail

**Dealership Setup Process:**

1. Dealership creates Lead Ad campaign in Facebook Ads Manager
2. Admin enables Facebook integration in Norvalt settings
3. Admin connects Facebook Page via OAuth flow
4. System subscribes to leadgen webhook for that Page
5. Leads automatically flow into Norvalt when submitted

**Validated Pain Point:** Facebook leads require manual CSV download from Ads Manager, causing 30+ minute delays. Dealerships miss hot leads. (Customer Profiles, 10% of leads)

---

#### US-2.4: Lead Deduplication

**Priority:** SHOULD-HAVE
**Story:** As a dealership, I want duplicate leads to be merged so I don't contact the same customer multiple times.

**Acceptance Criteria:**

- [ ] System checks for existing lead by email before creating
- [ ] If duplicate found within 7 days, updates existing lead
- [ ] If duplicate found after 7 days, creates new lead (new inquiry)
- [ ] Stores all submission sources in metadata
- [ ] Dashboard shows "duplicate" indicator

**Implementation Logic:**

```python
def create_or_update_lead(data, dealership_id):
    # Check for existing lead by email
    existing = db.query(Lead).filter(
        Lead.email == data.email,
        Lead.dealership_id == dealership_id,
        Lead.created_at >= now() - timedelta(days=7)
    ).first()

    if existing:
        # Update existing lead
        existing.last_contact_at = now()
        existing.source_metadata.append(data)
        return existing
    else:
        # Create new lead
        return Lead(**data)
```

**Validated Pain Point:** Avoid annoying customers with multiple contacts (Customer Profiles)

---

### Epic 3: AI Auto-Response System

**Business Value:** Respond to every lead within 90 seconds, 24/7

#### US-3.1: Claude API Integration

**Priority:** MUST-HAVE
**Story:** As the system, I want to generate high-quality Norwegian responses to customer inquiries using AI.

**Acceptance Criteria:**

- [ ] API key securely stored in environment variables
- [ ] System calls Claude API with lead context
- [ ] Responses are in Norwegian
- [ ] Responses are contextually relevant to vehicle interest
- [ ] Responses maintain professional dealership tone
- [ ] System handles API errors gracefully
- [ ] Response generation takes < 30 seconds

**Prompt Engineering:**

```python
SYSTEM_PROMPT = """
Du er en hjelpsom kundeservicerepresentant for {dealership_name},
en bilforhandler i Norge. Din oppgave er å svare raskt og profesjonelt
på kundehenvendelser om biler.

Regler:
- Svar alltid på norsk
- Vær høflig og profesjonell
- Bekreft kundens interesse
- Fortell at en selger vil ta kontakt snart
- IKKE forhandle priser
- IKKE love noe som ikke er bekreftet
- Hold svar kort (2-3 setninger)
"""

USER_PROMPT = """
Kunde: {customer_name}
Interessert i: {vehicle_interest}
Melding: {customer_message}

Generer et venlig svar som:
1. Takker kunden for henvendelsen
2. Bekrefter interesse i kjøretøyet
3. Forteller at en selger vil kontakte dem snart
"""
```

**Implementation Steps:**

1. Install Anthropic Python SDK
2. Create `ai_service.py` module
3. Implement `generate_response()` function
4. Build context from lead data
5. Call Claude API with prompt
6. Parse and validate response
7. Store response in database
8. Handle errors (API down, rate limits, timeouts)

**External Integration:**

- Claude API: `claude-3-5-sonnet-20241022` model
- Max tokens: 500 (keep responses concise)
- Temperature: 0.7 (balanced creativity)
- Rate limits: Track usage, stay within tier limits

**Validated Pain Point:** 4+ hour average response time (Customer Profiles, Pain #1)

---

#### US-3.2: Email Sending System

**Priority:** MUST-HAVE
**Story:** As the system, I want to send AI-generated responses to customers via email automatically.

**Acceptance Criteria:**

- [ ] System sends emails using Resend or SendGrid
- [ ] Emails are branded with dealership name and logo
- [ ] Emails include dealership contact information
- [ ] Emails have proper from/reply-to addresses
- [ ] System tracks email delivery status
- [ ] System handles bounce notifications
- [ ] Unsubscribe link included (GDPR compliance)

**Email Template:**

```html
<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8" />
    <title>{dealership_name} - Svar på din henvendelse</title>
  </head>
  <body>
    <div style="max-width: 600px; margin: 0 auto; font-family: Arial;">
      <div style="background: #1a73e8; color: white; padding: 20px;">
        <h1>{dealership_name}</h1>
      </div>

      <div style="padding: 20px;">
        <p>Hei {customer_name},</p>

        <p>{ai_response}</p>

        <p>
          Med vennlig hilsen,<br />
          {dealership_name}<br />
          Telefon: {dealership_phone}<br />
          E-post: {dealership_email}
        </p>
      </div>

      <div style="background: #f5f5f5; padding: 10px; font-size: 12px;">
        <a href="{unsubscribe_url}">Avmeld nyhetsbrev</a>
      </div>
    </div>
  </body>
</html>
```

**Implementation Steps:**

1. Sign up for Resend.com (or SendGrid)
2. Verify domain for email sending
3. Create email templates
4. Implement `send_email()` function
5. Queue email sending jobs
6. Handle delivery webhooks (bounces, opens, clicks)
7. Store email status in database

**External Integration:**

- Resend API: Simple REST API
- Rate limits: 100 emails/day (free tier), upgrade as needed
- Deliverability: Monitor bounce rate, maintain < 5%

**Validated Pain Point:** Need instant response to leads (Customer Profiles, Use Case 1)

---

#### US-3.3: SMS Notification to Sales Rep

**Priority:** SHOULD-HAVE
**Story:** As a sales rep, I want to receive an SMS when a hot lead arrives so I can follow up immediately.

**Acceptance Criteria:**

- [ ] Sales rep receives SMS within 2 minutes of new lead
- [ ] SMS includes: customer name, vehicle interest, urgency indicator
- [ ] SMS includes link to lead in dashboard
- [ ] Sales rep can configure SMS preferences (on/off, hours)
- [ ] System tracks SMS delivery status
- [ ] System respects Norwegian SMS regulations

**SMS Template:**

```
URGENT: Ny lead fra {customer_name}
Interessert i: {vehicle_interest}
Se detaljer: {dashboard_link}

- Norvalt
```

**Implementation Steps:**

1. Sign up for Twilio (or similar SMS provider)
2. Purchase Norwegian phone number
3. Implement `send_sms()` function
4. Queue SMS sending jobs
5. Track SMS delivery status
6. Add SMS preferences to user settings

**External Integration:**

- Twilio API
- Cost: ~1 NOK per SMS
- Rate limits: Monitor usage, alert if approaching limit

**Validated Pain Point:** Sales reps miss leads when not checking dashboard (Customer Profiles)

---

#### US-3.4: Auto-Response Workflow Orchestration

**Priority:** MUST-HAVE
**Story:** As the system, I want to automatically orchestrate the entire response flow when a new lead arrives.

**Acceptance Criteria:**

- [ ] New lead triggers auto-response workflow
- [ ] Workflow generates AI response
- [ ] Workflow sends email to customer
- [ ] Workflow sends SMS to sales rep
- [ ] Workflow updates lead status
- [ ] Workflow completes within 90 seconds
- [ ] Workflow retries on failure
- [ ] Workflow logs all steps for debugging

**Workflow Logic:**

```
1. Lead created in database
2. Queue "process-new-lead" job
3. Worker picks up job
4. Generate AI response (Claude API)
5. Send email to customer (Resend)
6. Send SMS to assigned sales rep (Twilio)
7. Create conversation record
8. Update lead status to "contacted"
9. Update lead.last_contact_at timestamp
10. Log completion
```

**Implementation Steps:**

1. Set up Redis instance (Upstash or Railway)
2. Install BullMQ library
3. Create job queues (ai-response, email-send, sms-send)
4. Implement workers for each job type
5. Configure retry logic (3 attempts, exponential backoff)
6. Implement job monitoring dashboard
7. Add error alerting (Sentry)

**Database Updates:**

```sql
-- Add to conversations table
INSERT INTO conversations (
  lead_id,
  dealership_id,
  channel,
  direction,
  sender,
  sender_type,
  message_content,
  created_at
) VALUES (
  {lead_id},
  {dealership_id},
  'email',
  'outbound',
  'AI',
  'ai',
  {ai_response},
  NOW()
);

-- Update lead
UPDATE leads
SET status = 'contacted', last_contact_at = NOW()
WHERE id = {lead_id};
```

**Validated Pain Point:** 90-second response time requirement (Company Context, Core Promise)

---

### Epic 4: Dashboard & Lead Management

**Business Value:** Sales reps can manage leads efficiently in one place

#### US-4.1: Lead Inbox View

**Priority:** MUST-HAVE
**Story:** As a sales rep, I want to see all my dealership's leads in one place so I can prioritize my work.

**Acceptance Criteria:**

- [ ] Page displays all leads for dealership
- [ ] Leads sorted by created_at (newest first)
- [ ] Each lead shows: customer name, vehicle interest, source, status, timestamp
- [ ] Pagination (25 leads per page)
- [ ] Real-time updates when new leads arrive
- [ ] Filter by status (new, contacted, qualified, won, lost)
- [ ] Filter by source (website, email, facebook)
- [ ] Filter by date range
- [ ] Search by customer name or email

**UI Wireframe:**

```
┌─────────────────────────────────────────────────────────────┐
│  Norvalt                    [Profile] [Settings] [Logout]   │
├─────────────────────────────────────────────────────────────┤
│  Leads                                                       │
│                                                              │
│  [All] [New] [Contacted] [Qualified] [Won] [Lost]          │
│  [Website] [Email] [Facebook]  [Last 7 days ▼]             │
│  [Search: customer name, email...]                          │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 🔵 Ola Nordmann - Tesla Model 3                      │  │
│  │    Website • 2 minutes ago • New                      │  │
│  │    "Interested in test drive this weekend"           │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 🟢 Kari Hansen - VW ID.4                             │  │
│  │    Email • 1 hour ago • Contacted                    │  │
│  │    "Looking for family SUV with long range"          │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  [1] 2 3 4 5 ... 10 [Next]                                  │
└─────────────────────────────────────────────────────────────┘
```

**Implementation Steps:**

1. Create Next.js page `/dashboard/leads`
2. Implement API call to `GET /api/leads`
3. Display leads in table/card layout
4. Add filter components
5. Implement search functionality
6. Add pagination
7. Set up real-time updates (WebSocket or polling)
8. Add loading states and error handling

**API Endpoint:**

```
GET /api/leads?status=new&source=website&limit=25&offset=0

Response: 200 OK
{
  "leads": [...],
  "total": 150,
  "page": 1,
  "pages": 6
}
```

**Validated Pain Point:** Scattered lead sources, no unified view (Customer Profiles, Pain #2)

---

#### US-4.2: Lead Detail View

**Priority:** MUST-HAVE
**Story:** As a sales rep, I want to view a lead's full details and conversation history so I can prepare for my follow-up.

**Acceptance Criteria:**

- [ ] Page displays all lead information
- [ ] Shows customer profile card (name, email, phone, vehicle interest)
- [ ] Shows full conversation history (all messages)
- [ ] Distinguishes between AI and human messages
- [ ] Allows sales rep to add manual reply
- [ ] Allows sales rep to change lead status
- [ ] Allows sales rep to add internal notes
- [ ] Shows lead source and timestamp
- [ ] Real-time updates when new messages arrive

**UI Wireframe:**

```
┌─────────────────────────────────────────────────────────────┐
│  ← Back to Leads                                            │
│                                                              │
│  Ola Nordmann                          [Change Status ▼]   │
│  ola.nordmann@example.no               Status: New         │
│  +47 123 45 678                                            │
│  Interested in: Tesla Model 3                              │
│  Source: Website • 10 minutes ago                          │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Conversation History                                │   │
│  │                                                       │   │
│  │  🔵 Customer (10 min ago)                           │   │
│  │     Interested in test drive this weekend           │   │
│  │                                                       │   │
│  │  🤖 AI (9 min ago)                                   │   │
│  │     Hei Ola! Takk for din interesse i Tesla Model 3│   │
│  │     Ja, vi har den på lager. En selger vil kontakte│   │
│  │     deg i dag for å avtale prøvekjøring.            │   │
│  │                                                       │   │
│  │  ┌─────────────────────────────────────────────┐   │   │
│  │  │ Add reply...                                 │   │   │
│  │  │                                              │   │   │
│  │  │ [Send Email] [Send SMS]                     │   │   │
│  │  └─────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Internal Notes                                      │   │
│  │  [Add note...]                                       │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

**Implementation Steps:**

1. Create Next.js page `/dashboard/leads/[id]`
2. Implement API call to `GET /api/leads/:id`
3. Display customer profile card
4. Display conversation history
5. Add manual reply form
6. Implement status change dropdown
7. Add notes functionality
8. Set up real-time updates

**API Endpoints:**

```
GET /api/leads/:id
Response: {lead data + conversations}

PATCH /api/leads/:id
Request: {status: "qualified"}

POST /api/conversations
Request: {lead_id, message_content, channel}
```

**Validated Pain Point:** Need context before calling leads (Customer Profiles, Use Case scenarios)

---

#### US-4.3: Manual Lead Creation

**Priority:** SHOULD-HAVE
**Story:** As a sales rep, I want to manually add leads (e.g., walk-ins, phone calls) so all leads are in one system.

**Acceptance Criteria:**

- [ ] "Add Lead" button in dashboard
- [ ] Form with fields: name, email, phone, vehicle interest, message, source
- [ ] Form validation (email format, phone format)
- [ ] Lead created with source='manual'
- [ ] AI response NOT triggered for manual leads
- [ ] Success message after creation
- [ ] Redirects to lead detail page

**Implementation Steps:**

1. Add "Add Lead" button to leads page
2. Create modal/page with form
3. Implement form validation
4. Call `POST /api/leads` endpoint
5. Handle success/error states
6. Redirect to new lead detail page

**Validated Pain Point:** Walk-in and phone leads also need tracking (Customer Profiles)

---

#### US-4.4: Lead Status Management

**Priority:** MUST-HAVE
**Story:** As a sales rep, I want to update lead status as I work through the sales process.

**Acceptance Criteria:**

- [ ] Status dropdown in lead detail page
- [ ] Status options: new, contacted, qualified, won, lost
- [ ] Status change updates database
- [ ] Status change logged in lead history
- [ ] Dashboard filters work with status values
- [ ] Analytics use status for conversion tracking

**Implementation Steps:**

1. Add status dropdown UI component
2. Implement `PATCH /api/leads/:id` endpoint
3. Update lead status in database
4. Log status change event
5. Update UI optimistically
6. Handle errors gracefully

**Database Schema:**

```sql
-- Optional: Track status history
CREATE TABLE lead_status_history (
  id UUID PRIMARY KEY,
  lead_id UUID REFERENCES leads(id),
  old_status VARCHAR(50),
  new_status VARCHAR(50),
  changed_by UUID REFERENCES users(id),
  changed_at TIMESTAMP DEFAULT NOW()
);
```

**Validated Pain Point:** Need to track progress through sales funnel (Customer Profiles)

---

### Epic 5: Basic Automation & Analytics

**Business Value:** Automated follow-ups and insights into lead performance

#### US-5.1: Follow-Up Sequences

**Priority:** SHOULD-HAVE
**Story:** As a sales rep, I want the system to automatically send follow-up messages so leads don't go cold.

**Acceptance Criteria:**

- [ ] System sends Day 3 follow-up if lead status is still "contacted"
- [ ] System sends Day 7 follow-up if lead status is still "contacted"
- [ ] Follow-ups are AI-generated and contextual
- [ ] Sales rep can disable follow-ups for specific leads
- [ ] Dashboard shows scheduled follow-ups

**Follow-Up Logic:**

```
Day 0: Initial inquiry + AI response
Day 3: If status = "contacted" → Send follow-up
Day 7: If status = "contacted" → Send final follow-up
Day 7: If no response → Change status to "lost"
```

**Implementation Steps:**

1. Create `automation_rules` table
2. Create scheduled job to check for follow-up triggers
3. Generate AI follow-up messages
4. Send via email
5. Log follow-up in conversation history
6. Add UI to view/disable scheduled follow-ups

**Validated Pain Point:** No follow-up system, leads go cold (Customer Profiles, Pain #3)

---

#### US-5.2: Basic Analytics Dashboard

**Priority:** SHOULD-HAVE
**Story:** As a sales manager, I want to see lead metrics so I can track team performance.

**Acceptance Criteria:**

- [ ] Dashboard shows total leads (last 7 days, last 30 days)
- [ ] Dashboard shows leads by source (pie chart)
- [ ] Dashboard shows leads by status (bar chart)
- [ ] Dashboard shows average response time
- [ ] Dashboard shows conversion rate (leads → qualified → won)
- [ ] Data refreshes automatically

**Metrics to Track:**

```
- Total leads: COUNT(*)
- By source: COUNT(*) GROUP BY source
- By status: COUNT(*) GROUP BY status
- Avg response time: AVG(first_response_time)
- Conversion rate: (won / total) * 100
```

**Implementation Steps:**

1. Create analytics queries in backend
2. Create `/api/analytics/summary` endpoint
3. Build analytics dashboard page
4. Display metrics in charts (Chart.js or Recharts)
5. Add date range selector
6. Cache analytics data for performance

**Validated Pain Point:** Can't measure performance or ROI (Customer Profiles, Pain #4)

---

#### US-5.3: Basic Inventory Management

**Priority:** SHOULD-HAVE
**Story:** As a sales manager, I want to add vehicles to inventory so AI can give accurate availability responses.

**Acceptance Criteria:**

- [ ] "Vehicles" page in dashboard
- [ ] Add/edit/delete vehicles
- [ ] Fields: make, model, year, price, status (available/sold)
- [ ] AI checks inventory when responding to leads
- [ ] AI mentions specific vehicles if available
- [ ] Dashboard shows vehicle count

**Implementation Steps:**

1. Create `vehicles` CRUD API
2. Create vehicles management page
3. Integrate inventory check into AI prompt
4. Update AI prompt to mention availability
5. Test AI responses with/without inventory

**Why It's Important:**

- Without inventory, AI says "I'll check if we have that" (weak response)
- With inventory, AI says "Yes, we have Model 3 in stock for 389,000 NOK" (strong response)

**Validated Pain Point:** Generic AI responses don't build trust (Customer Profiles, Pain #5)

---

## Technical Specifications

### Architecture Overview

```
┌──────────────────────────────────────────────────────────┐
│                    CLIENT LAYER                           │
│  Next.js Frontend (Vercel)                               │
│  - Dashboard UI                                           │
│  - Authentication (Clerk)                                 │
│  - Real-time updates                                      │
└──────────────────────────────────────────────────────────┘
                            │
                            ↓
┌──────────────────────────────────────────────────────────┐
│                    API LAYER                              │
│  FastAPI Backend (Railway/Render)                        │
│  - REST API endpoints                                     │
│  - Authentication middleware                              │
│  - Business logic                                         │
│  - Webhook receivers                                      │
└──────────────────────────────────────────────────────────┘
                            │
                ┌───────────┴───────────┐
                ↓                       ↓
┌──────────────────────────┐ ┌────────────────────────────┐
│    DATABASE LAYER        │ │   MESSAGE QUEUE LAYER      │
│  PostgreSQL (Supabase)   │ │   Redis + BullMQ           │
│  - Multi-tenant data     │ │   - Background jobs        │
│  - Row-level security    │ │   - Job scheduling         │
│  - Automated backups     │ │   - Retry logic            │
└──────────────────────────┘ └────────────────────────────┘
                            │
                            ↓
┌──────────────────────────────────────────────────────────┐
│               EXTERNAL INTEGRATIONS                       │
│  - Claude API (AI responses)                             │
│  - Resend/SendGrid (Email)                               │
│  - Twilio (SMS)                                           │
│  - Meta Graph API (Facebook)                             │
└──────────────────────────────────────────────────────────┘
```

---

### Authentication Flow

```
1. User visits norvalt.no/login
2. User clicks "Sign in with Clerk"
3. Clerk handles authentication (email/password or OAuth)
4. Clerk returns JWT with user_id and org_id
5. Frontend stores JWT in cookie/localStorage
6. Frontend includes JWT in Authorization header for API calls
7. Backend validates JWT using Clerk public key
8. Backend extracts dealership_id from org_id
9. Backend filters all queries by dealership_id
10. API returns data scoped to dealership
```

**Implementation:**

```python
# FastAPI middleware
from clerk import Clerk

@app.middleware("http")
async def verify_auth(request: Request, call_next):
    token = request.headers.get("Authorization")
    if not token:
        return JSONResponse(status_code=401, content={"error": "Unauthorized"})

    try:
        # Verify JWT with Clerk
        user = clerk.verify_token(token)

        # Extract dealership_id from organization
        dealership_id = get_dealership_id(user.org_id)

        # Add to request context
        request.state.dealership_id = dealership_id
        request.state.user_id = user.id

        return await call_next(request)
    except Exception as e:
        return JSONResponse(status_code=401, content={"error": "Invalid token"})
```

---

### Database Schema (Complete)

```sql
-- Dealerships (Organizations)
CREATE TABLE dealerships (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(255) NOT NULL,
  email VARCHAR(255) NOT NULL,
  phone VARCHAR(50),
  address TEXT,
  clerk_org_id VARCHAR(255) UNIQUE NOT NULL,
  subscription_status VARCHAR(50) DEFAULT 'active',
  subscription_tier VARCHAR(50) DEFAULT 'starter',
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_dealerships_clerk_org ON dealerships(clerk_org_id);

-- Users (Sales reps, managers, admins)
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  dealership_id UUID REFERENCES dealerships(id) ON DELETE CASCADE,
  clerk_user_id VARCHAR(255) UNIQUE NOT NULL,
  email VARCHAR(255) NOT NULL,
  name VARCHAR(255),
  role VARCHAR(50) DEFAULT 'sales_rep', -- admin, manager, sales_rep
  notification_preferences JSONB DEFAULT '{"sms": true, "email": true}',
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_users_dealership ON users(dealership_id);
CREATE INDEX idx_users_clerk ON users(clerk_user_id);

-- Leads (Customer inquiries)
CREATE TABLE leads (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  dealership_id UUID REFERENCES dealerships(id) ON DELETE CASCADE,

  -- Source tracking
  source VARCHAR(50) NOT NULL, -- website, email, facebook, manual
  source_url TEXT,
  source_metadata JSONB,

  -- Status
  status VARCHAR(50) DEFAULT 'new', -- new, contacted, qualified, won, lost

  -- Customer info
  customer_name VARCHAR(255),
  customer_email VARCHAR(255),
  customer_phone VARCHAR(50),

  -- Lead details
  vehicle_interest VARCHAR(255),
  initial_message TEXT,
  lead_score INTEGER DEFAULT 50, -- 1-100

  -- Assignment
  assigned_to UUID REFERENCES users(id),

  -- Timestamps
  created_at TIMESTAMP DEFAULT NOW(),
  last_contact_at TIMESTAMP,
  converted_at TIMESTAMP,

  -- Performance tracking
  first_response_time INTERVAL,

  CONSTRAINT valid_email CHECK (customer_email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$')
);

CREATE INDEX idx_leads_dealership ON leads(dealership_id);
CREATE INDEX idx_leads_status ON leads(status);
CREATE INDEX idx_leads_source ON leads(source);
CREATE INDEX idx_leads_created ON leads(created_at DESC);
CREATE INDEX idx_leads_email ON leads(customer_email);

-- Conversations (Message history)
CREATE TABLE conversations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  lead_id UUID REFERENCES leads(id) ON DELETE CASCADE,
  dealership_id UUID REFERENCES dealerships(id) ON DELETE CASCADE,

  -- Message details
  channel VARCHAR(50) NOT NULL, -- email, sms, facebook, manual
  direction VARCHAR(20) NOT NULL, -- inbound, outbound
  sender VARCHAR(255), -- customer name or "AI" or user name
  sender_type VARCHAR(20), -- customer, ai, human
  message_content TEXT NOT NULL,

  -- Metadata
  metadata JSONB,

  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_conversations_lead ON conversations(lead_id);
CREATE INDEX idx_conversations_created ON conversations(created_at DESC);

-- Vehicles (Basic inventory)
CREATE TABLE vehicles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  dealership_id UUID REFERENCES dealerships(id) ON DELETE CASCADE,

  -- Basic info
  make VARCHAR(100) NOT NULL,
  model VARCHAR(100) NOT NULL,
  year INTEGER,
  vin VARCHAR(17),

  -- Status
  status VARCHAR(50) DEFAULT 'available', -- available, sold, reserved

  -- Pricing
  price DECIMAL(10,2),

  -- Additional details
  mileage INTEGER,
  fuel_type VARCHAR(50),
  listing_url TEXT,

  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_vehicles_dealership ON vehicles(dealership_id);
CREATE INDEX idx_vehicles_status ON vehicles(status);

-- Automation Rules (Follow-up sequences)
CREATE TABLE automation_rules (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  dealership_id UUID REFERENCES dealerships(id) ON DELETE CASCADE,

  name VARCHAR(255) NOT NULL,
  trigger_type VARCHAR(50) NOT NULL, -- new_lead, no_response, time_based
  trigger_conditions JSONB,

  actions JSONB NOT NULL, -- [{type: "send_email", delay: "3 days", template_id: "..."}]

  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_automation_dealership ON automation_rules(dealership_id);

-- Row-Level Security Policies
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE vehicles ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their dealership's data
CREATE POLICY dealership_isolation_leads ON leads
  FOR ALL
  USING (dealership_id = current_setting('app.current_dealership_id')::uuid);

CREATE POLICY dealership_isolation_conversations ON conversations
  FOR ALL
  USING (dealership_id = current_setting('app.current_dealership_id')::uuid);

CREATE POLICY dealership_isolation_vehicles ON vehicles
  FOR ALL
  USING (dealership_id = current_setting('app.current_dealership_id')::uuid);
```

---

### API Contract Specification

#### Core Endpoints

```yaml
# Authentication
POST /api/auth/signup
  Request: {email, password, dealership_name}
  Response: {user_id, org_id, token}

POST /api/auth/login
  Request: {email, password}
  Response: {token}

# Leads
GET /api/leads
  Query: ?status=new&source=website&limit=25&offset=0&search=name
  Response: {leads: [...], total, page, pages}

GET /api/leads/:id
  Response: {lead: {...}, conversations: [...]}

POST /api/leads
  Request: {customer_name, customer_email, customer_phone, vehicle_interest, message, source}
  Response: {lead_id, status: "created"}

PATCH /api/leads/:id
  Request: {status?: string, assigned_to?: uuid, notes?: string}
  Response: {lead: {...}}

DELETE /api/leads/:id
  Response: {status: "deleted"}

# Conversations
GET /api/leads/:id/conversations
  Response: {conversations: [...]}

POST /api/conversations
  Request: {lead_id, message_content, channel}
  Response: {conversation_id}

# Vehicles
GET /api/vehicles
  Query: ?status=available
  Response: {vehicles: [...]}

POST /api/vehicles
  Request: {make, model, year, price, status}
  Response: {vehicle_id}

PATCH /api/vehicles/:id
  Request: {status?: string, price?: number}
  Response: {vehicle: {...}}

DELETE /api/vehicles/:id
  Response: {status: "deleted"}

# Analytics
GET /api/analytics/summary
  Query: ?start_date=2025-01-01&end_date=2025-01-31
  Response: {
    total_leads,
    by_source: {...},
    by_status: {...},
    avg_response_time,
    conversion_rate
  }

# Webhooks (Public - No Auth Required)
POST /webhooks/form/:dealership_id
  Request: {name, email, phone?, vehicle_interest?, message, source_url?}
  Response: {lead_id, status}

POST /webhooks/facebook
  Verification: GET with hub.challenge
  Request: Facebook lead notification
  Response: {status: "received"}

POST /webhooks/email
  Request: Email notification from importer
  Response: {status: "processed"}
```

---

### Background Job Architecture

```python
# Queue setup
from bullmq import Queue, Worker

# Queues
lead_processing_queue = Queue("lead-processing", connection=redis)
email_queue = Queue("email-send", connection=redis)
sms_queue = Queue("sms-send", connection=redis)
followup_queue = Queue("follow-up", connection=redis)

# Job types
jobs = {
    "process-new-lead": {
        "priority": "HIGH",
        "retry": 3,
        "timeout": 60000  # 60 seconds
    },
    "generate-ai-response": {
        "priority": "HIGH",
        "retry": 5,
        "timeout": 30000  # 30 seconds
    },
    "send-email": {
        "priority": "MEDIUM",
        "retry": 3,
        "timeout": 15000
    },
    "send-sms": {
        "priority": "MEDIUM",
        "retry": 3,
        "timeout": 10000
    },
    "follow-up-sequence": {
        "priority": "LOW",
        "retry": 2,
        "timeout": 30000
    }
}

# Worker: Process new lead
@worker("lead-processing")
async def process_new_lead(job):
    lead_id = job.data["lead_id"]
    dealership_id = job.data["dealership_id"]

    # 1. Fetch lead details
    lead = await db.fetch_lead(lead_id)

    # 2. Generate AI response
    ai_response = await claude_api.generate_response(lead)

    # 3. Send email
    await email_queue.add("send-email", {
        "to": lead.customer_email,
        "subject": f"Svar fra {dealership.name}",
        "body": ai_response
    })

    # 4. Send SMS to sales rep
    sales_rep = await db.fetch_assigned_rep(lead)
    await sms_queue.add("send-sms", {
        "to": sales_rep.phone,
        "message": f"New lead: {lead.customer_name} - {lead.vehicle_interest}"
    })

    # 5. Create conversation record
    await db.create_conversation({
        "lead_id": lead_id,
        "message_content": ai_response,
        "sender_type": "ai",
        "channel": "email"
    })

    # 6. Update lead status
    await db.update_lead(lead_id, {
        "status": "contacted",
        "last_contact_at": datetime.now(),
        "first_response_time": datetime.now() - lead.created_at
    })

    # 7. Schedule follow-up
    await followup_queue.add("follow-up-sequence", {
        "lead_id": lead_id
    }, {
        "delay": 3 * 24 * 60 * 60 * 1000  # 3 days
    })

    return {"status": "success"}
```

---

### Security Requirements Checklist

#### Data Protection

- [ ] All passwords hashed with bcrypt (handled by Clerk)
- [ ] All sensitive data encrypted at rest (Supabase default)
- [ ] HTTPS only for all API communication
- [ ] Environment variables for all secrets (no hardcoded keys)
- [ ] Database backups automated daily
- [ ] Row-level security enforced

#### API Security

- [ ] JWT-based authentication (Clerk)
- [ ] Rate limiting on public endpoints (10 req/min)
- [ ] Webhook signature verification (Facebook, email providers)
- [ ] Input validation on all endpoints (Pydantic models)
- [ ] SQL injection protection (parameterized queries)
- [ ] XSS protection (sanitize user inputs)
- [ ] CORS configured properly

#### GDPR Compliance

- [ ] Data residency in EU (Supabase EU region)
- [ ] Privacy policy and terms of service
- [ ] Cookie consent banner
- [ ] Unsubscribe links in all emails
- [ ] Right to be forgotten (lead deletion)
- [ ] Data export functionality
- [ ] User consent tracking

#### Monitoring & Alerts

- [ ] Error tracking (Sentry integration)
- [ ] Uptime monitoring (UptimeRobot or similar)
- [ ] API performance monitoring
- [ ] Database query performance
- [ ] Alert on critical errors (email/SMS)
- [ ] Log all webhook requests
- [ ] Track failed background jobs

---

## Implementation Roadmap

### Week 3 (Nov 4-10): Backend Foundation

**Day 1-2: Project Setup**

- [x] Initialize Git repositories (norvalt-backend, norvalt-frontend)
- [x] Initialize FastAPI project structure
- [x] Set up virtual environment and dependencies
- [x] Create `requirements.txt` with core packages
- [x] Initialize Next.js 14 project with App Router
- [x] Install and configure Shadcn UI
- [x] Set up development environment variables

**Dependencies:**

```bash
# Backend
pip install fastapi uvicorn sqlalchemy psycopg2-binary pydantic python-jose clerk-backend-api anthropic resend twilio redis bullmq sentry-sdk

# Frontend
npx create-next-app@latest norvalt-frontend
npx shadcn-ui@latest init
npm install @clerk/nextjs recharts date-fns
```

**Day 3: Database Setup**

- [x] Create Supabase project
- [x] Run database migrations (create all tables)
- [x] Set up RLS policies
- [x] Seed test data (2 dealerships, 10 leads each)
- [x] Test database connections

**Day 4-5: Core API**

- [x] Implement CRUD endpoints for leads
- [x] Implement authentication middleware
- [x] Set up API documentation (Swagger)
- [x] Write integration tests
- [ ] Deploy to Railway/Render staging

**Success Checkpoint:**

- Can create a lead via API (POST /api/leads)
- Can retrieve leads via API (GET /api/leads)
- Authentication works (JWT validation)
- Database queries respect multi-tenancy

---

### Week 4 (Nov 11-17): Authentication & Frontend

**Day 1-2: Clerk Integration**

- [x] Create Clerk application
- [x] Configure organizations (dealerships)
- [x] Integrate Clerk in Next.js frontend
- [x] Implement sign-up/login pages
- [x] Test organization creation

**Day 3-4: Dashboard Foundation**

- [x] Create dashboard layout (nav, sidebar)
- [x] Create leads list page
- [x] Fetch leads from API
- [x] Display leads in table/cards
- [x] Add basic styling

**Day 5: Testing & Deployment**

- [x] Create 2 test dealership accounts
- [x] Verify data isolation
- [x] Test authentication flow end-to-end
- [ ] Deploy frontend to Vercel staging (optional - can be done later)
- [x] Fix any critical bugs

**Success Checkpoint:**

- [x] Can sign up and log in ✅
- [x] Dashboard displays leads from API ✅
- [x] Data properly isolated between test accounts ✅
- [ ] Both frontend and backend deployed to staging (optional - deployment docs ready)

---

### Week 5 (Nov 18-24): Lead Capture - Website & Email

**Day 1-2: Website Form Webhook**

- [x] Implement `/webhooks/form/:dealership_id` endpoint
- [x] Add request validation (Pydantic model)
- [x] Implement duplicate detection
- [x] Create lead in database
- [x] Test with Postman/curl
- [x] Generate embed code for dealership websites

**Day 3-5: Email Monitoring**

- [ ] Set up test email account (Gmail or similar)
- [ ] Implement IMAP connection
- [ ] Create background worker (polls every 60s)
- [ ] Parse Toyota.no email template
- [ ] Parse VW.no email template
- [ ] Extract lead data from email
- [ ] Create lead in database
- [ ] Mark email as processed
- [ ] Test with real importer emails

**Success Checkpoint:**

- Website form webhook creates leads successfully
- Email monitor detects and processes importer emails
- Both sources create properly formatted leads in database
- Duplicate leads handled correctly

---

### Week 6 (Nov 25 - Dec 1): Lead Capture - Facebook & Dashboard Updates

**Day 1-3: Facebook Integration**

- [ ] Create Facebook App in Meta Business Suite
- [ ] Implement webhook verification (GET request)
- [ ] Implement webhook receiver (POST request)
- [ ] Verify Facebook signature
- [ ] Call Graph API to retrieve full lead data
- [ ] Map fields to Norvalt schema
- [ ] Test with test lead from Facebook

**Day 4-5: Dashboard Improvements**

- [ ] Add source filter (website, email, facebook)
- [ ] Add status filter
- [ ] Add date range filter
- [ ] Add search functionality
- [ ] Add pagination
- [ ] Style improvements

**Success Checkpoint:**

- All three lead sources (website, email, Facebook) working
- Dashboard displays leads from all sources
- Filters and search work correctly
- No critical bugs

---

### Week 7 (Dec 2-8): AI Engine - Foundation

**Day 1-2: Redis & Job Queue**

- [ ] Set up Redis instance (Upstash)
- [ ] Install and configure BullMQ
- [ ] Create job queues (ai-response, email-send, sms-send)
- [ ] Implement basic worker
- [ ] Test queue with dummy jobs

**Day 3-5: Claude API Integration**

- [ ] Get Claude API key
- [ ] Implement `ai_service.py` module
- [ ] Write system prompt for Norwegian responses
- [ ] Build context from lead data
- [ ] Call Claude API
- [ ] Test with 20+ different lead scenarios
- [ ] Refine prompt based on response quality
- [ ] Handle API errors gracefully

**Success Checkpoint:**

- Job queue processes jobs successfully
- Claude API returns quality Norwegian responses
- Responses are contextually relevant to vehicle interest
- Error handling works (API down, rate limits)

---

### Week 8 (Dec 9-15): AI Engine - Delivery

**Day 1-2: Email Sending**

- [ ] Sign up for Resend.com
- [ ] Verify domain
- [ ] Create email templates (HTML + plain text)
- [ ] Implement `send_email()` function
- [ ] Queue email sending jobs
- [ ] Test deliverability
- [ ] Handle bounce notifications

**Day 3-4: SMS Notifications**

- [ ] Sign up for Twilio
- [ ] Purchase Norwegian phone number
- [ ] Implement `send_sms()` function
- [ ] Queue SMS sending jobs
- [ ] Test SMS delivery
- [ ] Add cost tracking

**Day 5: Workflow Orchestration**

- [ ] Implement full auto-response workflow
- [ ] New lead → AI response → Email + SMS
- [ ] Update lead status after response
- [ ] Create conversation record
- [ ] Test end-to-end flow
- [ ] Measure response time (must be < 90s)

**Success Checkpoint:**

- New leads trigger automatic AI responses
- Emails delivered successfully
- SMS notifications sent to sales reps
- Full workflow completes within 90 seconds
- Conversation history stored correctly

---

### Week 9 (Dec 16-22): Dashboard Enhancements

**Day 1-2: Lead Detail Page**

- [ ] Create lead detail page UI
- [ ] Display customer profile card
- [ ] Display full conversation history
- [ ] Distinguish AI vs human messages
- [ ] Add manual reply form
- [ ] Implement status change dropdown
- [ ] Add real-time updates

**Day 3-4: Conversation Management**

- [ ] Implement "Take Over" button (disable AI)
- [ ] Add manual email/SMS reply
- [ ] Add internal notes functionality
- [ ] Show AI vs human sender clearly
- [ ] Test conversation flow

**Day 5: Real-Time Updates**

- [ ] Set up WebSocket or polling for new leads
- [ ] New leads appear in inbox automatically
- [ ] New messages appear in conversation view
- [ ] Test with multiple users

**Success Checkpoint:**

- Lead detail page shows all information
- Sales reps can manually reply to leads
- Conversation history is clear and complete
- Real-time updates work smoothly

---

### Week 10 (Dec 23-29): Automation & Inventory

**Day 1-2: Follow-Up Sequences**

- [ ] Create `automation_rules` table
- [ ] Implement Day 3 follow-up logic
- [ ] Implement Day 7 follow-up logic
- [ ] Generate AI follow-up messages
- [ ] Test automation with dummy leads
- [ ] Add UI to view scheduled follow-ups

**Day 3-4: Basic Inventory**

- [ ] Implement vehicles CRUD API
- [ ] Create vehicles management page
- [ ] Add/edit/delete vehicles UI
- [ ] Integrate inventory into AI context
- [ ] Test AI responses with inventory data

**Day 5: Lead Status Workflow**

- [ ] Implement status change API
- [ ] Track status history
- [ ] Update dashboard filters
- [ ] Test status transitions

**Success Checkpoint:**

- Follow-up sequences send messages on schedule
- Inventory management works
- AI mentions inventory availability
- Status workflow is clear

---

### Week 11 (Dec 30 - Jan 5): Analytics & Settings

**Day 1-2: Analytics Dashboard**

- [ ] Implement analytics queries
- [ ] Create `/api/analytics/summary` endpoint
- [ ] Build analytics page UI
- [ ] Display: total leads, by source, by status, conversion rate
- [ ] Add charts (pie chart, bar chart)
- [ ] Add date range selector

**Day 3-4: Settings & Configuration**

- [ ] Create settings page
- [ ] Dealership profile settings
- [ ] Team management (invite users)
- [ ] Notification preferences
- [ ] AI response template customization
- [ ] Test all settings

**Day 5: Error Handling & Logging**

- [ ] Integrate Sentry for error tracking
- [ ] Add comprehensive logging
- [ ] Test failure scenarios
- [ ] Implement error notifications

**Success Checkpoint:**

- Analytics provide useful insights
- Settings allow customization
- Errors are caught and logged
- Team management works

---

### Week 12 (Jan 6-12): Production Readiness & Polish

**Day 1-2: Security Audit**

- [ ] Review all endpoints for SQL injection vulnerabilities
- [ ] Test XSS protection
- [ ] Review CORS configuration
- [ ] Test rate limiting
- [ ] Review authentication flow
- [ ] Verify RLS policies
- [ ] Test data isolation thoroughly

**Day 3: Performance Optimization**

- [ ] Add database indexes
- [ ] Optimize slow queries
- [ ] Implement API caching where appropriate
- [ ] Compress images
- [ ] Minimize bundle size
- [ ] Load testing (100 concurrent users)

**Day 4: Documentation**

- [ ] Write user guide
- [ ] Write admin guide
- [ ] Document API endpoints
- [ ] Create troubleshooting guide
- [ ] Record demo video

**Day 5: Final Testing & Deployment**

- [ ] End-to-end testing
- [ ] User acceptance testing
- [ ] Fix all critical bugs
- [ ] Deploy to production
- [ ] Set up monitoring and alerts
- [ ] Create demo account

**Success Checkpoint:**

- MVP is production-ready
- Zero critical bugs
- Documentation complete
- Demo is polished
- Platform achieves 99.5% uptime target

**MILESTONE: MVP COMPLETE**

---

## Progress Tracking

### Phase 1: Foundation (Week 3-4)

**Week 3 Deliverables:**

- [x] Project repositories created
- [x] Database schema deployed
- [x] Core API endpoints functional
- [x] API documentation available
- [x] Backend deployed to staging

**Week 4 Deliverables:**

- [x] Clerk authentication integrated
- [x] Multi-tenant data isolation working
- [x] Dashboard displays leads
- [x] Frontend deployed to staging
- [x] 2 test dealerships created
- [x] **Clerk webhook provisioning implemented** - Automatic user/dealership creation

**Status:** [x] Completed

**Blockers:** **\*\*\*\***\*\***\*\*\*\***\_**\*\*\*\***\*\***\*\*\*\***

**Notes:** **\*\*\*\***\*\***\*\*\*\***\_**\*\*\*\***\*\***\*\*\*\***

---

### Phase 2: Lead Capture (Week 5-6)

**Week 5 Deliverables:**

- [x] Website form webhook functional
- [x] Email monitoring system working (SendGrid Inbound Parse + AI classification)
- [x] Email classification with Claude API (sales_inquiry, spam, other, uncertain)
- [x] Lead extraction from sales inquiry emails
- [x] Duplicate detection implemented (Message-ID based)

**Week 6 Deliverables:**

- [ ] Facebook webhook verified
- [ ] Facebook leads captured successfully
- [ ] Dashboard shows leads from all sources
- [ ] Filters and search working
- [ ] Pagination implemented

**Status:** [ ] Not Started | [ ] In Progress | [ ] Completed | [ ] Blocked

**Blockers:** **\*\*\*\***\*\***\*\*\*\***\_**\*\*\*\***\*\***\*\*\*\***

**Notes:** **\*\*\*\***\*\***\*\*\*\***\_**\*\*\*\***\*\***\*\*\*\***

---

### Phase 3: AI Engine (Week 7-9)

**Week 7 Deliverables:**

- [ ] Redis and BullMQ configured
- [ ] Claude API integrated
- [ ] AI generates quality Norwegian responses
- [ ] Job queue processes tasks

**Week 8 Deliverables:**

- [ ] Email sending system functional
- [ ] SMS notification system working
- [ ] Auto-response workflow complete
- [ ] Response time < 90 seconds

**Week 9 Deliverables:**

- [ ] Lead detail page functional
- [ ] Conversation history displayed
- [ ] Manual reply working
- [ ] Human takeover functional
- [ ] Real-time updates working

**Status:** [ ] Not Started | [ ] In Progress | [ ] Completed | [ ] Blocked

**Blockers:** **\*\*\*\***\*\***\*\*\*\***\_**\*\*\*\***\*\***\*\*\*\***

**Notes:** **\*\*\*\***\*\***\*\*\*\***\_**\*\*\*\***\*\***\*\*\*\***

---

### Phase 4: Polish (Week 10-12)

**Week 10 Deliverables:**

- [ ] Follow-up sequences working
- [ ] Inventory management functional
- [ ] AI uses inventory data
- [ ] Status workflow complete

**Week 11 Deliverables:**

- [ ] Analytics dashboard functional
- [ ] Settings page complete
- [ ] Team management working
- [ ] Error tracking integrated

**Week 12 Deliverables:**

- [ ] Security audit passed
- [ ] Performance optimized
- [ ] Documentation complete
- [ ] Production deployment successful
- [ ] Demo prepared

**Status:** [ ] Not Started | [ ] In Progress | [ ] Completed | [ ] Blocked

**Blockers:** **\*\*\*\***\*\***\*\*\*\***\_**\*\*\*\***\*\***\*\*\*\***

**Notes:** **\*\*\*\***\*\***\*\*\*\***\_**\*\*\*\***\*\***\*\*\*\***

---

## Definition of Done

### Feature-Level DoD

A feature is considered DONE when:

- [ ] Code is written and committed to Git
- [ ] Unit tests written and passing (backend only)
- [ ] Integration tests written and passing
- [ ] Code reviewed (self-review or peer review)
- [ ] Deployed to staging environment
- [ ] Manually tested on staging
- [ ] No critical bugs
- [ ] Documentation updated (if needed)
- [ ] Acceptance criteria met

### Epic-Level DoD

An epic is considered DONE when:

- [ ] All user stories completed
- [ ] End-to-end testing passed
- [ ] Performance benchmarks met
- [ ] Security review passed (if applicable)
- [ ] Deployed to production
- [ ] Validated with real users (if applicable)

### MVP-Level DoD

The MVP is considered DONE when:

- [ ] All core user stories completed
- [ ] All technical specifications met
- [ ] Security requirements checklist passed
- [ ] Performance targets met (response time, uptime)
- [ ] Documentation complete
- [ ] Demo prepared and polished
- [ ] Production deployment successful
- [ ] No critical bugs in production
- [ ] First demo delivered to prospect

---

## Quality Checklist

### Testing Requirements

**Unit Tests (Backend):**

- [ ] Test lead creation with valid data
- [ ] Test lead creation with invalid data
- [ ] Test duplicate detection logic
- [ ] Test authentication middleware
- [ ] Test AI response generation
- [ ] Test email parsing logic
- [ ] Target: 70% code coverage

**Integration Tests:**

- [ ] Test full lead capture flow (webhook → DB → AI → email)
- [ ] Test multi-tenant data isolation
- [ ] Test Facebook webhook verification
- [ ] Test email sending flow
- [ ] Test SMS sending flow
- [ ] Test follow-up sequence scheduling

**End-to-End Tests (Frontend):**

- [ ] Test user signup and login
- [ ] Test lead list page
- [ ] Test lead detail page
- [ ] Test filters and search
- [ ] Test manual reply
- [ ] Test status change

**Performance Tests:**

- [ ] API response time < 200ms (p95)
- [ ] Lead capture to AI response < 90 seconds
- [ ] Dashboard load time < 2 seconds
- [ ] Database queries < 100ms (p95)
- [ ] Load test: 100 concurrent users

**Security Tests:**

- [ ] Test SQL injection prevention
- [ ] Test XSS prevention
- [ ] Test authentication bypass attempts
- [ ] Test data isolation between dealerships
- [ ] Test rate limiting on public endpoints

---

### Performance Benchmarks

**Must Achieve:**

- Lead capture to AI response: **< 90 seconds** (target: < 60 seconds)
- API response time (p95): **< 200ms**
- Dashboard load time: **< 2 seconds**
- Database queries (p95): **< 100ms**
- Platform uptime: **> 99.5%**

**Monitoring:**

- Set up alerts for response time > 90 seconds
- Set up alerts for API errors > 1%
- Set up alerts for failed background jobs
- Set up alerts for downtime

---

## Risk Register

### Technical Risks

**Risk 1: AI API Rate Limits**

- **Likelihood:** Medium
- **Impact:** High (blocks core functionality)
- **Mitigation:**
  - Monitor usage closely
  - Implement queue to control request rate
  - Have fallback templates for simple responses
  - Budget for higher API tier if needed

**Risk 2: Email Deliverability Issues**

- **Likelihood:** Medium
- **Impact:** High (customers don't receive responses)
- **Mitigation:**
  - Use reputable email service (Resend/SendGrid)
  - Proper SPF/DKIM/DMARC setup
  - Monitor bounce rates
  - Have SMS as backup channel

**Risk 3: Webhook Reliability**

- **Likelihood:** Medium
- **Impact:** Medium (leads not captured)
- **Mitigation:**
  - Implement retry logic with exponential backoff
  - Log all webhook failures
  - Alert on high failure rates
  - Provide manual upload as backup

**Risk 4: Multi-Tenant Data Leaks**

- **Likelihood:** Low
- **Impact:** Critical (security breach, legal issues)
- **Mitigation:**
  - RLS policies at database level
  - Comprehensive integration tests
  - Regular security audits
  - Penetration testing before launch

**Risk 5: Third-Party API Changes**

- **Likelihood:** Low
- **Impact:** High (integration breaks)
- **Mitigation:**
  - Monitor API changelogs
  - Version all API integrations
  - Have alert for API errors
  - Build abstraction layers

### Project Risks

**Risk 6: MVP Takes Longer Than 10 Weeks**

- **Likelihood:** Medium
- **Impact:** High (delays customer acquisition)
- **Mitigation:**
  - Cut scope ruthlessly if behind schedule
  - Work longer hours if needed (but avoid burnout)
  - Get help from Sebastian or contractors
  - Use AI coding assistants aggressively

**Risk 7: Loss of Motivation**

- **Likelihood:** Medium (based on founder's pattern)
- **Impact:** Critical (project fails)
- **Mitigation:**
  - Weekly accountability check-ins with Sebastian
  - Celebrate small wins (weekly milestones)
  - Keep life vision visible (the farm)
  - Join founder community for support
  - No other projects until March

**Risk 8: First Customers Don't Convert**

- **Likelihood:** Low (warm network)
- **Impact:** High (delays profitability)
- **Mitigation:**
  - Offer generous pilot terms (reduced pricing)
  - Get feedback on objections and address
  - Improve demo based on learnings
  - Expand outreach beyond RSA network

---

## Success Criteria (Recap)

### Technical Success

- [ ] All three lead sources capture leads successfully (website, email, Facebook)
- [ ] AI responds to 95%+ of new leads within 90 seconds
- [ ] Multi-tenant architecture with proper data isolation
- [ ] Dashboard allows sales reps to manage leads end-to-end
- [ ] Platform achieves 99.5% uptime
- [ ] Zero critical security vulnerabilities
- [ ] All API endpoints documented and functional

### Business Success

- [ ] Week 12 (Jan 12): MVP is production-ready
- [ ] Week 14 (Jan 26): First paying customer signed
- [ ] Week 16 (Feb 9): 5 paying customers, no churn
- [ ] Week 20 (Mar 9): 8-10 paying customers, profitable (36-45K NOK MRR)

### User Success

- [ ] Sales reps can view all leads in one place
- [ ] Sales reps receive instant notifications for hot leads
- [ ] Sales reps can manage conversations from dashboard
- [ ] Dealerships report faster response times
- [ ] Dealerships report higher lead conversion rates
- [ ] No dealership experiences data leak or security issue

---

## Next Actions

### This Week (Week 3: Nov 4-10)

**Critical Path:**

1. Initialize both repositories (backend + frontend)
2. Set up database on Supabase
3. Implement core lead API endpoints
4. Deploy backend to staging
5. Verify multi-tenant architecture works

**Owner:** Nikolai
**Support:** Helios (technical guidance via Claude Code)
**Expected Completion:** November 10, 2025
**Success Checkpoint:** Can create and retrieve leads via API

---

## Connection to Vision

Every feature in this PRD is a step toward the farm in the Norwegian countryside. Every API endpoint deployed is another brick in the foundation. Every lead captured is proof this works.

**The Stakes:**

- 8-10 customers by March = 36-45K NOK/month
- That's 432-540K NOK/year net profit
- That's enough to buy land, plan the farm, achieve financial freedom
- This is not just code - this is the vehicle to your life vision

**The Commitment:**
This PRD is the roadmap. Follow it. Ship it. Win it.

When things get hard, remember why you're building this. Every dealership signed gets you closer to that farm. Every feature shipped is another brick in your family's future.

**Let's build Norvalt. Let's ship the MVP in 10 weeks. Let's make this the one that doesn't get quit.**

---

**Document Status:** ACTIVE
**Next Review:** End of Week 4 (November 17, 2025)
**Version History:**

- v1.0 (Nov 4, 2025): Initial PRD created, all MVP features defined

---

**END OF PRD**
