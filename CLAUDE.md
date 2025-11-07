# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Autolead Platform** (Norvalt): AI-powered lead management SaaS for Norwegian car dealerships. Multi-tenant architecture with automatic user provisioning via Clerk webhooks.

## Development Commands

### Backend (FastAPI + PostgreSQL)

```bash
# Start backend server
cd backend
source venv/bin/activate  # macOS/Linux
uvicorn main:app --reload --port 8000

# Run database migrations
cd backend
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "description"

# Run tests
cd backend
pytest

# Run specific test file
pytest tests/test_api_leads.py -v

# Seed test data
python backend/scripts/seed_test_data.py
```

### Frontend (Next.js 16 + React 19)

```bash
# Start frontend dev server
cd frontend
npm run dev

# Build for production
npm run build

# Run linter
npm run lint
```

### Database

The project uses PostgreSQL (hosted on Supabase) with Row-Level Security (RLS) for multi-tenant isolation.

## Architecture

### Backend Architecture (FastAPI)

**Technology Stack:**
- FastAPI 0.121.0 with Uvicorn 0.38.0
- SQLAlchemy 2.0.44 ORM with Alembic migrations
- PostgreSQL via Supabase
- Clerk authentication (JWT RS256 + webhooks)
- Svix for webhook signature verification

**Key Files:**
- `backend/main.py` - Application entry point with CORS, exception handlers, startup/shutdown events
- `backend/app/core/config.py` - Pydantic Settings for environment variables
- `backend/app/core/database.py` - SQLAlchemy engine, session management, connection pooling
- `backend/app/core/auth.py` - JWT verification with cached JWKS endpoint
- `backend/app/core/rls.py` - Row-Level Security context helpers for multi-tenant isolation
- `backend/app/api/deps.py` - FastAPI dependencies (`get_current_user`, `get_current_dealership`)

**Database Models** (`backend/app/models/`):
- `Dealership` - Organizations (maps to Clerk orgs via `clerk_org_id`)
- `User` - Sales reps/managers/admins (maps to Clerk users via `clerk_user_id`)
- `Lead` - Customer inquiries with status (new, contacted, qualified, won, lost)
- `Conversation` - Message history between dealership and customers

**API Structure:**
```
/api/v1/
├── /leads (GET, POST, PATCH, DELETE)
│   └── /{lead_id}/conversations (GET)
└── /conversations (POST)

/webhooks/clerk (POST) - Clerk webhook endpoint
```

**Multi-Tenant Isolation:**
Each request sets `dealership_id` in PostgreSQL session via `set_dealership_context(db, dealership_id)`. All queries are automatically filtered by RLS policies based on `app.current_dealership_id` session variable.

**Authentication Flow:**
1. Frontend gets JWT from Clerk via `auth().getToken()`
2. Backend receives request with `Authorization: Bearer <token>`
3. JWT verified against Clerk JWKS endpoint (cached with `@lru_cache`)
4. User extracted from JWT and dealership context set
5. All queries automatically scoped to user's dealership

**Webhook Provisioning:**
- Clerk sends `organization.created` and `organizationMembership.created` events
- Backend verifies Svix signature and creates `Dealership` and `User` records automatically
- First user in dealership becomes admin
- Idempotent handlers prevent duplicate records

### Frontend Architecture (Next.js)

**Technology Stack:**
- Next.js 16.0.1 (App Router)
- React 19.2.0
- TypeScript 5
- Tailwind CSS 4
- Clerk authentication (`@clerk/nextjs` v6.34.1)
- Shadcn/Radix UI components
- Lucide React icons

**Key Files:**
- `frontend/middleware.ts` - Clerk middleware for route protection
- `frontend/app/layout.tsx` - Root layout with ClerkProvider
- `frontend/lib/api.ts` - API client with authenticated fetch wrapper
- `frontend/types/index.ts` - TypeScript types matching backend schemas

**Page Structure:**
```
/app/
├── (auth)/
│   ├── sign-in/[[...sign-in]]/page.tsx
│   └── sign-up/[[...sign-up]]/page.tsx
└── dashboard/
    ├── layout.tsx (navigation + org switcher)
    ├── leads/
    │   ├── page.tsx (server-side data fetching with filters)
    │   └── [id]/page.tsx (lead detail with conversation history)
```

**API Integration Pattern:**
Server-side data fetching in async React Server Components:
```typescript
// In page.tsx
const token = await getAuthToken();
const leads = await fetchLeads(token, filters);
```

All API calls use `apiRequest<T>()` wrapper from `lib/api.ts` which:
- Automatically injects Bearer token from Clerk
- Handles errors with fallback messages
- Uses `NEXT_PUBLIC_API_URL` (default: http://localhost:8000)

**State Management:**
- No Redux/Context - relies on Next.js App Router server components
- URL-based filter state (searchParams)
- Suspense boundaries for loading states

### Type Synchronization

Backend Pydantic schemas and frontend TypeScript types are **manually synchronized** (no auto-generation). When changing schemas:

1. Update backend Pydantic models in `backend/app/schemas/`
2. Update frontend types in `frontend/types/index.ts`
3. Ensure enums match exactly (LeadStatus, LeadSource, etc.)

## Important Patterns

### Adding a New API Endpoint

1. **Create Pydantic schemas** in `backend/app/schemas/`:
   ```python
   class ThingCreate(BaseModel):
       field: str

   class ThingResponse(BaseModel):
       id: UUID
       field: str
       created_at: datetime

       model_config = ConfigDict(from_attributes=True)
   ```

2. **Create endpoint** in `backend/app/api/v1/endpoints/`:
   ```python
   from app.api.deps import get_current_user, get_db
   from app.core.rls import set_dealership_context

   @router.get("/things")
   async def list_things(
       db: Session = Depends(get_db),
       user: User = Depends(get_current_user)
   ):
       set_dealership_context(db, user.dealership_id)
       things = db.query(Thing).all()
       return things
   ```

3. **Register router** in `backend/app/api/v1/router.py`:
   ```python
   from app.api.v1.endpoints import things
   api_router.include_router(things.router, prefix="/things", tags=["things"])
   ```

4. **Add frontend API function** in `frontend/lib/api.ts`:
   ```typescript
   export async function fetchThings(token: string): Promise<Thing[]> {
     return apiRequest<Thing[]>('/api/v1/things', { token });
   }
   ```

5. **Update frontend types** in `frontend/types/index.ts` to match Pydantic schema

### Database Migrations

**ALWAYS use Alembic for schema changes:**

```bash
# Generate migration from model changes
cd backend
alembic revision --autogenerate -m "add field to leads table"

# Review generated migration in alembic/versions/
# Edit if needed to add indexes, constraints, or RLS policies

# Apply migration
alembic upgrade head

# Rollback if needed
alembic downgrade -1
```

**Adding RLS policies** (for multi-tenant tables):
```sql
-- In migration file
op.execute("""
    ALTER TABLE my_table ENABLE ROW LEVEL SECURITY;

    CREATE POLICY dealership_isolation ON my_table
    FOR ALL
    USING (dealership_id = current_setting('app.current_dealership_id')::uuid);
""")
```

### Multi-Tenant Context

**Backend:** Always set dealership context in authenticated endpoints:
```python
from app.core.rls import set_dealership_context

@router.get("/leads")
def list_leads(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    set_dealership_context(db, user.dealership_id)  # CRITICAL!
    leads = db.query(Lead).all()  # Automatically filtered
    return leads
```

**Frontend:** Clerk organizations map 1:1 to Dealerships. Use OrganizationSwitcher component for multi-org users.

## Environment Variables

### Backend `.env`
```env
DATABASE_URL=postgresql://user:pass@host:5432/db
CLERK_SECRET_KEY=sk_test_xxx
CLERK_PUBLISHABLE_KEY=pk_test_xxx
CLERK_JWKS_URL=https://your-instance.clerk.accounts.dev/.well-known/jwks.json
CLERK_WEBHOOK_SECRET=whsec_xxx
DEBUG=True
```

### Frontend `.env.local`
```env
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_xxx
CLERK_SECRET_KEY=sk_test_xxx
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Testing

### Backend Tests

Tests use pytest with fixtures in `tests/conftest.py`:
- Mock Clerk JWT verification (no real tokens needed)
- In-memory SQLite or PostgreSQL test database
- Sample data fixtures (dealership, user, lead)

**Run tests:**
```bash
cd backend
pytest -v
pytest tests/test_api_leads.py::test_create_lead -v
```

**Important:** Some tests require PostgreSQL (SQLite doesn't support JSONB). Set `TEST_DATABASE_URL` in `.env` for full test coverage.

### Frontend Testing

Currently manual testing. Future: Add Jest + React Testing Library.

## Common Issues

### "User not found" after Clerk signup

**Cause:** Webhook not configured or failing.

**Fix:**
1. Verify `CLERK_WEBHOOK_SECRET` is set in backend `.env`
2. Check webhook endpoint is reachable (use Cloudflare Tunnel for local dev)
3. In Clerk Dashboard → Webhooks, verify events are being sent
4. Check backend logs for webhook errors
5. Manual fallback: Run `python backend/scripts/sync_clerk_user.py`

### CORS errors in frontend

**Cause:** Backend CORS middleware doesn't allow frontend origin.

**Fix:** Add origin to `main.py` CORS middleware:
```python
allow_origins=[
    "http://localhost:3000",
    "http://localhost:3001",
    "https://your-domain.vercel.app",
],
```

### Database connection pool exhausted

**Cause:** Connections not being returned to pool.

**Fix:** Always use `Depends(get_db)` for database sessions in FastAPI endpoints. Never create sessions manually with `SessionLocal()`.

### RLS policies blocking queries

**Cause:** `set_dealership_context()` not called before query.

**Fix:** Add `set_dealership_context(db, user.dealership_id)` at start of endpoint handler.

## Code Style

### Backend
- Use SQLAlchemy 2.0 style (no legacy query API)
- Pydantic v2 with `model_config = ConfigDict(from_attributes=True)`
- Type hints on all functions
- Docstrings on all public functions
- Use custom exceptions (NotFoundException, UnauthorizedException, ForbiddenException) not generic HTTP exceptions

### Frontend
- Async Server Components for data fetching (not useEffect)
- Client Components only when needed (forms, interactivity)
- Prefer `searchParams` over client-side state for filters
- Use Shadcn components (Button, Card, Dialog, etc.) for UI
- Tailwind CSS for styling (no CSS modules)

## Deployment

### Backend Deployment (Railway/Render)

1. Set all environment variables in platform dashboard
2. Set build command: `pip install -r requirements.txt`
3. Set start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Run migrations: `alembic upgrade head` (or add to start script)
5. Configure Clerk webhook URL to production domain

### Frontend Deployment (Vercel)

1. Connect GitHub repository
2. Set environment variables (Clerk keys, API URL)
3. Set framework preset: Next.js
4. Deploy

## Project Status

See `IMPLEMENTATION_STATUS.md` for detailed completion status. Current phase: Week 4 complete (backend API + frontend dashboard with Clerk authentication).
