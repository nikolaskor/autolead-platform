# Norvalt Backend

FastAPI backend for the Norvalt lead management platform.

## Setup Instructions

### 1. Environment Variables

Create a `.env` file in the `backend/` directory:

```bash
cp .env.example .env
```

Edit `.env` and add the required variables:

```env
DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@[HOST]:5432/postgres
CLERK_SECRET_KEY=sk_test_xxx
CLERK_PUBLISHABLE_KEY=pk_test_xxx
CLERK_JWKS_URL=https://[YOUR-CLERK-INSTANCE].clerk.accounts.dev/.well-known/jwks.json
CLERK_WEBHOOK_SECRET=whsec_xxx
```

**Database URL:**

1. Go to your Supabase project dashboard
2. Click Settings → Database
3. Copy the "Connection string" (URI format)
4. Replace `[YOUR-PASSWORD]` with your actual database password

**Clerk keys:**

- `CLERK_SECRET_KEY` and `CLERK_PUBLISHABLE_KEY` are available under Clerk → API Keys.
- `CLERK_JWKS_URL` is listed on the same page (needed for JWT verification).
- `CLERK_WEBHOOK_SECRET` is generated when you create a webhook endpoint in the Clerk dashboard (see [Clerk Webhook Setup](#clerk-webhook-setup)).

### 2. Install Dependencies

Make sure your virtual environment is activated:

```bash
# If venv not created yet
python -m venv venv

# Activate venv
source venv/bin/activate  # On macOS/Linux
# OR
venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt
```

### 3. Run Database Migrations

Apply the database schema to your Supabase database:

```bash
# From the backend/ directory
alembic upgrade head
```

This will create all tables with proper indexes and Row-Level Security policies.

### 4. Seed Test Data (Optional)

Populate the database with test dealerships, users, and leads:

```bash
# From the project root
python backend/scripts/seed_test_data.py
```

This creates:

- 2 test dealerships (Tesla Oslo, VW Bergen)
- 4 users (2 per dealership)
- 20 leads (10 per dealership)
- Sample conversations

### 5. Run Tests

```bash
# From the backend/ directory
pytest
```

### 6. Start the Development Server

```bash
# From the backend/ directory
uvicorn main:app --reload --port 8000
```

API will be available at: `http://localhost:8000`

API documentation: `http://localhost:8000/docs`

## Clerk Webhook Setup

The backend now provisions dealerships and users automatically when Clerk sends webhook events. Configure a webhook endpoint once your server is reachable.

1. **Expose your backend**
   - **Development:** run `ngrok http 8000` (or your reverse proxy of choice) and copy the HTTPS URL.
   - **Production:** use the deployed backend domain.
2. **Create a webhook endpoint in Clerk**
   - Navigate to Clerk Dashboard → Webhooks → Add endpoint.
   - Use `<YOUR_URL>/webhooks/clerk` as the target URL.
3. **Subscribe to events**
   - `organizationMembership.created` (required) - Creates users and dealerships
   - `organization.created` (optional but keeps metadata up to date)
   - `user.deleted` (recommended) - Removes users from database when deleted in Clerk
   - `organizationMembership.deleted` (recommended) - Removes users when removed from organization
4. **Copy the signing secret**
   - Set it as `CLERK_WEBHOOK_SECRET` in your backend environment.
5. **Redeploy/restart the backend** so the new environment variable takes effect.

> Tip: Keep `scripts/sync_clerk_user.py` as a manual fallback when testing locally without webhooks.

## Project Structure

```
backend/
├── alembic/                 # Database migrations
│   └── versions/
│       ├── 001_initial_schema.py
│       └── 002_rls_policies.py
├── app/
│   ├── api/                # API endpoints (to be added)
│   ├── core/               # Core functionality
│   │   ├── config.py       # Configuration and settings
│   │   ├── database.py     # Database connection
│   │   └── rls.py          # Row-Level Security helpers
│   ├── models/             # SQLAlchemy models
│   │   ├── dealership.py
│   │   ├── user.py
│   │   ├── lead.py
│   │   └── conversation.py
│   └── schemas/            # Pydantic schemas (to be added)
├── scripts/
│   └── seed_test_data.py   # Database seeding script
├── tests/                  # Test files
│   ├── test_database.py
│   └── test_models.py
├── main.py                 # FastAPI application entry point
└── requirements.txt        # Python dependencies
```

## Database Schema

The database includes these core tables:

- **dealerships**: Car dealership organizations (multi-tenant)
- **users**: Sales reps, managers, and admins
- **leads**: Customer inquiries from all sources
- **conversations**: Message history for each lead
- **vehicles**: Inventory (optional, for future use)
- **automation_rules**: Follow-up sequences (optional, for future use)

All tables use UUID primary keys and include proper foreign key relationships.

## Row-Level Security (RLS)

RLS policies are enabled on multi-tenant tables (leads, conversations, vehicles) to ensure data isolation between dealerships.

To set the dealership context in your application:

```python
from app.core.rls import set_dealership_context

# In your API endpoint
set_dealership_context(db, dealership_id)
leads = db.query(Lead).all()  # Automatically filtered by dealership_id
```

## Next Steps

After completing the database setup:

1. **Week 3, Days 4-5**: Implement Core API endpoints

   - Authentication middleware (Clerk integration)
   - Lead CRUD endpoints
   - Webhook endpoints

2. **Week 4**: Frontend integration with Clerk
3. **Week 5-6**: Lead capture from all sources
4. **Week 7-9**: AI auto-response system

See `docs/PRD.md` for the complete roadmap.

## Troubleshooting

### Connection Error

If you get "could not connect to server":

- Verify your DATABASE_URL is correct
- Check that Supabase project is active
- Ensure your IP is allowed in Supabase settings

### Migration Error

If `alembic upgrade head` fails:

- Check DATABASE_URL is set in .env
- Verify database credentials are correct
- Try running migrations with `--sql` flag to see generated SQL

### Import Error

If you get import errors:

- Ensure virtual environment is activated
- Verify all dependencies are installed: `pip install -r requirements.txt`
- Check you're in the correct directory
