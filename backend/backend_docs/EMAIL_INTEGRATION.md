# Email Integration Guide

## Overview

The Email Integration feature allows car dealerships to automatically convert incoming sales emails into leads. Emails are received via **SendGrid Inbound Parse**, classified by AI (Claude API), and converted to leads if they're genuine sales inquiries.

---

## Architecture

```
┌─────────────────────────────────────────┐
│ Customer sends email to                 │
│ sales@dealership.com                    │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│ Email forwarded to                       │
│ dealership-abc123@leads.autolead.no     │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│ SendGrid Inbound Parse                  │
│ Parses email and sends webhook          │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│ POST /api/v1/emails/webhook/inbound     │
│ - Stores email in database              │
│ - Queues for processing                 │
│ - Returns 200 OK immediately            │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│ Background Processing                   │
│ 1. Pre-filter spam (rules-based)        │
│ 2. AI classification (Claude API)       │
│ 3. Lead extraction (if sales inquiry)   │
│ 4. Create lead in database              │
└─────────────────────────────────────────┘
```

---

## Database Schema

### `emails` Table

Stores all incoming emails with processing status and classification results.

```sql
CREATE TABLE emails (
    id UUID PRIMARY KEY,
    dealership_id UUID NOT NULL REFERENCES dealerships(id) ON DELETE CASCADE,
    lead_id UUID REFERENCES leads(id) ON DELETE SET NULL,

    -- Email metadata
    message_id VARCHAR(255) UNIQUE NOT NULL,
    from_email VARCHAR(255) NOT NULL,
    from_name VARCHAR(255),
    to_email VARCHAR(255) NOT NULL,
    subject VARCHAR(500),

    -- Email content
    body_text TEXT,
    body_html TEXT,
    raw_headers JSONB,
    attachments JSONB,

    -- Processing status
    processing_status VARCHAR(50) NOT NULL DEFAULT 'pending',
    classification VARCHAR(50),
    classification_confidence FLOAT,
    classification_reasoning TEXT,
    extracted_data JSONB,

    -- Error tracking
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,

    -- Timestamps
    received_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE
);
```

### `dealerships` Table (Extended)

Added email integration fields:

```sql
ALTER TABLE dealerships ADD COLUMN email_integration_enabled BOOLEAN DEFAULT FALSE;
ALTER TABLE dealerships ADD COLUMN email_forwarding_address VARCHAR(255) UNIQUE;
ALTER TABLE dealerships ADD COLUMN email_integration_settings JSONB;
```

---

## API Endpoints

### 1. Email Webhook (SendGrid Inbound Parse)

**Endpoint:** `POST /api/v1/emails/webhook/inbound`

**Authentication:** None (SendGrid webhook)

**Content-Type:** `multipart/form-data`

**Request Body:**
```
to: dealership-abc123@leads.autolead.no
from: John Doe <john@example.com>
subject: Interested in Toyota Corolla
text: Hi, I'd like to schedule a test drive...
html: <html>...</html>
headers: {"Message-Id": "...", ...}
```

**Response:**
```json
{
  "status": "ok",
  "message": "Email received and queued for processing",
  "email_id": "uuid"
}
```

---

### 2. List Emails

**Endpoint:** `GET /api/v1/emails/`

**Authentication:** Required (JWT)

**Query Parameters:**
- `skip` (int, default: 0): Pagination offset
- `limit` (int, default: 50): Page size
- `classification` (str, optional): Filter by classification (sales_inquiry, spam, other, uncertain)
- `processing_status` (str, optional): Filter by status (pending, processing, completed, failed)

**Response:**
```json
{
  "emails": [
    {
      "id": "uuid",
      "from_email": "customer@example.com",
      "subject": "Test drive inquiry",
      "classification": "sales_inquiry",
      "classification_confidence": 0.95,
      "processing_status": "completed",
      "received_at": "2025-11-10T10:30:00Z"
    }
  ],
  "total": 150,
  "page": 1,
  "page_size": 50
}
```

---

### 3. Get Email Details

**Endpoint:** `GET /api/v1/emails/{email_id}`

**Authentication:** Required (JWT)

**Response:**
```json
{
  "id": "uuid",
  "from_email": "customer@example.com",
  "from_name": "John Doe",
  "subject": "Test drive inquiry",
  "body_text": "Email content...",
  "classification": "sales_inquiry",
  "classification_confidence": 0.95,
  "classification_reasoning": "Customer is requesting a test drive...",
  "extracted_data": {
    "customer_name": "John Doe",
    "email": "customer@example.com",
    "phone": "+47 123 45 678",
    "car_interest": "Toyota Corolla",
    "inquiry_summary": "Customer wants to schedule a test drive",
    "urgency": "medium"
  },
  "lead_id": "uuid",
  "processing_status": "completed"
}
```

---

### 4. Reprocess Email

**Endpoint:** `POST /api/v1/emails/{email_id}/reprocess`

**Authentication:** Required (JWT)

**Use Cases:**
- Retry failed emails
- Reclassify uncertain emails
- Re-extract lead data after model improvements

**Response:** Same as Get Email Details

---

### 5. Get Email Integration Settings

**Endpoint:** `GET /api/v1/settings/email-integration`

**Authentication:** Required (JWT)

**Response:**
```json
{
  "email_integration_enabled": true,
  "email_forwarding_address": "dealership-abc123@leads.autolead.no",
  "instructions": "Setup instructions..."
}
```

---

### 6. Enable Email Integration

**Endpoint:** `POST /api/v1/settings/email-integration/enable`

**Authentication:** Required (JWT)

**Response:**
```json
{
  "email_integration_enabled": true,
  "email_forwarding_address": "dealership-abc123@leads.autolead.no",
  "instructions": "Email integration is now enabled! Forward emails to..."
}
```

---

### 7. Disable Email Integration

**Endpoint:** `POST /api/v1/settings/email-integration/disable`

**Authentication:** Required (JWT)

**Response:**
```json
{
  "email_integration_enabled": false,
  "email_forwarding_address": "dealership-abc123@leads.autolead.no",
  "instructions": "Email integration has been disabled..."
}
```

---

## Email Classification

### Pre-filtering (Rules-based)

Emails are pre-filtered for obvious spam before AI classification:

1. **Spam domain check**: Reject known spam domains
2. **Spam keywords**: Check subject/body for keywords like "unsubscribe", "viagra", "casino"
3. **Link count**: Reject emails with 10+ links (likely newsletters)
4. **Unsubscribe links**: Reject emails with unsubscribe links

### AI Classification (Claude API)

Emails that pass pre-filtering are sent to Claude for classification:

**Categories:**
- `sales_inquiry`: Customer interested in buying/test driving a car
- `spam`: Marketing emails, scams, irrelevant messages
- `other`: Internal communication, vendor emails
- `uncertain`: Cannot determine with confidence (needs human review)

**Output:**
```json
{
  "classification": "sales_inquiry",
  "confidence": 0.95,
  "reasoning": "Customer is requesting a test drive for Toyota Corolla and provided contact details"
}
```

---

## Lead Extraction

When an email is classified as `sales_inquiry`, Claude extracts structured lead data:

**Extracted Fields:**
- `customer_name`: Full name if mentioned
- `email`: Email address (defaults to sender)
- `phone`: Phone number if mentioned
- `car_interest`: Which car model(s) they're interested in
- `inquiry_summary`: Brief 1-2 sentence summary
- `urgency`: high|medium|low (based on language)
- `source`: toyota.no|volkswagen.no|direct_email|other

**Example:**
```json
{
  "customer_name": "John Doe",
  "email": "john@example.com",
  "phone": "+47 123 45 678",
  "car_interest": "Toyota Corolla 2024",
  "inquiry_summary": "Customer wants to schedule a test drive for next week",
  "urgency": "high",
  "source": "toyota.no"
}
```

This data is used to automatically create a lead in the database.

---

## SendGrid Setup

### Step 1: Create SendGrid Account

1. Sign up at https://sendgrid.com
2. Verify your email
3. Get your API key (Settings → API Keys)

### Step 2: Configure Inbound Parse

1. Go to **Settings → Inbound Parse**
2. Click **Add Host & URL**
3. Configure:
   - **Subdomain:** `leads`
   - **Domain:** `autolead.no`
   - **Destination URL:** `https://api.autolead.no/api/v1/emails/webhook/inbound`
   - **Check spam:** No
   - **Send raw:** No
   - **POST the raw MIME:** No

4. Verify DNS records:
   ```
   MX Record: mx.sendgrid.net (Priority: 10)
   ```

### Step 3: Test Webhook

Send a test email to `test-abc123@leads.autolead.no` and verify it appears in the emails table.

---

## Environment Variables

Add to `backend/.env`:

```env
# Anthropic API (for email classification)
ANTHROPIC_API_KEY=sk-ant-...
```

---

## Cost Estimation

### Anthropic API Costs

- **Model:** Claude 3.5 Sonnet
- **Classification:** ~500 tokens per email = $0.001
- **Lead extraction:** ~800 tokens per email = $0.002
- **Total per sales inquiry:** ~$0.003

**Monthly estimate for 1,000 emails:**
- Assuming 30% are sales inquiries: 300 emails
- Cost: 300 × $0.003 = **$0.90/month**

---

## Testing

### Manual Testing

1. Enable email integration for a dealership
2. Get the forwarding address from `/api/v1/settings/email-integration`
3. Send a test email to the forwarding address
4. Check `/api/v1/emails/` to see the email
5. Verify classification and lead creation

### Test Email Examples

**Sales Inquiry:**
```
To: dealership-abc123@leads.autolead.no
From: customer@example.com
Subject: Interested in Toyota Corolla

Hi, I saw your Toyota Corolla 2024 listing and would like to schedule a test drive.
My phone is +47 123 45 678. When is the earliest available time?

Best regards,
John Doe
```

**Spam:**
```
To: dealership-abc123@leads.autolead.no
From: marketing@spam.com
Subject: URGENT: You've won a prize!

Click here to claim your prize! Unsubscribe here.
```

---

## Troubleshooting

### Email not received

1. Check SendGrid logs (Activity → Activity Feed)
2. Verify MX records are configured correctly
3. Check that `email_integration_enabled = true` for dealership
4. Verify `email_forwarding_address` matches the "to" address

### Classification failed

1. Check `ANTHROPIC_API_KEY` is set
2. Check API quota/limits
3. View error in `emails.error_message` field
4. Retry with `/api/v1/emails/{id}/reprocess`

### Lead not created

1. Check `emails.classification = 'sales_inquiry'`
2. Check `emails.extracted_data` is populated
3. Check `emails.error_message` for lead creation errors
4. Verify RLS context is set correctly

---

## Future Enhancements

**Phase 2 (Later):**
- IMAP integration (direct mailbox access)
- Email threading (group related emails)
- Attachment handling (photos, documents)
- Reply detection (skip auto-replies)
- Custom classification rules per dealership
- Email templates for quick responses
- Sentiment analysis for lead scoring

---

## Security Considerations

1. **Webhook validation:** Consider adding SendGrid webhook signature verification
2. **Rate limiting:** Add rate limits to prevent abuse
3. **Deduplication:** Message-ID ensures emails aren't processed twice
4. **RLS policies:** All emails are scoped to dealerships
5. **API key security:** Store Anthropic API key in environment variables only
