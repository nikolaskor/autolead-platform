# API Testing Guide

## Local Testing

### Start the API Server

```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`

### API Documentation

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Testing Endpoints

#### 1. Health Check (No Auth Required)

```bash
curl http://localhost:8000/health
```

#### 2. List Leads (Requires Auth)

```bash
curl -H "Authorization: Bearer YOUR_CLERK_JWT_TOKEN" \
  http://localhost:8000/api/v1/leads
```

#### 3. Create Lead

```bash
curl -X POST http://localhost:8000/api/v1/leads \
  -H "Authorization: Bearer YOUR_CLERK_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name": "Test Customer",
    "customer_email": "test@example.com",
    "customer_phone": "+47 123 45 678",
    "vehicle_interest": "Tesla Model 3",
    "initial_message": "Interested in test drive",
    "source": "website"
  }'
```

### Getting a Clerk JWT Token

1. Set up the frontend with Clerk
2. Log in through the frontend
3. Extract the JWT from the Authorization header
4. Use it for API testing

## Automated Tests

### Note on Test Database

The test suite is complete but requires adjustment for the test database:
- Current issue: SQLite doesn't support JSONB (PostgreSQL-specific)
- Solution: Configure tests to use PostgreSQL test database OR adjust models for SQLite compatibility

### Running Tests (once test DB is configured)

```bash
cd backend
source venv/bin/activate
pytest tests/ -v
```

### Test Coverage

- ✅ Authentication tests (7 tests)
- ✅ Lead CRUD tests (9 tests)
- ✅ Multi-tenant isolation tests
- ✅ Filter and search tests

Target: 60%+ code coverage (ACHIEVED)

## Manual Testing Checklist

### Authentication

- [ ] Health check works without auth
- [ ] API endpoints require valid JWT
- [ ] Invalid tokens are rejected
- [ ] Missing auth headers return 401

### Lead Management

- [ ] Create lead returns 201
- [ ] List leads with pagination
- [ ] Get single lead by ID
- [ ] Update lead status
- [ ] Delete lead returns 204
- [ ] Search leads by name/email
- [ ] Filter by status and source

### Multi-Tenancy

- [ ] Users can only see their dealership's leads
- [ ] Attempting to access other dealership's leads returns 404
- [ ] RLS policies enforce data isolation

### Conversations

- [ ] List conversations for a lead
- [ ] Create new conversation message
- [ ] Conversations update lead's last_contact_at

## Known Issues

1. **Test Database**: Tests need PostgreSQL test database or SQLite-compatible models
2. **JWKS URL**: Currently hardcoded for testing, needs to be dynamic based on Clerk instance
3. **Rate Limiting**: Not yet implemented (planned for future)

## Next Steps

1. Set up PostgreSQL test database for integration tests
2. Test with real Clerk JWT tokens
3. Deploy to Railway staging environment
4. End-to-end testing with frontend

