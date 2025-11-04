# Norvalt Platform Architecture

## Executive Summary

Norvalt is built as a robust, scalable B2B SaaS platform designed to handle 100+ car dealerships with real-time lead processing, AI orchestration, and multi-tenant architecture. This is NOT a weekend project - it's a production-grade system built for reliability and growth.

## Core Technical Requirements

### Must Handle
- 500-1000+ leads per day across all customers
- Real-time webhook processing (Facebook, website forms)
- Background job processing (email monitoring, AI responses, follow-ups)
- Multi-tenant data isolation (each dealership's data separate)
- Norwegian language AI processing
- 99.5%+ uptime (dealerships depend on this for sales)

### Performance Targets
- Lead capture to AI response: < 90 seconds
- API response time: < 200ms (p95)
- Dashboard load time: < 2 seconds
- Database queries: < 100ms (p95)

---

## Tech Stack Decisions

### Frontend Stack

**Framework: Next.js 14 (App Router)**
- ✅ Server-side rendering for fast initial loads
- ✅ Built-in API routes for backend communication
- ✅ Excellent developer experience
- ✅ Production-ready with Vercel deployment

**UI Library: Shadcn UI + Tailwind CSS**
- ✅ Professional, modern B2B interface
- ✅ Accessible components out of the box
- ✅ Customizable without fighting the framework
- ✅ Consistent design system

**Authentication: Clerk**
- ✅ Multi-tenant support built-in (critical for B2B)
- ✅ Handles billing integration with Stripe
- ✅ User management and organizations
- ✅ Reduces auth complexity by 90%
- ⚠️ Cost: Free tier generous, scales with success

**Hosting: Vercel**
- ✅ Optimized for Next.js
- ✅ Automatic deployments
- ✅ Global CDN
- ✅ Easy scaling

**Decision Rationale:** This is the "fast food" stack for good reason - it's proven, well-documented, and lets us ship features fast. For B2B SaaS dashboard, this is ideal.

---

### Backend Stack

**Framework: FastAPI (Python)**
- ✅ Modern async support (critical for webhooks)
- ✅ Automatic API documentation
- ✅ Type hints and validation built-in
- ✅ Easier for founder to learn than Django
- ✅ Better for API-first architecture

**Why NOT Convex:**
- ❌ Cannot handle complex background jobs
- ❌ No proper message queue system
- ❌ Limited control over async workflows
- ❌ Not designed for webhook-heavy applications

**Why NOT Django:**
- Django is more opinionated, heavier
- FastAPI is faster to learn and iterate
- Better async support out of the box
- Modern API-first design

**Database: PostgreSQL (via Supabase)**
- ✅ Relational data model fits our needs
- ✅ Complex queries for analytics
- ✅ ACID compliance for financial data
- ✅ Supabase provides managed hosting + realtime features
- ✅ Free tier generous, easy migration later if needed

**Message Queue: Redis + BullMQ (or Celery)**
- ✅ Critical for async processing
- ✅ Handles webhook spikes gracefully
- ✅ Background job scheduling (follow-up sequences)
- ✅ Retry logic for failed tasks

**AI Integration: Claude API (Anthropic)**
- ✅ Best Norwegian language support
- ✅ Excellent for conversational responses
- ✅ Reliable API with good rate limits
- ✅ Context management capabilities

**Hosting: Railway or Render**
- ✅ Easy deployment for FastAPI
- ✅ Built-in PostgreSQL and Redis
- ✅ Auto-scaling
- ✅ Affordable for startup phase

---

## System Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────────┐
│                     NORVALT PLATFORM                     │
└─────────────────────────────────────────────────────────┘

FRONTEND (Next.js)
├─ Dealership Dashboard
├─ Lead Inbox (unified view)
├─ Customer Profiles
├─ Analytics & Reports
└─ Settings & Configuration

BACKEND API (FastAPI)
├─ Authentication & Authorization
├─ Lead Management API
├─ AI Orchestration
├─ Webhook Receivers
├─ Background Job Scheduler
└─ Integration APIs

DATABASE (PostgreSQL)
├─ dealerships (tenant isolation)
├─ users (sales reps, managers)
├─ leads (all customer inquiries)
├─ conversations (message history)
├─ vehicles (optional - Phase 2)
└─ automation_rules (follow-up sequences)

MESSAGE QUEUE (Redis + BullMQ)
├─ Webhook processing queue
├─ AI response generation queue
├─ Email/SMS sending queue
├─ Follow-up scheduler queue
└─ Analytics processing queue

EXTERNAL INTEGRATIONS
├─ Meta Graph API (Facebook Lead Ads)
├─ Email Provider (IMAP monitoring)
├─ Claude API (AI responses)
├─ Twilio (SMS)
├─ Stripe (billing - via Clerk)
└─ Webhook endpoints (website forms)
```

---

## Database Schema (MVP)

### Core Tables

**dealerships**
```sql
CREATE TABLE dealerships (
  id UUID PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  email VARCHAR(255) NOT NULL,
  phone VARCHAR(50),
  address TEXT,
  clerk_org_id VARCHAR(255) UNIQUE, -- Links to Clerk organization
  subscription_status VARCHAR(50), -- active, trial, cancelled
  subscription_tier VARCHAR(50), -- starter, professional, enterprise
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

**users**
```sql
CREATE TABLE users (
  id UUID PRIMARY KEY,
  dealership_id UUID REFERENCES dealerships(id),
  clerk_user_id VARCHAR(255) UNIQUE, -- Links to Clerk user
  email VARCHAR(255) NOT NULL,
  name VARCHAR(255),
  role VARCHAR(50), -- admin, sales_rep, manager
  notification_preferences JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);
```

**leads**
```sql
CREATE TABLE leads (
  id UUID PRIMARY KEY,
  dealership_id UUID REFERENCES dealerships(id),
  source VARCHAR(50) NOT NULL, -- website, email, facebook, manual
  status VARCHAR(50) DEFAULT 'new', -- new, contacted, qualified, won, lost
  
  -- Customer info
  customer_name VARCHAR(255),
  customer_email VARCHAR(255),
  customer_phone VARCHAR(50),
  
  -- Lead details
  vehicle_interest VARCHAR(255),
  initial_message TEXT,
  lead_score INTEGER, -- 1-100
  
  -- Assignment
  assigned_to UUID REFERENCES users(id),
  
  -- Metadata
  source_url TEXT,
  source_metadata JSONB,
  
  -- Timestamps
  created_at TIMESTAMP DEFAULT NOW(),
  last_contact_at TIMESTAMP,
  converted_at TIMESTAMP
);
```

**conversations**
```sql
CREATE TABLE conversations (
  id UUID PRIMARY KEY,
  lead_id UUID REFERENCES leads(id),
  dealership_id UUID REFERENCES dealerships(id),
  
  channel VARCHAR(50), -- email, sms, facebook, website
  direction VARCHAR(20), -- inbound, outbound
  
  sender VARCHAR(255), -- customer name or "AI" or user name
  sender_type VARCHAR(20), -- customer, ai, human
  
  message_content TEXT,
  metadata JSONB, -- channel-specific data
  
  created_at TIMESTAMP DEFAULT NOW()
);
```

**automation_rules**
```sql
CREATE TABLE automation_rules (
  id UUID PRIMARY KEY,
  dealership_id UUID REFERENCES dealerships(id),
  
  name VARCHAR(255),
  trigger_type VARCHAR(50), -- new_lead, no_response, time_based
  trigger_conditions JSONB,
  
  actions JSONB, -- Array of actions: send_email, send_sms, assign, etc.
  
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP DEFAULT NOW()
);
```

**vehicles**
```sql
CREATE TABLE vehicles (
  id UUID PRIMARY KEY,
  dealership_id UUID REFERENCES dealerships(id),
  
  -- Basic info
  make VARCHAR(100), -- Toyota, VW, Tesla
  model VARCHAR(100), -- RAV4, ID.4, Model 3
  year INTEGER,
  vin VARCHAR(17), -- Optional
  
  -- Status
  status VARCHAR(50) DEFAULT 'available', -- available, sold, reserved, demo_only
  
  -- Optional details
  price DECIMAL(10,2),
  mileage INTEGER,
  fuel_type VARCHAR(50), -- bensin, diesel, electric, hybrid
  listing_url TEXT, -- Link to Finn.no or importer page
  
  -- Metadata
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_vehicles_dealership ON vehicles(dealership_id);
CREATE INDEX idx_vehicles_status ON vehicles(status);
```

---

## API Design

### Core Endpoints

**Lead Management**
```
POST   /api/leads                  # Create new lead
GET    /api/leads                  # List leads (with filters)
GET    /api/leads/:id              # Get lead details
PATCH  /api/leads/:id              # Update lead status/details
DELETE /api/leads/:id              # Delete lead (soft delete)
```

**Conversations**
```
GET    /api/leads/:id/conversations # Get conversation history
POST   /api/conversations            # Add message to conversation
```

**Webhooks (Public)**
```
POST   /webhooks/facebook           # Facebook Lead Ads webhook
POST   /webhooks/form/:dealership   # Website form submissions
POST   /webhooks/email              # Email notification webhook
```

**AI Responses**
```
POST   /api/ai/generate-response    # Generate AI response for lead
POST   /api/ai/analyze-lead         # Analyze and score lead
```

**Vehicle Management (Basic)**
```
POST   /api/vehicles              # Add new vehicle
GET    /api/vehicles              # List vehicles (filter by status)
GET    /api/vehicles/:id          # Get vehicle details
PATCH  /api/vehicles/:id          # Update vehicle (mostly status changes)
DELETE /api/vehicles/:id          # Remove vehicle
GET    /api/vehicles/available    # Quick check: available vehicles
```

---

## Integration Architecture

### 1. Website Form Capture

```
Customer fills form → Webhook to Norvalt → Store in DB → Trigger AI response
```

**Implementation:**
- Provide embed code for dealership websites
- Webhook receiver validates and processes form data
- Background job generates and sends AI response
- Sales rep gets notification

### 2. Email Monitoring (Importer Portals)

```
Importer sends notification → IMAP polling → Parse email → Extract lead data → Store + AI response
```

**Implementation:**
- Set up dedicated email address for each dealership
- Background worker polls IMAP every 60 seconds
- Parse email template (Toyota.no, VW.no formats)
- Extract: customer name, email, phone, vehicle interest, message
- Create lead record + trigger AI response

### 3. Facebook Lead Ads

```
Customer submits FB form → Meta webhook → Norvalt receives → Process lead
```

**Implementation:**
- Meta Graph API integration
- Webhook verification (required by Meta)
- Field mapping (Meta form fields → Norvalt lead fields)
- Immediate AI response via Messenger or email

### 4. AI Response Generation

```
New lead detected → Queue job → Claude API call → Generate response → Send via email/SMS
```

**Implementation:**
- Background worker picks up job from queue
- Build context: lead details, vehicle interest, dealership info
- Call Claude API with Norwegian language prompt
- Template response with dealership branding
- Send via appropriate channel (email or SMS)
- Store conversation in DB

---

## Multi-Tenant Architecture

### Data Isolation Strategy

**Row-Level Security (RLS)**
- Every table has `dealership_id` column
- Database queries automatically filtered by dealership
- Prevents data leaks between customers

**Clerk Organization Mapping**
- Each Norvalt dealership = One Clerk organization
- Users belong to organizations
- Clerk handles user permissions and access control

**API Authentication Flow**
```
1. User logs in via Clerk
2. Clerk provides JWT with organization_id
3. API validates JWT
4. API extracts dealership_id from JWT
5. All queries filtered by dealership_id
```

---

## Background Job Processing

### Job Types

**1. Webhook Processing**
- Priority: HIGH
- Retry: 3 attempts
- Timeout: 10 seconds

**2. AI Response Generation**
- Priority: HIGH
- Retry: 5 attempts (API can fail)
- Timeout: 30 seconds

**3. Email/SMS Sending**
- Priority: MEDIUM
- Retry: 3 attempts
- Timeout: 15 seconds

**4. Follow-up Sequences**
- Priority: LOW
- Scheduled based on automation rules
- Retry: 2 attempts

**5. Analytics Processing**
- Priority: LOW
- Runs periodically (hourly/daily)
- No immediate retry needed

### Queue Implementation (BullMQ)

```javascript
// Example queue setup
const leadQueue = new Queue('lead-processing', {
  connection: redis,
  defaultJobOptions: {
    attempts: 3,
    backoff: {
      type: 'exponential',
      delay: 2000
    }
  }
});

// Worker
leadQueue.process('generate-ai-response', async (job) => {
  const { leadId, dealershipId } = job.data;
  
  // 1. Fetch lead details
  // 2. Call Claude API
  // 3. Send response via email/SMS
  // 4. Update lead status
  // 5. Notify sales rep
});
```

---

## Development Priorities (Ranked)

### Phase 1: Foundation (Weeks 3-4)
**Priority: CRITICAL**

1. **Project Setup**
   - Initialize Next.js + FastAPI projects
   - Set up Git repositories
   - Configure development environments
   - Deploy to staging environments

2. **Authentication System**
   - Integrate Clerk for frontend
   - Implement JWT validation in FastAPI
   - Set up multi-tenant user model
   - Test organization-based access control

3. **Database Schema**
   - Set up PostgreSQL via Supabase
   - Create core tables (dealerships, users, leads, conversations)
   - Implement RLS policies
   - Seed test data

4. **Basic API Structure**
   - CRUD endpoints for leads
   - API documentation (Swagger)
   - Error handling middleware
   - Request validation

**Milestone:** Can create/read leads via API with proper authentication

---

### Phase 2: Lead Capture (Weeks 5-6)
**Priority: CRITICAL**

1. **Website Form Webhook**
   - Public webhook endpoint
   - Form data validation
   - Lead creation flow
   - Error handling and logging

2. **Email Monitoring System**
   - IMAP connection to email server
   - Email parsing logic (Toyota.no, VW.no templates)
   - Lead extraction from email body
   - Background worker for polling

3. **Facebook Lead Ads Integration**
   - Meta Graph API setup
   - Webhook verification
   - Lead retrieval from Facebook
   - Field mapping

4. **Lead Deduplication**
   - Check for duplicate leads (email/phone matching)
   - Merge duplicate detection
   - Update existing lead vs create new

**Milestone:** All three lead sources successfully creating leads in database

---

### Phase 3: AI Response Engine (Weeks 7-9)
**Priority: CRITICAL**

1. **Claude API Integration**
   - API key management
   - Prompt engineering for Norwegian responses
   - Context building (lead details + dealership info)
   - Response quality testing

2. **Email Sending System**
   - SMTP integration (Resend or SendGrid)
   - Email templating
   - Deliverability optimization
   - Unsubscribe handling

3. **SMS Sending System** (Optional for MVP)
   - Twilio integration
   - Norwegian phone number validation
   - Cost tracking per SMS
   - Opt-out management

4. **Auto-Response Logic**
   - Trigger on new lead creation
   - Background job for AI generation
   - Send via appropriate channel
   - Log conversation in database

**Milestone:** New leads receive AI-generated responses within 90 seconds

---

### Phase 4: Dashboard & UX (Weeks 10-12)
**Priority: HIGH**

1. **Lead Inbox Interface**
   - List view with filters (status, source, date)
   - Search functionality
   - Real-time updates (new leads appear)
   - Pagination

2. **Lead Detail View**
   - Customer profile card
   - Full conversation history
   - Actions (change status, assign, add note)
   - Vehicle interest display

3. **Automation Rules UI**
   - Create follow-up sequences
   - Set notification preferences
   - Configure AI response templates
   - Test automation flows

4. **Basic Analytics Dashboard**
   - Lead count by source
   - Response times
   - Conversion rates
   - Sales rep performance

**Milestone:** Dealerships can manage leads end-to-end in dashboard

---

### Future Phases (Post-MVP)

**Phase 5: Advanced Automation**
- Complex follow-up sequences
- Lead scoring algorithms
- Predictive analytics
- A/B testing for AI responses

**Phase 6: Inventory Integration**
- Vehicle CRUD interface
- Link conversations to specific vehicles
- Inventory sync with external systems
- Pricing intelligence

**Phase 7: Advanced Analytics**
- Custom reports
- ROI calculation per lead source
- Sales funnel visualization
- Dealership benchmarking

**Phase 8: Additional Channels**
- WhatsApp Business API
- Instagram DMs
- Google Business Messages
- SMS two-way conversations

---

## Security & Compliance

### Data Protection
- All data encrypted at rest (Supabase default)
- HTTPS only for all API communication
- Row-level security in database
- Regular backups (automated via Supabase)

### GDPR Compliance
- Data residency in EU (Supabase EU region)
- User consent management
- Data export functionality
- Right to be forgotten (lead deletion)
- Privacy policy and terms of service

### API Security
- JWT-based authentication
- Rate limiting on public endpoints
- Webhook signature verification
- Input validation and sanitization
- SQL injection protection (parameterized queries)

---

## Monitoring & Observability

### Error Tracking
- Sentry integration for both frontend and backend
- Real-time error alerts
- Error grouping and prioritization

### Performance Monitoring
- API response time tracking
- Database query performance
- Background job success/failure rates
- AI API latency monitoring

### Business Metrics
- Daily active dealerships
- Leads processed per day
- AI response success rate
- Revenue metrics

---

## Deployment Strategy

### Environments

**Development**
- Local development on developer machines
- Connected to development database
- Mock external APIs when possible

**Staging**
- Vercel preview deployment for frontend
- Railway/Render staging environment for backend
- Separate staging database
- Used for testing before production

**Production**
- Vercel production for frontend
- Railway/Render production for backend
- Production database with backups
- Monitoring and alerts active

### CI/CD Pipeline

**Frontend (Next.js)**
- GitHub Actions trigger on push to main
- Run tests and linting
- Deploy to Vercel automatically
- Preview deployments for pull requests

**Backend (FastAPI)**
- GitHub Actions trigger on push to main
- Run tests (pytest)
- Deploy to Railway/Render
- Database migrations run automatically

---

## Cost Estimates (Monthly)

### MVP Phase (1-10 customers)
- Vercel: Free tier (sufficient)
- Railway/Render: $20-50
- Supabase: Free tier
- Clerk: Free tier (up to 10,000 users)
- Claude API: $50-100 (based on usage)
- Twilio (SMS): $20-50
- Domain + SSL: $15
- **Total: $105-215/month**

### Growth Phase (50 customers)
- Vercel: $20
- Railway/Render: $100-150
- Supabase: $25
- Clerk: $75 (charged per active user)
- Claude API: $300-500
- Twilio: $200
- Monitoring (Sentry): $25
- **Total: $745-970/month**

### Scale Phase (200 customers)
- Vercel: $20
- Railway/Render: $300-500
- Supabase: $100
- Clerk: $200
- Claude API: $1,500-2,000
- Twilio: $800
- Monitoring: $50
- **Total: $2,970-3,670/month**

**Infrastructure costs as % of revenue:**
- 10 customers @ 5K/month = 50K revenue = ~2% infrastructure
- 50 customers @ 5K/month = 250K revenue = ~0.4% infrastructure
- 200 customers @ 5K/month = 1M revenue = ~0.4% infrastructure

**Healthy unit economics throughout growth.**

---

## Technical Risks & Mitigations

### Risk 1: AI API Rate Limits
**Mitigation:** 
- Implement queue system to control request rate
- Fallback to simpler responses if API unavailable
- Cache common responses where appropriate

### Risk 2: Email Deliverability
**Mitigation:**
- Use reputable email service (Resend/SendGrid)
- Proper SPF/DKIM setup
- Monitor bounce rates and adjust

### Risk 3: Webhook Reliability
**Mitigation:**
- Implement retry logic with exponential backoff
- Log all webhook failures for debugging
- Alert on high failure rates

### Risk 4: Database Performance
**Mitigation:**
- Proper indexing on frequently queried columns
- Query optimization
- Connection pooling
- Monitor slow query log

### Risk 5: Multi-Tenant Data Leaks
**Mitigation:**
- RLS policies enforced at database level
- Comprehensive integration tests
- Regular security audits
- Principle of least privilege

---

## Success Criteria

### Technical Milestones
- [ ] Week 4: Authentication + database working
- [ ] Week 6: All three lead sources capturing successfully
- [ ] Week 9: AI responses being sent automatically
- [ ] Week 12: Full dashboard functional
- [ ] Week 14: First paying customer using system
- [ ] Week 16: 5 customers, no critical bugs
- [ ] Week 20: Platform handling 50+ leads/day reliably

### Performance Targets
- [ ] 99.5% uptime
- [ ] < 90 seconds lead capture to AI response
- [ ] < 200ms API response time (p95)
- [ ] Zero data loss incidents
- [ ] < 1% webhook failure rate

---

**Last Updated:** October 2025  
**Next Review:** After Week 4 (Foundation complete)
