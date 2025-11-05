# Railway Deployment Guide

## Prerequisites

- Railway account (https://railway.app/)
- GitHub repository with code
- Clerk account with API keys
- Supabase database (already set up)

## Deployment Steps

### 1. Create Railway Project

1. Go to https://railway.app/
2. Click "New Project"
3. Choose "Deploy from GitHub repo"
4. Select `autolead-platform` repository

### 2. Configure Environment Variables

Add these environment variables in Railway dashboard:

```
DATABASE_URL=<your-supabase-connection-string>
CLERK_SECRET_KEY=<your-clerk-secret-key>
CLERK_PUBLISHABLE_KEY=<your-clerk-publishable-key>
APP_NAME=Norvalt API
APP_VERSION=1.0.0
DEBUG=False
```

### 3. Configure Build Settings

- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- **Root Directory**: `/backend`

### 4. Deploy

Railway will automatically deploy on git push to main branch.

### 5. Verify Deployment

1. Check Railway logs for successful startup
2. Visit `https://<your-app>.railway.app/health`
3. Check Swagger docs at `https://<your-app>.railway.app/docs`

## Environment Configuration

### Production Settings

Make sure to:
- Set `DEBUG=False` in production
- Use production Clerk keys (sk_live_, pk_live_)
- Configure CORS for your frontend domain
- Set up monitoring and alerts

### Database Migrations

Run migrations after deployment:

```bash
# Railway CLI
railway run alembic upgrade head
```

## Monitoring

### Check Application Health

```bash
curl https://<your-app>.railway.app/health
```

### View Logs

```bash
railway logs
```

## Troubleshooting

### Common Issues

1. **Database Connection Fails**
   - Verify DATABASE_URL is correct
   - Check Supabase allows Railway's IP

2. **Import Errors**
   - Ensure all dependencies in requirements.txt
   - Check Python version compatibility

3. **Auth Errors**
   - Verify Clerk keys are correct
   - Check JWKS URL is accessible

## Alternative: Render Deployment

If using Render instead of Railway:

1. Create new Web Service
2. Connect GitHub repository
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add same environment variables
6. Deploy

## Next Steps After Deployment

1. Test all endpoints with Postman/curl
2. Integrate with frontend (update API URLs)
3. Set up monitoring (Sentry, etc.)
4. Configure custom domain
5. Set up CI/CD pipeline

