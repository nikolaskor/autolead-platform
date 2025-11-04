# Norvalt Product Roadmap - 20 Weeks to Profitability

## Mission Critical Deadline
**March 2025: Norvalt must be profitable**

This means:
- Platform is built and operational
- 8-10 paying customers
- Monthly revenue: 36,000-60,000 NOK
- Operating costs covered
- Sustainable business model proven

---

## Timeline Overview

```
OCTOBER 2025          NOVEMBER-JANUARY        FEBRUARY-MARCH
Week 1-2              Week 3-12               Week 13-20
┌────────────┐       ┌─────────────┐         ┌──────────────┐
│  CLEANUP   │  →    │  BUILD MVP  │    →    │   SCALE TO   │
│ PROJECTS   │       │  PLATFORM   │         │ PROFITABLE   │
└────────────┘       └─────────────┘         └──────────────┘

Clear the      Build core        Sign 8-10
deck for       platform          customers
100% focus     in 10 weeks       profitable
```

---

## PHASE 1: CLEANUP & PREPARATION

### Weeks 1-2 (Current - End of October 2025)

**Status:** In Progress  
**Goal:** Complete all existing client commitments, clear calendar for 100% Norvalt focus

#### Week 1 (Oct 21-27)
**Deliverables:**
- [ ] Complete Okei Handel Odoo automation
- [ ] Finalize scope for Ironman Pawning website
- [ ] Document all learnings from these projects (what worked, what didn't)

**Technical Prep:**
- [ ] Set up development environment (VS Code, Claude, Cursor)
- [ ] Create GitHub repositories (norvalt-frontend, norvalt-backend)
- [ ] Sign up for required services (Clerk, Supabase, Vercel, Railway)

**Business Prep:**
- [ ] List all 30-50 RSA contacts (potential customers)
- [ ] Draft initial outreach message
- [ ] Prepare demo script outline

**Success Criteria:**
- Okay Humble delivered and signed off
- Ironman Pawning scoped and timeline agreed
- Development tools ready to go

---

#### Week 2 (Oct 28 - Nov 3)
**Deliverables:**
- [ ] Complete Arven Honning website
- [ ] Final client handover and invoicing
- [ ] Close all other distractions

**Strategic Planning:**
- [ ] Review this roadmap document with CTO Helios
- [ ] Finalize MVP feature scope (no scope creep!)
- [ ] Set up Notion/project management for tracking

**Founder Mindset Prep:**
- [ ] Review life vision document (the farm, the freedom)
- [ ] Commit publicly to Sebastian about 100% focus
- [ ] Block calendar for deep work sessions (4-6 hours daily)

**Success Criteria:**
- All client projects complete and invoiced
- November 1st: Calendar clear, 100% Norvalt focus begins
- Mental commitment locked in (no shiny objects!)

---

## PHASE 2: MVP DEVELOPMENT

### Weeks 3-4: FOUNDATION (Nov 4-17)

**Goal:** Build the technical foundation that everything else depends on

#### Week 3 (Nov 4-10)
**Backend Setup:**
- [ ] Initialize FastAPI project structure
- [ ] Set up PostgreSQL database on Supabase
- [ ] Create core tables (dealerships, users, leads, conversations)
- [ ] Implement basic CRUD API endpoints for leads
- [ ] Set up API documentation (Swagger)

**Frontend Setup:**
- [ ] Initialize Next.js 14 project with App Router
- [ ] Install and configure Shadcn UI + Tailwind
- [ ] Set up basic routing structure (/dashboard, /leads, /settings)
- [ ] Create layout components (navbar, sidebar)

**DevOps:**
- [ ] Deploy backend to Railway/Render (staging environment)
- [ ] Deploy frontend to Vercel (staging)
- [ ] Set up CI/CD pipelines

**Daily Time Allocation:**
- 6-8 hours: Coding and building
- 1 hour: Learning/troubleshooting
- 30 min: Documentation

**Success Criteria:**
- ✅ Can create a lead via API
- ✅ Can view leads via API
- ✅ Basic frontend renders without errors

---

#### Week 4 (Nov 11-17)
**Authentication & Multi-Tenancy:**
- [ ] Integrate Clerk authentication
- [ ] Set up organizations (dealerships) in Clerk
- [ ] Implement JWT validation in FastAPI
- [ ] Row-level security in database (filter by dealership_id)
- [ ] Test multi-tenant data isolation

**Basic Dashboard:**
- [ ] Login/logout flow
- [ ] Dashboard homepage (empty state)
- [ ] Leads list page (read from API)
- [ ] Lead detail page (basic view)

**Testing:**
- [ ] Create 2 test dealerships
- [ ] Create 10 test leads in each
- [ ] Verify data isolation (Dealership A can't see Dealership B's data)

**Success Criteria:**
- ✅ Multi-tenant authentication working
- ✅ Can log in and see list of leads
- ✅ Data properly isolated between test accounts

---

### Weeks 5-6: LEAD CAPTURE SYSTEM (Nov 18 - Dec 1)

**Goal:** All lead sources successfully capturing leads into the system

#### Week 5 (Nov 18-24)
**Website Form Webhook:**
- [ ] Build public webhook endpoint (`/webhooks/form`)
- [ ] Handle form data validation
- [ ] Create lead record in database
- [ ] Test with simulated webhook calls
- [ ] Generate embed code for dealership websites

**Email Monitoring (Importer Portals):**
- [ ] Set up IMAP connection to email server
- [ ] Build email polling worker (checks every 60 seconds)
- [ ] Parse Toyota.no email template (extract: name, email, phone, vehicle, message)
- [ ] Parse VW.no email template
- [ ] Create lead from parsed email data

**Testing:**
- [ ] Send test emails to monitored inbox
- [ ] Verify leads are created correctly
- [ ] Test edge cases (malformed emails, missing data)

**Success Criteria:**
- ✅ Website form webhook creates leads successfully
- ✅ Email monitor detects new emails and creates leads
- ✅ Both lead sources visible in dashboard

---

#### Week 6 (Nov 25 - Dec 1)
**Facebook Lead Ads Integration:**
- [ ] Create Facebook App and get API credentials
- [ ] Set up webhook for lead form submissions
- [ ] Verify webhook with Facebook
- [ ] Map Facebook form fields to Norvalt lead fields
- [ ] Test with real Facebook Lead Ad

**Lead Deduplication:**
- [ ] Check for existing leads by email
- [ ] Check for existing leads by phone
- [ ] Decide: Update existing lead or create new?
- [ ] Implement merge logic

**Dashboard Improvements:**
- [ ] Add source filter (website, email, facebook)
- [ ] Add date range filter
- [ ] Show lead source icon/badge on each lead
- [ ] Basic search functionality

**Success Criteria:**
- ✅ All three lead sources working reliably
- ✅ Duplicates are detected and handled
- ✅ Dashboard shows leads from all sources

---

### Weeks 7-9: AI AUTO-RESPONSE ENGINE (Dec 2-22)

**Goal:** AI automatically responds to every new lead within 90 seconds

#### Week 7 (Dec 2-8)
**Redis & Job Queue Setup:**
- [ ] Set up Redis instance (Upstash or Railway)
- [ ] Install and configure BullMQ
- [ ] Create job queues (ai-response, email-send, sms-send)
- [ ] Build worker to process jobs
- [ ] Test queue with dummy jobs

**Claude API Integration:**
- [ ] Get Claude API key
- [ ] Build prompt for Norwegian car sales responses
- [ ] Test prompt with various lead scenarios
- [ ] Implement context building (lead details + dealership info)
- [ ] Handle API errors gracefully

**Testing AI Responses:**
- [ ] Test 20+ different lead inquiries
- [ ] Verify Norwegian language quality
- [ ] Check response relevance to vehicle interest
- [ ] Ensure professional tone

**Success Criteria:**
- ✅ Job queue processing works
- ✅ Claude API returns quality Norwegian responses
- ✅ Responses are contextually relevant

---

#### Week 8 (Dec 9-15)
**Email Sending System:**
- [ ] Set up email service (Resend or SendGrid)
- [ ] Build email templates (responsive HTML)
- [ ] Implement email sending function
- [ ] Handle bounce/error notifications
- [ ] Test deliverability

**SMS Sending System (Optional for MVP):**
- [ ] Set up Twilio account (or skip if email-only MVP)
- [ ] Implement SMS sending function
- [ ] Norwegian phone number validation
- [ ] Track SMS costs

**Auto-Response Workflow:**
- [ ] Trigger: New lead created → Queue AI response job
- [ ] Worker: Generate AI response using Claude
- [ ] Worker: Send email (and optionally SMS)
- [ ] Store conversation in database
- [ ] Update lead status

**Success Criteria:**
- ✅ New leads trigger automatic AI responses
- ✅ Emails are delivered successfully
- ✅ Response time < 90 seconds from lead capture

---

#### Week 9 (Dec 16-22)
**Sales Rep Notifications:**
- [ ] Implement SMS notification to sales rep on new lead
- [ ] Implement email notification to sales rep
- [ ] Include lead details and urgency indicator
- [ ] Test notification delivery

**Human Handoff:**
- [ ] Add "Take Over" button in dashboard
- [ ] Disable AI for specific conversation after handoff
- [ ] Log handoff action
- [ ] Show in UI when human is handling lead

**Conversation View:**
- [ ] Display full conversation history
- [ ] Show who sent each message (AI vs human vs customer)
- [ ] Add manual reply option (sales rep can reply from dashboard)
- [ ] Real-time updates (new messages appear automatically)

**Success Criteria:**
- ✅ Sales reps are notified immediately of new leads
- ✅ Human takeover works smoothly
- ✅ Full conversation history visible

---

### Weeks 10-12: AUTOMATION & POLISH (Dec 23 - Jan 12)

**Goal:** Complete MVP with follow-up automation and production-ready UI

#### Week 10 (Dec 23-29)
**Follow-Up Sequences:**
- [ ] Create automation_rules table and API
- [ ] Build simple sequence builder UI
- [ ] Implement Day 1, Day 3, Day 7 follow-up logic
- [ ] Schedule jobs for future follow-ups
- [ ] Test automation with dummy leads

**Lead Status Management:**
- [ ] Implement status workflow (new → contacted → qualified → won/lost)
- [ ] Add status change UI in dashboard
- [ ] Track status history
- [ ] Filter leads by status

**Customer Profile Cards:**
- [ ] Design customer profile view
- [ ] Show: contact info, vehicle interest, conversation history, notes
- [ ] Add notes functionality (sales reps can add internal notes)
- [ ] Show lead source and timestamp

**Basic Inventory (for AI Context):**
- [ ] Add vehicles table to database
- [ ] Build simple CRUD API for vehicles
- [ ] Create basic vehicle list interface (add/edit/delete)
- [ ] Integrate with AI: Pass available vehicles to Claude context
- [ ] Test AI response: "Do you have [car] in stock?"

**Success Criteria:**
- ✅ Follow-up automation sends messages on schedule
- ✅ Lead status workflow is clear and functional
- ✅ Customer profiles are informative

---

#### Week 11 (Dec 30 - Jan 5)
**Analytics Dashboard (Basic):**
- [ ] Show total leads count
- [ ] Show leads by source (website, email, facebook)
- [ ] Show average response time
- [ ] Show conversion rate (leads → qualified → won)
- [ ] Show leads by status (pie chart or bar chart)

**Settings & Configuration:**
- [ ] Dealership settings page (name, contact info)
- [ ] AI response template customization
- [ ] Notification preferences (SMS on/off, email frequency)
- [ ] Team management (add/remove sales reps)

**Error Handling & Logging:**
- [ ] Implement Sentry for error tracking
- [ ] Add comprehensive logging
- [ ] Create error notification system
- [ ] Test failure scenarios (API down, database error, etc.)

**Success Criteria:**
- ✅ Basic analytics provide useful insights
- ✅ Settings allow customization
- ✅ Errors are caught and logged

---

#### Week 12 (Jan 6-12)
**Production Readiness:**
- [ ] Security audit (SQL injection, XSS, CSRF)
- [ ] Performance optimization (database indexes, API caching)
- [ ] Mobile responsiveness check
- [ ] Browser compatibility testing
- [ ] Load testing (simulate 100 concurrent users)

**Documentation:**
- [ ] User guide for dealership staff
- [ ] Admin guide for setup and configuration
- [ ] API documentation
- [ ] Troubleshooting guide

**Demo Preparation:**
- [ ] Create demo account with realistic data
- [ ] Prepare demo script (10-minute walkthrough)
- [ ] Record demo video (for async demos)
- [ ] Create sales deck (problem, solution, pricing, ROI)

**Final Testing:**
- [ ] End-to-end testing of all workflows
- [ ] User acceptance testing (simulate real dealership usage)
- [ ] Fix all critical bugs
- [ ] Deploy to production environment

**Success Criteria:**
- ✅ MVP is production-ready
- ✅ Demo is polished and compelling
- ✅ Zero critical bugs in production

**🎉 MILESTONE: MVP COMPLETE**

---

## PHASE 3: CUSTOMER ACQUISITION & SCALE

### Weeks 13-16: FIRST CUSTOMERS (Jan 13 - Feb 9)

**Goal:** Sign 3-5 pilot customers, prove the MVP works in production

#### Week 13 (Jan 13-19)
**Outreach Campaign:**
- [ ] Send personalized emails to top 10 RSA contacts
- [ ] LinkedIn messages to 10 more prospects
- [ ] Book 5-7 demo calls for Week 14
- [ ] Prepare pilot offer: 25K setup + 4.5K/month (discounted)

**First Demos:**
- [ ] Conduct 3-5 demos
- [ ] Gather feedback on features, pricing, concerns
- [ ] Document objections and responses
- [ ] Follow up with proposals

**Customer Success Prep:**
- [ ] Create onboarding checklist
- [ ] Prepare training materials
- [ ] Set up support email (support@norvalt.no)
- [ ] Define SLA (response time, uptime guarantees)

**Success Criteria:**
- ✅ 5 demos completed
- ✅ At least 2 strong prospects interested
- ✅ Onboarding process documented

---

#### Week 14 (Jan 20-26)
**First Customer Onboarding:**
- [ ] Sign first customer contract! 🎉
- [ ] Complete technical setup (connect lead sources)
- [ ] Train sales team (1-hour session)
- [ ] Go live with first customer
- [ ] Daily check-ins first week (ensure success)

**Continued Outreach:**
- [ ] Book 5 more demos
- [ ] Follow up with Week 13 prospects
- [ ] Refine demo based on feedback
- [ ] Test closing techniques

**Product Iteration:**
- [ ] Fix bugs reported by first customer
- [ ] Implement quick wins (small feature requests)
- [ ] Improve onboarding based on learnings

**Success Criteria:**
- ✅ First paying customer live on platform
- ✅ Customer is actively using the system
- ✅ 3-5 more demos completed

**🎉 MILESTONE: FIRST PAYING CUSTOMER**

---

#### Week 15 (Jan 27 - Feb 2)
**Scale Customer Acquisition:**
- [ ] Sign customer #2
- [ ] Sign customer #3
- [ ] Onboard both customers simultaneously (test scalability)
- [ ] Continue demos (5 more)

**Referral Program:**
- [ ] Ask first customer for referral
- [ ] Create referral incentive (1 month free for successful referral)
- [ ] Update sales materials with case study

**Product Improvements:**
- [ ] Fix bugs reported by customers 1, 2, 3
- [ ] Improve dashboard performance
- [ ] Add most-requested features (if quick wins)

**Success Criteria:**
- ✅ 3 paying customers
- ✅ All customers actively using platform
- ✅ At least 1 referral lead

---

#### Week 16 (Feb 3-9)
**Expand Customer Base:**
- [ ] Sign customers #4 and #5
- [ ] Total: 5 paying customers
- [ ] Refine onboarding (make it faster and smoother)
- [ ] Create customer success playbook

**Revenue Checkpoint:**
- Current MRR: 5 × 4,500 = 22,500 NOK/month
- Costs: ~3,000 NOK/month (infrastructure + tools)
- **Net: ~19,500 NOK/month** (not yet profitable, but close!)

**Focus on Retention:**
- [ ] Weekly check-ins with all customers
- [ ] Measure: Lead volume, response times, conversion rates
- [ ] Gather testimonials and success stories
- [ ] Ensure all customers are happy (NPS check)

**Success Criteria:**
- ✅ 5 paying customers
- ✅ All customers actively engaged
- ✅ Zero churn
- ✅ Positive testimonials

**🎉 MILESTONE: 5 CUSTOMERS, REPEATABLE PROCESS**

---

### Weeks 17-20: PATH TO PROFITABILITY (Feb 10 - Mar 9)

**Goal:** Reach 8-10 customers, achieve profitability by March

#### Week 17 (Feb 10-16)
**Aggressive Sales Push:**
- [ ] Reach out to next 20 contacts from RSA network
- [ ] Book 10 demos this week
- [ ] Leverage social proof (5 existing customers)
- [ ] Sign customers #6 and #7

**Product Scaling:**
- [ ] Ensure platform handles 5-7 concurrent customers smoothly
- [ ] Monitor: API performance, database load, job queue
- [ ] Optimize slow queries
- [ ] Add monitoring dashboards

**Customer Success:**
- [ ] Bi-weekly check-ins with all customers
- [ ] Measure success metrics: leads captured, response times, conversions
- [ ] Create customer success report (show ROI)
- [ ] Use success data in sales conversations

**Success Criteria:**
- ✅ 7 paying customers
- ✅ Platform performance is stable
- ✅ Customers report measurable ROI

---

#### Week 18 (Feb 17-23)
**Continue Growth:**
- [ ] Sign customer #8
- [ ] Target: 10+ demos this week
- [ ] Expand outreach beyond RSA network (cold outreach, ads?)
- [ ] Experiment with LinkedIn ads to book demos

**Revenue Checkpoint:**
- Current MRR: 8 × 4,500 = 36,000 NOK/month
- Costs: ~4,000 NOK/month
- **Net: ~32,000 NOK/month** 🎉 **PROFITABLE!**

**Product Maturity:**
- [ ] Address all critical bugs
- [ ] Improve UI/UX based on feedback
- [ ] Add small but valuable features
- [ ] Start documenting product roadmap (post-MVP)

**Success Criteria:**
- ✅ 8 paying customers
- ✅ **PROFITABLE** (MRR > costs)
- ✅ Platform is stable and reliable

**🎉 MILESTONE: PROFITABLE BUSINESS**

---

#### Week 19 (Feb 24 - Mar 2)
**Solidify Position:**
- [ ] Sign customers #9 and #10
- [ ] Total: 10 paying customers
- [ ] MRR: 45,000 NOK/month
- [ ] Net profit: ~40,000 NOK/month

**Optimize Operations:**
- [ ] Streamline onboarding (goal: < 1 day to go live)
- [ ] Create self-serve resources (video tutorials, FAQ)
- [ ] Improve support efficiency (templated responses, faster resolution)
- [ ] Hire part-time support person? (if needed)

**Customer Retention Focus:**
- [ ] Conduct 30-day success reviews with each customer
- [ ] Identify at-risk customers (low usage, complaints)
- [ ] Proactively address concerns
- [ ] Gather feature requests for roadmap

**Success Criteria:**
- ✅ 10 paying customers
- ✅ Consistent 45K+ MRR
- ✅ Zero churn
- ✅ Efficient operations

---

#### Week 20 (Mar 3-9)
**Celebrate & Reflect:**
- [ ] **MILESTONE ACHIEVED: Profitable by March** 🎉
- [ ] Team celebration (you and Sebastian!)
- [ ] Review what worked, what didn't
- [ ] Document lessons learned

**Plan Next Phase:**
- [ ] Set Q2 2025 goals (20 customers? 100K MRR?)
- [ ] Identify next features to build
- [ ] Consider: Self-serve platform? Marketing automation?
- [ ] Hiring plan (if growth justifies it)

**Business Fundamentals:**
- [ ] Set up proper accounting (Tripletex or similar)
- [ ] Separate business/personal finances
- [ ] Start saving for taxes
- [ ] Consider reinvestment strategy

**Success Criteria:**
- ✅ 10+ paying customers
- ✅ 40-50K NOK/month net profit
- ✅ Sustainable, profitable business
- ✅ Clear plan for next 6 months

**🎉 ULTIMATE MILESTONE: NORVALT IS PROFITABLE AND SUSTAINABLE**

---

## Key Metrics to Track Weekly

### Product Metrics
- **Lead Capture Rate:** % of leads successfully captured (target: > 99%)
- **AI Response Time:** Seconds from lead capture to AI response (target: < 90s)
- **AI Response Success:** % of leads that receive AI response (target: > 95%)
- **Platform Uptime:** % time platform is accessible (target: > 99.5%)

### Customer Metrics
- **Leads Per Customer:** Average leads per customer per week
- **Customer Engagement:** % of customers logging in daily (target: > 80%)
- **Customer Satisfaction:** NPS score (target: > 40)
- **Feature Requests:** Track common requests for roadmap

### Business Metrics
- **Weekly Demos:** Number of demos conducted
- **Demo-to-Customer Rate:** % of demos that convert to customers
- **MRR:** Monthly recurring revenue
- **Customer Churn:** % of customers canceling (target: < 5%)
- **CAC:** Customer acquisition cost (target: < 10,000 NOK)

---

## Risk Mitigation Plan

### Risk 1: MVP Takes Longer Than 10 Weeks
**Mitigation:**
- Cut scope ruthlessly (remove non-critical features)
- Work longer hours if needed (but avoid burnout)
- Get help from Sebastian if possible
- Use AI coding assistants more aggressively

### Risk 2: First Customers Don't Convert
**Mitigation:**
- Offer generous pilot terms (1 month free trial?)
- Get feedback on objections and address them
- Improve demo to be more compelling
- Expand outreach beyond RSA network

### Risk 3: Platform Has Critical Bugs in Production
**Mitigation:**
- Thorough testing before each customer onboarding
- Have rollback plan for deployments
- 24/7 monitoring with alerts
- Commit to fixing critical bugs within 24 hours

### Risk 4: Lose Motivation Mid-Build
**Mitigation:**
- Weekly accountability check-ins with Sebastian
- Celebrate small wins (Week 4, Week 8, Week 12)
- Keep life vision visible (the farm, the freedom)
- Join founder community for support

### Risk 5: Shiny Object Syndrome Returns
**Mitigation:**
- Public commitment to 100% Norvalt focus
- No other projects until March
- Block distractions (social media, YouTube)
- Remind yourself: This is the vehicle to the farm

---

## Decision Framework for Roadmap Changes

### When to ADD a feature:
- 3+ customers request the same thing
- It directly impacts conversion or retention
- Can be built in < 1 week
- Aligns with validated customer pain points

### When to REMOVE a feature from roadmap:
- No customers ask for it after 5+ demos
- Too complex for MVP (saves for later)
- Doesn't impact core value proposition
- Can be faked/done manually temporarily

### When to PUSH BACK a feature:
- Nice-to-have, not must-have
- Only 1 customer requests it
- Would take > 2 weeks to build
- Can wait until post-MVP

### When to ACCELERATE a feature:
- All customers need it immediately
- Blocking customer success
- Competitive differentiator
- Quick win (< 2 days to build)

---

## Daily Habits for Success

### Morning Routine (30 minutes)
1. Review life vision (the farm, the why)
2. Check: Yesterday's progress vs. plan
3. Identify: Today's ONE critical task
4. Block calendar for deep work (4-6 hours)

### Deep Work Sessions (4-6 hours)
1. Phone on airplane mode
2. Close all non-essential tabs
3. Use Cursor + Claude for coding
4. Take 5-min breaks every hour

### Evening Review (15 minutes)
1. What did I ship today?
2. What's blocking me?
3. What's tomorrow's priority?
4. Update progress tracker

### Weekly Review (60 minutes)
1. Review this roadmap document
2. Update status of all milestones
3. Identify: On track or behind?
4. Adjust plan if needed
5. Celebrate wins with Sebastian

---

## Commitment Contract

**I, Nikolai Skorodihin, commit to:**

1. **100% Focus:** No other projects, no shiny objects, until Norvalt is profitable (March 2025)
2. **Daily Execution:** 6-8 hours/day of focused work on Norvalt
3. **Weekly Accountability:** Check-ins with Sebastian every Friday
4. **No Excuses:** When obstacles arise, I find solutions, not reasons to quit
5. **Customer-First:** Every decision based on validated customer needs
6. **Ship, Don't Perfect:** MVP is good enough; iteration comes after launch
7. **The Why:** This is the vehicle to my farm, my freedom, my family's future

**Signed:** [Founder Signature]  
**Date:** [Date when commitment is made]  
**Witness:** Sebastian [Co-Founder]

---

## Success Mantra

> "Every dealership I sign gets me closer to that farm.  
> Every feature I ship is another brick in my family's foundation.  
> Every lead I capture is proof this works.  
> I will not give up. I will not get distracted.  
> This is Norvalt. This is my mission. This is my future."

---

**Let's build this. Let's ship this. Let's win this.** 🚀

---

**Last Updated:** October 2025  
**Next Review:** End of Week 4 (Foundation milestone)
