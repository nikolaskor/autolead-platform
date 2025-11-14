# Multi-Tenant Email Setup Guide

## Overview

This document explains how email sending works in Autolead's multi-tenant architecture.

---

## Current Architecture (MVP)

### Inbound Emails (Receiving)
**How it works:**
```
Customer emails: sales@dealership.com
    ↓
Dealership forwards to: dealership-abc123@leads.autolead.no
    ↓
SendGrid Inbound Parse webhook
    ↓
Platform processes email
```

**Status:** ✅ Already implemented

---

### Outbound Emails (Sending)
**How it works:**
```
Platform sends AI response
    ↓
From: "Tesla Oslo <no-reply@autolead.no>"
Reply-To: "sales@teslaoslo.no"
    ↓
Customer receives email
    ↓
Customer clicks "Reply" → Goes to sales@teslaoslo.no ✅
```

**Status:** ✅ Implemented in this commit

---

## Why This Approach?

### Multi-Tenant Requirements
1. **Data Isolation** - Each dealership's emails must be separate
2. **Simple Onboarding** - No complex DNS setup per customer
3. **Scalability** - Support 100s of dealerships with one SendGrid account
4. **Cost Effective** - One SendGrid account ($15/month) for all customers

### Alternative Approaches Considered

#### ❌ Option 1: Each dealership has their own SendGrid account
- **Problem:** Not scalable, complex billing, hard to support
- **Cost:** $15/month × 100 dealerships = $1,500/month

#### ❌ Option 2: Domain verification per dealership
- **Problem:** Requires DNS access from each dealership
- **Onboarding:** 24-48 hours per customer (waiting for DNS propagation)
- **Support burden:** High (DNS troubleshooting)

#### ✅ Option 3: Shared sending domain (Current)
- **Benefit:** 5-minute onboarding per customer
- **Cost:** $15/month total
- **Scalability:** Supports 1000s of dealerships
- **Trade-off:** Emails come from `@autolead.no` not `@dealership.com`

---

## Customer Experience

### What the customer sees:
```
From: Tesla Oslo <no-reply@autolead.no>
Reply-To: sales@teslaoslo.no
Subject: Svar på din henvendelse - Tesla Model 3

Hei Ola!

[AI-generated Norwegian response]

Med vennlig hilsen,
Tesla Oslo
Telefon: +47 123 45 678
E-post: sales@teslaoslo.no
```

### What happens when customer replies:
✅ Reply goes to `sales@teslaoslo.no` (dealership's real email)
✅ Dealership receives it in their normal inbox
✅ Customer never sees `autolead.no` in reply chain

---

## Setup Process Per Dealership

### 1. Dealership Signs Up
```
1. Admin creates account in Clerk
2. Clerk webhook creates dealership record
3. Platform generates unique forwarding address
```

### 2. Configure Email (One-time, 5 minutes)
```
Dealership Settings:
- Name: "Tesla Oslo"
- Email: "sales@teslaoslo.no" ← Used for Reply-To
- Phone: "+47 123 45 678"
- Address: "Oslo, Norway"
```

### 3. Set Up Email Forwarding (Their email provider)
**Gmail/Google Workspace:**
```
Settings → Forwarding → Add: dealership-abc123@leads.autolead.no
```

**Outlook/Microsoft 365:**
```
Rules → Create Rule → Forward to: dealership-abc123@leads.autolead.no
```

### 4. Done! ✅
- Inbound emails → Platform receives via SendGrid Inbound Parse
- Outbound emails → Platform sends via SendGrid with Reply-To set

---

## Technical Implementation

### Code: Sending Emails
```python
# email_service.py
message = Mail(
    from_email=Email("no-reply@autolead.no", dealership.name),  # Shared domain
    to_emails=To(customer_email, customer_name),
    subject=subject,
    html_content=html_content
)

# Multi-tenant isolation via Reply-To
if dealership.email:
    message.reply_to = ReplyTo(dealership.email, dealership.name)

# Send via SendGrid
response = self.client.send(message)
```

### Database: Dealership Settings
```sql
-- dealerships table
CREATE TABLE dealerships (
    id UUID PRIMARY KEY,
    name VARCHAR(255),
    email VARCHAR(255),  -- Used for Reply-To
    phone VARCHAR(50),
    address TEXT,
    email_forwarding_address VARCHAR(255) UNIQUE,  -- Inbound address
    email_integration_enabled BOOLEAN DEFAULT FALSE
);
```

---

## SendGrid Configuration

### Required Setup (One-time)

1. **Verify Domain:**
   - Domain: `autolead.no`
   - Add DNS records (CNAME, TXT for DKIM)
   - Status: Must be "Verified" for sending

2. **API Key:**
   - Permissions: "Mail Send" (Full Access)
   - Stored in: `SENDGRID_API_KEY` env variable

3. **Inbound Parse:**
   - Already configured for `@leads.autolead.no`
   - Webhook: `https://api.autolead.no/api/v1/emails/webhook/inbound`

### DNS Records Required
```
Type    Name                        Value
CNAME   em1234.autolead.no          u12345.wl123.sendgrid.net
TXT     autolead.no                 v=spf1 include:sendgrid.net ~all
TXT     s1._domainkey.autolead.no   [SendGrid provides this]
```

**Status:** Must be set up before sending emails

---

## Deliverability Best Practices

### 1. SPF/DKIM/DMARC
- **SPF:** ✅ Configured via SendGrid DNS records
- **DKIM:** ✅ Configured via SendGrid DNS records
- **DMARC:** ⚠️ Recommended (add to DNS)

```
Type    Name            Value
TXT     _dmarc          v=DMARC1; p=none; rua=mailto:postmaster@autolead.no
```

### 2. Email Content Quality
- ✅ Personalized Norwegian responses (AI-generated)
- ✅ Plain text + HTML versions
- ✅ No spam trigger words
- ✅ Unsubscribe link (GDPR compliance)

### 3. Monitoring
- Track bounce rate (< 5%)
- Track spam complaints (< 0.1%)
- Monitor SendGrid reputation dashboard

---

## Future Enhancements (Post-MVP)

### Phase 2: OAuth Email Integration

**Goal:** Send emails truly from dealership's email account

**How it works:**
```
1. Dealership clicks "Connect Gmail" in dashboard
2. OAuth popup → Grant access to Google account
3. Platform sends via Gmail API using dealership's account
4. Email appears in dealership's "Sent" folder
5. Email truly comes from sales@dealership.com
```

**Implementation:**
```python
# Per-dealership email provider
if dealership.email_provider == "gmail":
    gmail_api.send_email(dealership.oauth_tokens, email_data)
elif dealership.email_provider == "outlook":
    microsoft_graph.send_email(dealership.oauth_tokens, email_data)
else:
    # Fallback to shared SendGrid
    sendgrid.send_email(email_data)
```

**Benefits:**
- ✅ Email comes from `@dealership.com` (not `@autolead.no`)
- ✅ Appears in dealership's Sent folder
- ✅ Better brand consistency
- ✅ Higher trust from customers

**Effort:** 2-3 weeks development

**Pricing Tier:** Premium feature ($7,500/month vs $4,500/month)

---

## Troubleshooting

### Issue: Emails not being delivered
**Check:**
1. SendGrid API key is valid (`SENDGRID_API_KEY` in `.env`)
2. Domain `autolead.no` is verified in SendGrid dashboard
3. Dealership email is set correctly in database
4. Check SendGrid activity logs for errors

### Issue: Customer replies not reaching dealership
**Check:**
1. `dealership.email` field is correct in database
2. Dealership's email inbox is working
3. No spam filters blocking emails from customers

### Issue: Emails going to spam
**Check:**
1. SPF/DKIM records are configured correctly
2. DMARC policy is set
3. Email content doesn't have spam trigger words
4. SendGrid sender reputation is good (> 95%)

---

## Cost Analysis

### MVP (8-10 customers)
- SendGrid: $15/month (40,000 emails/month)
- Average: 100 emails/customer/month = 1,000 emails/month
- **Cost per customer:** $1.50/month
- **Margin:** $4,500 - $1.50 = $4,498.50/month per customer

### Scale (100 customers)
- SendGrid: $15/month (still within 40,000 limit)
- Average: 10,000 emails/month
- **Cost per customer:** $0.15/month
- **Margin:** $4,500 - $0.15 = $4,499.85/month per customer

**Conclusion:** Email sending is negligible cost at scale

---

## Summary

✅ **MVP Approach:** Shared SendGrid domain with Reply-To
✅ **Onboarding Time:** 5 minutes per customer
✅ **Cost:** $15/month for all customers
✅ **Scalability:** Supports 1000s of dealerships
✅ **Deliverability:** High (with proper DNS setup)
⏳ **Future:** OAuth integration for true `@dealership.com` sending

This approach balances simplicity, cost, and scalability for MVP while leaving the door open for premium features in Phase 2.
