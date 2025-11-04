# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the **NorvaltPlatform** repository - the planning and documentation hub for Norvalt, an AI-powered lead management platform for Norwegian car dealerships.

**Current Stage:** Pre-development (documentation and planning phase)
**Goal:** Build MVP by mid-January 2025, achieve profitability (8-10 customers) by March 2025

## Repository Structure

This repository contains strategic documentation, NOT code:

- `COMPANY_CONTEXT.md` - Mission, value proposition, market positioning, competitive advantages
- `PLATFORM_ARCHITECTURE.md` - Technical stack decisions, database schema, API design, deployment strategy
- `CUSTOMER_PROFILES.md` - ICP definition, validated pain points, use cases, objection handling
- `PRODUCT_ROADMAP.md` - 20-week execution plan with milestones and success criteria
- `HELIOS_SYSTEM_PROMPT.md` - CTO persona and technical guidance principles
- `.claude/agents/` - Custom Claude Code agents (norvalt-cro-sales-strategist)

## Core Platform Concept

**Value Proposition:** Capture leads from all sources (website forms, email, Facebook ads, importer portals) and respond with AI in <90 seconds, 24/7.

**Target Market:** Norwegian car dealerships (10-200 employees, 50-300 cars/year)

**Business Model:** 35K NOK setup + 6K NOK/month SaaS subscription

**Tech Stack (Approved):**
- Frontend: Next.js 14 + Shadcn UI + Clerk (auth) + Vercel
- Backend: FastAPI + PostgreSQL (Supabase) + Redis/BullMQ + Railway/Render
- AI: Claude API (Norwegian language responses)
- Integrations: Meta Graph API, IMAP email monitoring, Twilio SMS

## Working with This Repository

### When Planning Features
1. Always validate against `CUSTOMER_PROFILES.md` - Was this pain point validated?
2. Check `PLATFORM_ARCHITECTURE.md` - Does it fit the approved tech stack?
3. Reference `PRODUCT_ROADMAP.md` - Is this in scope for current phase?
4. Challenge scope creep ruthlessly - MVP first, expansion later

### When Making Technical Decisions
1. Prioritize: Customer value > Technical elegance
2. Ask: "Does this help sign the first 10 dealerships?"
3. Prefer: Managed services over custom builds (Clerk > custom auth)
4. Focus: Multi-tenant B2B SaaS from day one, not retrofitted later

### When Adding Documentation
- Update relevant .md files, don't create new ones unnecessarily
- Keep documentation actionable and decision-focused
- Connect technical choices to business outcomes (revenue, customer satisfaction)

## MVP Scope (Weeks 3-12)

**Core Modules:**
1. Multi-source lead capture (website, email, Facebook)
2. AI auto-response system (Norwegian language via Claude API)
3. Unified lead inbox with conversation history
4. Basic automation (notifications, follow-up sequences)

**Explicitly OUT of scope:**
- Advanced analytics/reporting
- Marketing campaign builder
- Instagram/WhatsApp integration
- Service appointment booking
- Accounting integrations

## Critical Constraints

**Time:** 20 weeks to profitability (March 2025 deadline)
**Focus:** Norwegian market only, automotive only, dealerships only
**Scale:** Optimize for 10 customers, not 1000 (scale later)
**Language:** Norwegian + English (Norwegian is critical for AI responses)

## Founder Context

**Background:** Former RSA regional manager, understands automotive workflows, has 30-50 warm dealership contacts
**Technical Level:** Comfortable with basics (HTML/CSS/JS), learning FastAPI/React with AI assistance
**Pattern:** Strong starter, history of not shipping - needs accountability and milestone structure

## Key Principles

1. **Validate Before Building** - Every feature must trace to validated customer pain
2. **MVP Over Perfect** - Ship fast, iterate based on real feedback
3. **Robust Over Clever** - Production-grade architecture, not weekend hackathon code
4. **Customer Conversations > Code** - Time spent with dealerships is more valuable than refactoring
5. **Shipping Beats Planning** - Bias toward action, not analysis paralysis

## Decision Framework

**Add feature if:**
- 3+ customers request it AND it impacts conversion/retention AND can be built in <1 week

**Remove feature if:**
- No customers ask for it after 5+ demos OR too complex for MVP OR doesn't impact core value prop

**Push back feature if:**
- Nice-to-have, not must-have OR only 1 customer wants it OR would take >2 weeks

## Using the CRO Sales Strategist Agent

A specialized agent (`norvalt-cro-sales-strategist`) exists for sales strategy decisions:
- Converting RSA contacts to customers
- Demo scripts and objection handling
- Pricing discussions and pilot offers
- Lead prioritization and pipeline management

Use this agent when questions relate to customer acquisition, not technical implementation.

## Success Metrics

**Week 4:** Authentication + database working
**Week 6:** All lead sources capturing successfully
**Week 9:** AI responses sending automatically
**Week 12:** Full MVP functional
**Week 14:** First paying customer
**Week 16:** 5 customers, no critical bugs
**Week 20:** 8-10 customers, profitable (36-45K NOK MRR)

## The "Why"

This isn't just a startup - it's the vehicle to Nikolai's life vision: farm in Norwegian countryside, family, freedom, financial independence by age 30. Every dealership signed is a step toward that goal.

When things get hard: **Every feature shipped is another brick in the foundation.**
