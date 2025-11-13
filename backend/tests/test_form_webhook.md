# Form Webhook Testing Guide

This guide provides examples for testing the website form webhook endpoint.

## Endpoint

```
POST /webhooks/form/{dealership_id}
```

This is a **public endpoint** (no authentication required) that accepts form submissions from dealership websites.

## Test Data

Before testing, you'll need:
- A valid dealership UUID (obtain from database or create via API)
- Example dealership_id: `123e4567-e89b-12d3-a456-426614174000`

## curl Examples

### 1. Basic Valid Request

```bash
curl -X POST http://localhost:8000/webhooks/form/fef413f2-f763-4034-aadb-7474138fafea \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Ola Nordmann",
    "email": "ola@example.com",
    "phone": "+47 123 45 678",
    "vehicle_interest": "Tesla Model 3",
    "message": "I am interested in a test drive this weekend",
    "source_url": "https://dealership.no/contact"
  }'
```

**Expected Response (200 OK):**
```json
{
  "lead_id": "uuid-of-created-lead",
  "status": "created"
}
```

### 2. Minimal Request (without optional fields)

```bash
curl -X POST http://localhost:8000/webhooks/form/fef413f2-f763-4034-aadb-7474138fafea \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Kari Hansen",
    "email": "kari@example.com",
    "message": "I want more information about electric cars"
  }'
```

**Expected Response (200 OK):**
```json
{
  "lead_id": "uuid-of-created-lead",
  "status": "created"
}
```

### 3. Duplicate Submission (within 5 minutes)

Submit the same email twice within 5 minutes:

```bash
# First submission
curl -X POST http://localhost:8000/webhooks/form/fef413f2-f763-4034-aadb-7474138fafea \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "email": "test@example.com",
    "message": "First submission"
  }'

# Second submission (within 5 minutes)
curl -X POST http://localhost:8000/webhooks/form/fef413f2-f763-4034-aadb-7474138fafea \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "email": "test@example.com",
    "message": "Updated submission"
  }'
```

**Expected Response (200 OK):**
```json
{
  "lead_id": "same-uuid-as-first",
  "status": "updated"
}
```

### 4. Invalid Email Format

```bash
curl -X POST http://localhost:8000/webhooks/form/fef413f2-f763-4034-aadb-7474138fafea \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Invalid Email",
    "email": "not-an-email",
    "message": "This should fail"
  }'
```

**Expected Response (422 Unprocessable Entity):**
```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "input": "not-an-email"
    }
  ]
}
```

### 5. Missing Required Fields

```bash
curl -X POST http://localhost:8000/webhooks/form/fef413f2-f763-4034-aadb-7474138fafea \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Missing Email"
  }'
```

**Expected Response (422 Unprocessable Entity):**
```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "email"],
      "msg": "Field required"
    },
    {
      "type": "missing",
      "loc": ["body", "message"],
      "msg": "Field required"
    }
  ]
}
```

### 6. Invalid Dealership ID

```bash
curl -X POST http://localhost:8000/webhooks/form/00000000-0000-0000-0000-000000000000 \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "email": "test@example.com",
    "message": "This dealership does not exist"
  }'
```

**Expected Response (404 Not Found):**
```json
{
  "detail": "Dealership not found: 00000000-0000-0000-0000-000000000000"
}
```

### 7. Malformed JSON

```bash
curl -X POST http://localhost:8000/webhooks/form/fef413f2-f763-4034-aadb-7474138fafea \
  -H "Content-Type: application/json" \
  -d '{invalid json'
```

**Expected Response (422 Unprocessable Entity):**
```json
{
  "detail": [
    {
      "type": "json_invalid",
      "loc": ["body"],
      "msg": "Invalid JSON"
    }
  ]
}
```

## Postman Collection

To import these tests into Postman:

1. Create a new Collection named "Norvalt - Form Webhook Tests"
2. Add environment variable: `DEALERSHIP_ID` = your test dealership UUID
3. Add environment variable: `BASE_URL` = `http://localhost:8000`
4. Create requests for each test case above using `{{BASE_URL}}/webhooks/form/{{DEALERSHIP_ID}}`

## Verification Steps

After making a successful request:

1. Check database for new lead:
   ```sql
   SELECT * FROM leads
   WHERE customer_email = 'ola@example.com'
   AND dealership_id = '123e4567-e89b-12d3-a456-426614174000'
   ORDER BY created_at DESC
   LIMIT 1;
   ```

2. Verify lead fields:
   - `source` should be "website"
   - `status` should be "new"
   - `lead_score` should be 50
   - `customer_name`, `customer_email`, `customer_phone`, etc. should match request

3. Check logs:
   ```bash
   # Backend logs should show:
   # INFO: Form webhook received for dealership {id} from {email}
   # INFO: Created lead {lead_id} for dealership {id} from website form (customer: {email})
   ```

## Edge Cases Tested

✅ Valid submission creates lead
✅ Duplicate within 5 min updates existing lead
✅ Invalid email format rejected
✅ Missing required fields rejected
✅ Invalid dealership ID returns 404
✅ Malformed JSON rejected
✅ Optional fields can be omitted
✅ Whitespace in fields is trimmed
✅ Empty strings in optional fields converted to None

## Next Steps

- [ ] Test with real dealership websites
- [ ] Monitor webhook response times (should be < 500ms)
- [ ] Set up webhook logging/monitoring (Week 7)
- [ ] Implement AI response job queuing (Week 7)
