# Facebook Lead Ads Integration - Setup Guide

This guide walks you through setting up Facebook Lead Ads integration for Autolead Platform. This integration automatically captures leads submitted through Facebook Lead Ad campaigns and creates them in Autolead in real-time.

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Meta for Developers Setup](#meta-for-developers-setup)
4. [Facebook App Configuration](#facebook-app-configuration)
5. [Webhook Setup](#webhook-setup)
6. [Page Access Token Generation](#page-access-token-generation)
7. [Backend Configuration](#backend-configuration)
8. [Testing](#testing)
9. [Troubleshooting](#troubleshooting)
10. [Known Limitations (MVP)](#known-limitations-mvp)

---

## Overview

### What This Integration Does

- **Automatic Lead Capture**: When a customer submits a Facebook Lead Ad form, the lead is instantly created in Autolead
- **Real-time Processing**: Leads appear in your dashboard within seconds
- **Field Mapping**: Facebook form fields (name, email, phone, vehicle interest) are automatically mapped to Autolead lead records
- **AI Response**: Autolead's AI automatically sends a response email to the customer
- **No Manual Downloads**: Eliminates the need to manually download CSV files from Facebook Ads Manager

### Architecture

```
Facebook Lead Ad → Facebook Webhook → Autolead Backend → Graph API → Create Lead → AI Response
```

---

## Prerequisites

Before starting, ensure you have:

- [ ] **Facebook Business Manager** account (business.facebook.com)
- [ ] **Facebook Page** associated with your dealership
- [ ] **Admin access** to both Business Manager and the Facebook Page
- [ ] **Autolead Backend** deployed with a public HTTPS URL (webhook endpoint)
- [ ] **Basic understanding** of Facebook Ads Manager (for testing)

---

## Meta for Developers Setup

### Step 1: Create Meta for Developers Account

1. Go to **[Meta for Developers](https://developers.facebook.com/)**
2. Click **"Get Started"** in the top right
3. Log in with your Facebook account (use the account that has admin access to your Business Manager)
4. Complete the registration process:
   - Accept the Terms of Service
   - Verify your email if prompted
   - Complete your developer profile

### Step 2: Create a Facebook App

1. From the [Meta for Developers Dashboard](https://developers.facebook.com/apps), click **"Create App"**
2. Select app type:
   - Choose **"Business"** as the app type
   - Click **"Next"**
3. Fill in app details:
   - **App Name**: `Autolead Integration - [Dealership Name]`
   - **App Contact Email**: Your dealership email
   - **Business Account**: Select your Business Manager account
   - Click **"Create App"**
4. You'll be redirected to the App Dashboard

### Step 3: Add Products to Your App

1. In the App Dashboard, find **"Add Products"** section
2. Add the following products:

#### A. Webhooks Product

1. Find **"Webhooks"** in the products list
2. Click **"Set Up"**
3. Keep this tab open - we'll configure webhooks later

#### B. Facebook Login Product (for Page Access Tokens)

1. Find **"Facebook Login"** in the products list
2. Click **"Set Up"**
3. No additional configuration needed at this stage

---

## Facebook App Configuration

### Step 4: Configure App Settings

1. In the App Dashboard, go to **Settings → Basic**
2. Note down the following credentials (you'll need these later):
   - **App ID**: `123456789012345` (example)
   - **App Secret**: Click **"Show"** to reveal, then copy it
3. Scroll down to **"App Domains"** section:
   - Add your Autolead backend domain: `api.autolead.no` (or your custom domain)
   - Click **"Save Changes"**

### Step 5: Set App to Live Mode

**Important**: Your app starts in Development Mode, which limits functionality.

1. In the App Dashboard, look for the toggle at the top: **"Development Mode"**
2. Before switching to Live Mode, ensure:
   - [ ] App has a Privacy Policy URL (add in Settings → Basic)
   - [ ] App has appropriate permissions configured
3. Toggle to **"Live Mode"**
4. Confirm the switch

---

## Webhook Setup

### Step 6: Generate Verify Token

In your backend `.env` file, generate a random verify token:

```bash
# Generate a secure random token (on Linux/Mac)
openssl rand -hex 32

# Or use this simple string for testing (replace in production!)
autolead_webhook_secret_2024
```

Add to your `.env`:

```env
FACEBOOK_VERIFY_TOKEN=your_generated_token_here
```

### Step 7: Configure Webhook in Meta App

1. In your Meta App Dashboard, go to **Products → Webhooks → Configuration**
2. Click **"Create Subscription"** or **"Edit Subscription"**
3. Select **"Page"** as the object type
4. Configure the webhook:

   **Callback URL**:
   ```
   https://api.autolead.no/api/v1/webhooks/facebook
   ```
   (Replace with your actual backend URL)

   **Verify Token**:
   ```
   your_generated_token_here
   ```
   (Use the same token from your `.env` file)

5. Click **"Verify and Save"**

**What happens**: Meta will send a GET request to your webhook URL to verify it's working. Your backend will respond with the challenge code.

**Expected response**: ✅ "Verified" message

### Step 8: Subscribe to Webhook Events

After verification succeeds:

1. In the Webhooks configuration, find the **"Page"** subscription
2. Click **"Add Subscription"**
3. Check the following webhook fields:
   - ✅ **leadgen** (this is the critical one for Lead Ads)
4. Click **"Save"**

---

## Page Access Token Generation

### Step 9: Link Facebook Page to App

1. In your Meta App Dashboard, go to **Add Products → Facebook Login**
2. On the left sidebar, click **"Tools" → "Access Token Tool"** (under Facebook Login product)
3. In the **"User or Page"** section:
   - Select **"Page Access Tokens"**
   - Click **"Add or Remove Pages"**
4. You'll be redirected to Facebook to authorize:
   - Select the Facebook Page(s) you want to connect
   - Grant **"Manage Pages"** and **"Read Lead Information"** permissions
   - Click **"Done"**

### Step 10: Generate Long-Lived Page Access Token

**Important**: The tokens shown in the Access Token Tool expire after 1 hour. You need a long-lived token.

#### Method 1: Using Graph API Explorer (Recommended)

1. Go to **[Graph API Explorer](https://developers.facebook.com/tools/explorer/)**
2. In the top right, select:
   - **Application**: Your created app (e.g., "Autolead Integration - Tesla Oslo")
   - Click **"Generate Access Token"**
3. In the permissions dialog:
   - Search for and add these permissions:
     - `pages_manage_metadata`
     - `pages_read_engagement`
     - `leads_retrieval`
   - Click **"Generate Access Token"**
4. Copy the generated token (this is still short-lived)
5. To convert to long-lived token, make this API request:

```bash
curl -X GET "https://graph.facebook.com/v21.0/oauth/access_token" \
  -d "grant_type=fb_exchange_token" \
  -d "client_id=YOUR_APP_ID" \
  -d "client_secret=YOUR_APP_SECRET" \
  -d "fb_exchange_token=SHORT_LIVED_TOKEN"
```

Response:
```json
{
  "access_token": "EAALxnzB...",  // This is your long-lived token (60 days)
  "token_type": "bearer"
}
```

#### Method 2: Using Meta Business Suite (Alternative)

1. Go to **[Meta Business Suite → Settings → Business Assets → Pages](https://business.facebook.com/settings/pages)**
2. Select your Page
3. Go to **"Page Access"** section
4. Generate a System User Token with long-lived access (this is more complex but tokens don't expire)

### Step 11: Store Page Access Token Securely

**For Development/Testing** (single dealership):
Add to `.env`:
```env
FACEBOOK_PAGE_ACCESS_TOKEN=EAALxnzB...your_token_here
```

**For Production** (multiple dealerships):
Store in database, encrypted:
```python
# In dealerships table:
# facebook_page_tokens = {
#   "page_id": "encrypted_access_token"
# }
```

---

## Backend Configuration

### Step 12: Update Environment Variables

Add all Facebook credentials to `backend/.env`:

```env
# Facebook Lead Ads Configuration
FACEBOOK_APP_ID=123456789012345
FACEBOOK_APP_SECRET=abc123def456ghi789jkl
FACEBOOK_VERIFY_TOKEN=your_generated_token_here
FACEBOOK_PAGE_ACCESS_TOKEN=EAALxnzB...long_lived_token

# Optional: Graph API Version (default: v21.0)
FACEBOOK_GRAPH_API_VERSION=v21.0
```

### Step 13: Update Backend Code

Ensure your backend has the Facebook webhook endpoint implemented:

**File: `backend/app/api/v1/endpoints/facebook.py`**

```python
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from fastapi.responses import PlainTextResponse
import hmac
import hashlib
from app.core.config import settings

router = APIRouter()

@router.get("/webhooks/facebook")
async def verify_facebook_webhook(request: Request):
    """Facebook webhook verification (GET request)."""
    params = request.query_params

    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == settings.FACEBOOK_VERIFY_TOKEN:
        print(f"✅ Facebook webhook verified successfully")
        return PlainTextResponse(content=challenge, status_code=200)
    else:
        raise HTTPException(status_code=403, detail="Verification failed")

@router.post("/webhooks/facebook")
async def receive_facebook_webhook(
    request: Request,
    background_tasks: BackgroundTasks
):
    """Receive Facebook leadgen webhook events."""
    # Implementation continues...
```

### Step 14: Restart Backend

```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload --port 8000
```

---

## Testing

### Step 15: Test Webhook Verification

1. In Meta App Dashboard, go to **Webhooks → Configuration**
2. Click **"Test"** next to your webhook subscription
3. You should see a ✅ success message

If it fails:
- Check that your backend is running and accessible via HTTPS
- Verify the `FACEBOOK_VERIFY_TOKEN` matches in both Meta App and `.env`
- Check backend logs for errors

### Step 16: Create a Test Lead Ad

1. Go to **[Facebook Ads Manager](https://www.facebook.com/adsmanager)**
2. Click **"Create"** → **"Lead"** campaign objective
3. Create a simple lead form:
   - **Form Type**: More volume
   - **Form Fields**:
     - Full Name (built-in)
     - Email (built-in)
     - Phone Number (built-in)
     - Add custom question: "Which vehicle are you interested in?" (short answer)
4. Complete the ad creation (you don't need to publish it for testing)

### Step 17: Test Lead Submission

#### Method 1: Facebook Test Tools (Recommended)

1. In Meta App Dashboard, go to **Lead Ads Testing Tool**:
   ```
   https://developers.facebook.com/tools/lead-ads-testing/
   ```
2. Select your app and page
3. Create a test lead:
   - Fill in: Name, Email, Phone, Vehicle Interest
   - Click **"Send"**
4. Facebook will send a webhook to your backend
5. Check your backend logs - you should see the webhook received
6. Check your database - a new lead should be created with `source='facebook'`

#### Method 2: Use Facebook Preview (Real Ad Test)

1. In Ads Manager, find your test ad
2. Click **"Preview"** or use the ad preview link
3. Click the lead form and submit it with test data
4. Check backend logs and database

### Step 18: Verify End-to-End Flow

**Expected Flow:**
1. ✅ Webhook received and logged
2. ✅ Signature verified
3. ✅ Lead ID extracted from payload
4. ✅ Graph API called to retrieve lead details
5. ✅ Lead created in database with `source='facebook'`
6. ✅ AI response triggered (email sent to customer)
7. ✅ Lead appears in Autolead dashboard

**Check Database**:
```sql
SELECT * FROM leads WHERE source = 'facebook' ORDER BY created_at DESC LIMIT 5;
```

**Check Lead Details**:
```sql
SELECT
  id,
  customer_name,
  customer_email,
  customer_phone,
  vehicle_interest,
  source_metadata
FROM leads
WHERE source = 'facebook'
ORDER BY created_at DESC;
```

The `source_metadata` field should contain the raw Facebook `field_data`.

---

## Troubleshooting

### Common Issues

#### 1. Webhook Verification Fails

**Symptom**: Meta shows "Verification Failed" when testing webhook

**Solutions**:
- ✅ Ensure backend is running and accessible via HTTPS
- ✅ Check `FACEBOOK_VERIFY_TOKEN` matches in `.env` and Meta App
- ✅ Verify the webhook URL is correct: `https://your-domain/api/v1/webhooks/facebook`
- ✅ Check backend logs for errors during verification
- ✅ Test webhook URL directly:
  ```bash
  curl -X GET "https://your-domain/api/v1/webhooks/facebook?hub.mode=subscribe&hub.verify_token=your_token&hub.challenge=test123"
  ```
  Should return: `test123`

#### 2. Webhook Received But Lead Not Created

**Symptom**: Webhook logs show request received, but no lead in database

**Solutions**:
- ✅ Check `X-Hub-Signature-256` validation - signature mismatch will reject webhook
- ✅ Verify Page Access Token is valid and has `leads_retrieval` permission
- ✅ Check Graph API call succeeds:
  ```bash
  curl -X GET "https://graph.facebook.com/v21.0/{leadgen_id}?access_token={page_access_token}"
  ```
- ✅ Check backend logs for errors in lead processing
- ✅ Verify `facebook_lead_id` deduplication logic isn't preventing creation

#### 3. Page Access Token Expired

**Symptom**: Graph API returns error: `(#190) Error validating access token: Session has expired`

**Solutions**:
- ✅ Page Access Tokens expire after 60 days (short-lived) or 1-2 months (long-lived)
- ✅ Regenerate long-lived token using the method in Step 10
- ✅ Consider implementing automatic token refresh logic
- ✅ For production, use System User tokens from Business Manager (never expire)

#### 4. Leads from One Page Work, Another Page Doesn't

**Symptom**: Leads from Page A are captured, but Page B leads fail

**Solutions**:
- ✅ Each page needs its own Page Access Token
- ✅ Verify the Page B is subscribed to your app's webhook
- ✅ Check Page B has granted `leads_retrieval` permission to your app
- ✅ In backend, ensure you're using the correct Page Access Token for each page

#### 5. Test Leads Triggering AI Responses

**Symptom**: Test leads sent from Facebook Test Tools trigger AI emails to fake addresses

**Solutions**:
- ✅ Facebook marks test leads with `is_test: true` flag
- ✅ Add check in backend to skip AI processing for test leads:
  ```python
  if lead_data.get("is_test"):
      print("Test lead detected, skipping AI response")
      return
  ```

#### 6. Webhook Signature Validation Fails

**Symptom**: Webhook rejected with 401 Unauthorized

**Solutions**:
- ✅ Ensure `FACEBOOK_APP_SECRET` in `.env` matches Meta App Dashboard
- ✅ Verify signature calculation:
  ```python
  expected_signature = hmac.new(
      app_secret.encode(),
      request_body,
      hashlib.sha256
  ).hexdigest()

  received_signature = request.headers.get("X-Hub-Signature-256").replace("sha256=", "")

  if expected_signature != received_signature:
      raise HTTPException(status_code=401)
  ```
- ✅ Check that you're reading the raw request body (not parsed JSON)

---

## Monitoring & Maintenance

### Webhook Health Check

Monitor webhook delivery in Meta App:
1. Go to **Webhooks → Configuration**
2. Check the **"Recent Deliveries"** section
3. Look for failed deliveries (red X)
4. Click to see error details

### Page Access Token Renewal

**Important**: Page Access Tokens expire. Set up monitoring:

1. **Check token expiry**:
   ```bash
   curl -X GET "https://graph.facebook.com/debug_token?input_token={token}&access_token={app_id}|{app_secret}"
   ```
   Response includes `expires_at` timestamp

2. **Set up renewal reminder**:
   - Add calendar reminder 1 week before expiry
   - Or implement automatic token refresh in backend

### Rate Limits

Facebook Graph API has rate limits:
- **200 calls per hour per user** (standard tier)
- **4,800 calls per hour** (with approved rate increase request)

If you expect high volume:
1. Go to **App Dashboard → Settings → Advanced**
2. Request **Rate Limit Increase**
3. Explain your use case (lead retrieval for dealerships)

---

## Production Checklist

Before going live:

- [ ] App is in **Live Mode** (not Development Mode)
- [ ] Privacy Policy URL added to app settings
- [ ] Page Access Tokens are **long-lived** (60+ days) or System User tokens
- [ ] Webhook URL uses **HTTPS** (not HTTP)
- [ ] `FACEBOOK_APP_SECRET` and `FACEBOOK_VERIFY_TOKEN` are securely stored
- [ ] Signature verification is enabled and tested
- [ ] Error handling and logging implemented
- [ ] Test lead detection logic works (skips AI for `is_test: true`)
- [ ] Deduplication logic tested (no duplicate leads)
- [ ] Monitoring set up for webhook failures
- [ ] Page Access Token expiry monitoring in place
- [ ] All dealership Facebook Pages are connected and tested

---

## Support & Resources

### Meta Documentation
- [Lead Ads API Documentation](https://developers.facebook.com/docs/marketing-api/guides/lead-ads/)
- [Webhooks for Pages](https://developers.facebook.com/docs/graph-api/webhooks/getting-started)
- [Graph API Explorer](https://developers.facebook.com/tools/explorer/)
- [Lead Ads Testing Tool](https://developers.facebook.com/tools/lead-ads-testing/)

### Autolead Support
- For integration issues, contact: support@autolead.no
- For Meta app setup help, check Meta Business Help Center

---

## Appendix: Example Webhook Payloads

### Example 1: Leadgen Webhook Event

```json
{
  "object": "page",
  "entry": [
    {
      "id": "987654321",
      "time": 1699901234,
      "changes": [
        {
          "field": "leadgen",
          "value": {
            "leadgen_id": "123456789",
            "page_id": "987654321",
            "form_id": "456789123",
            "adgroup_id": "789123456",
            "ad_id": "321654987",
            "created_time": 1699901234
          }
        }
      ]
    }
  ]
}
```

### Example 2: Graph API Lead Response

```json
{
  "created_time": "2024-11-13T10:30:00+0000",
  "id": "123456789",
  "ad_id": "321654987",
  "form_id": "456789123",
  "field_data": [
    {
      "name": "full_name",
      "values": ["Ola Nordmann"]
    },
    {
      "name": "email",
      "values": ["ola.nordmann@example.com"]
    },
    {
      "name": "phone_number",
      "values": ["+4712345678"]
    },
    {
      "name": "vehicle_interest",
      "values": ["Tesla Model 3 2024"]
    }
  ]
}
```

---

## Known Limitations (MVP)

The current implementation has the following limitations that will be addressed in future releases:

### 1. Single Dealership Support
- **Current Behavior**: All Facebook leads are assigned to the first dealership in the database
- **Impact**: Multi-tenant support not yet implemented for Facebook integration
- **Workaround**: Ensure only one dealership is configured during MVP testing
- **Future**: Page ID to dealership mapping will be implemented using `facebook_page_tokens` JSONB field

### 2. Single Page Access Token
- **Current Behavior**: Uses a single `FACEBOOK_PAGE_ACCESS_TOKEN` environment variable for all pages
- **Impact**: Cannot support multiple Facebook pages simultaneously
- **Workaround**: Configure one page per Autolead instance during MVP
- **Future**: Page-specific tokens will be retrieved from `dealerships.facebook_page_tokens` field

### 3. Token Storage
- **Current Behavior**: Page Access Tokens are stored in plain text in environment variables
- **Impact**: Tokens visible in environment configuration
- **Note**: In production, tokens should be encrypted before storing in the database
- **Future Options**:
  - Application-level encryption using cryptography.fernet
  - Database-level encryption using PostgreSQL pgcrypto extension
  - External secrets management (AWS Secrets Manager, Azure Key Vault)

### 4. No Retry Logic
- **Current Behavior**: Failed Graph API requests are logged but not retried
- **Impact**: Transient failures may result in lost leads
- **Future**: Implement exponential backoff retry logic for Graph API calls

### 5. No Rate Limit Handling
- **Current Behavior**: Rate limit errors are logged but not queued for retry
- **Impact**: Leads submitted during rate limiting may be lost
- **Future**: Implement queue-based processing with automatic retry

---

**Last Updated**: November 13, 2025
**Version**: 1.0
