# Clerk User Sync Guide

## Problem
You can log in with Clerk, but the backend shows "User not found" because your Clerk account isn't in the database yet.

## Solution
Run the sync script to create your user and dealership records.

---

## Step 1: Get Your Clerk IDs

1. **Open your dashboard** in the browser (http://localhost:3000/dashboard)
2. **Open browser console** (Press F12 or Cmd+Option+I on Mac)
3. **Run this JavaScript code** in the console:

```javascript
const token = await window.Clerk.session.getToken();
const parts = token.split('.');
const payload = JSON.parse(atob(parts[1]));
console.log('User ID:', payload.sub);
console.log('Org ID:', payload.org_id);
console.log('Email:', payload.email);
```

4. **Copy the output** - you'll need these values!

Example output:
```
User ID: user_2abc123xyz
Org ID: org_2def456uvw
Email: your.email@example.com
```

---

## Step 2: Run the Sync Script

1. **Open a terminal** in the backend directory
2. **Activate the virtual environment:**
```bash
cd backend
source venv/bin/activate
```

3. **Run the script:**
```bash
python scripts/sync_clerk_user.py
```

4. **Follow the prompts:**
   - Paste your Clerk User ID
   - Paste your Clerk Org ID
   - Enter your email
   - Enter your name
   - Choose a dealership name (e.g., "Tesla Oslo")
   - Confirm with "yes"

---

## Step 3: Test

1. **Refresh your dashboard** (http://localhost:3000/dashboard)
2. **The error should be gone!** 🎉
3. You should see "No leads found" (empty state)

---

## Next Steps

### Add Test Data

Now that your user exists, you can add test leads:

```bash
python scripts/seed_test_data.py
```

This will add:
- 10 sample leads to YOUR dealership
- Sample conversations
- Test vehicle data

### Or Create Leads Manually

Visit http://localhost:8000/docs and use the API to create leads manually.

---

## Troubleshooting

### "User ID should start with 'user_'"
Make sure you copied the full User ID from the console, including the `user_` prefix.

### "Org ID should start with 'org_'"
Make sure you copied the full Org ID from the console, including the `org_` prefix.

### "Dealership already exists"
That's fine! The script will use the existing dealership.

### Still seeing "User not found"
1. Make sure the script completed successfully
2. Check the backend logs for errors
3. Try restarting the backend server

---

## What the Script Does

1. Creates a `dealerships` record with your Clerk org ID
2. Creates a `users` record with your Clerk user ID
3. Links them together with `dealership_id`
4. Sets you as an admin user

After this, the backend can find your user when you authenticate! ✅

