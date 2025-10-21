# Deployment Guide - Railway

This guide walks you through deploying the polito-log application to Railway with separate services for frontend, backend, and PostgreSQL database.

## Architecture Overview

The deployment consists of three Railway services:

1. **PostgreSQL Database** - Managed PostgreSQL instance
2. **Backend API** - FastAPI application running in a Docker container
3. **Frontend** - Vue.js application built and served as static files via nginx

## Prerequisites

- Railway account (sign up at https://railway.app)
- GitHub repository with this code
- Railway CLI installed (optional, for local testing)

## Initial Setup Steps

### 1. Create Railway Project

1. Go to https://railway.app/new
2. Select "Empty Project"
3. Name it `polito-log` or your preferred name

### 2. Add PostgreSQL Database

1. Click "New" → "Database" → "Add PostgreSQL"
2. Railway will automatically provision a PostgreSQL instance
3. Note: The database will be automatically configured with connection credentials

### 3. Create Backend Service

1. Click "New" → "GitHub Repo"
2. Select your `polito-log` repository
3. Railway will detect it as a monorepo
4. Configure the service:
   - **Service Name**: `backend`
   - **Root Directory**: Leave empty (uses project root, configured in railway.json)
   - Click "Deploy"

5. After initial deployment, verify configuration:
   - Go to service Settings → Build
   - Verify "Dockerfile Path" shows `backend/Dockerfile`
   - Verify "Watch Paths" shows `backend/**`
   - These are configured automatically from `backend/railway.json`

#### Backend Environment Variables

Add the following environment variables to the backend service:

**Required:**
```bash
DATABASE_URL=${{Postgres.DATABASE_URL}}
ENVIRONMENT=production
DEBUG=False
PORT=8000
```

**Optional (for future features):**
```bash
# Google OAuth (when implemented)
GOOGLE_CLIENT_ID=<your-google-client-id>
GOOGLE_CLIENT_SECRET=<your-google-client-secret>

# CORS origins (comma-separated)
ALLOWED_ORIGINS=https://your-frontend-domain.railway.app

# Secret key for JWT tokens (when implemented)
SECRET_KEY=<generate-a-secure-random-key>
```

**To link database:**
- In Railway dashboard, the `${{Postgres.DATABASE_URL}}` variable reference will automatically connect to your PostgreSQL service

### 4. Create Frontend Service

1. Click "New" → "GitHub Repo"
2. Select your `polito-log` repository again
3. Configure the service:
   - **Service Name**: `frontend`
   - **Root Directory**: Leave empty (uses project root, configured in railway.json)
   - Click "Deploy"

4. After initial deployment, verify configuration:
   - Go to service Settings → Build
   - Verify "Dockerfile Path" shows `frontend/Dockerfile`
   - Verify "Watch Paths" shows `frontend/**`
   - These are configured automatically from `frontend/railway.json`

#### Frontend Environment Variables

Add the following environment variables to the frontend service:

```bash
VITE_API_URL=https://<your-backend-service>.railway.app
```

Replace `<your-backend-service>` with your actual backend Railway URL (you'll get this after backend deploys).

### 5. Configure GitHub Actions Secrets

Go to your GitHub repository settings → Secrets and variables → Actions → New repository secret

Add the following secrets:

#### Required Secrets:

1. **RAILWAY_TOKEN**
   - Get this from Railway dashboard: Settings → Tokens → Create Token
   - Copy the token and add it as a GitHub secret
   - This token allows GitHub Actions to deploy to Railway

2. **VITE_API_URL** (optional)
   - The URL of your backend service
   - Example: `https://polito-log-backend.up.railway.app`
   - If not set, the workflow will use a default value

### 6. Set Up Railway Services for CI/CD

For GitHub Actions to work correctly:

1. **Connect GitHub Repository to Railway:**
   - In Railway dashboard, go to Project Settings
   - Click on "Deployments" tab
   - Ensure your GitHub repository is connected
   - This allows Railway CLI to auto-detect the project from GitHub Actions

2. **Verify Service Names:**
   - Go to each service (backend/frontend)
   - Click on Settings → General
   - Ensure services are named exactly:
     - `backend` for backend service
     - `frontend` for frontend service
   - The GitHub Actions workflows reference these service names

3. **Important - Monorepo Configuration:**
   - Both services should have empty Root Directory in Railway dashboard
   - The `railway.json` files handle the monorepo structure
   - Railway will build from project root and use paths specified in railway.json

### 7. Configure Service Domains

1. **Backend Service:**
   - Go to backend service → Settings → Networking
   - Click "Generate Domain" to get a public URL
   - Copy this URL for frontend configuration

2. **Frontend Service:**
   - Go to frontend service → Settings → Networking
   - Click "Generate Domain" to get a public URL
   - This is your application's public URL

3. **Update Frontend Environment Variable:**
   - Update the `VITE_API_URL` in frontend service with the backend URL
   - Trigger a redeployment

## Deployment Workflows

The project includes two GitHub Actions workflows:

### Automatic Deployments

**Backend Deployment** (`.github/workflows/deploy-backend.yml`):
- Triggers on push to `main` or `production` branches when backend files change
- Can also be triggered manually via workflow_dispatch

**Frontend Deployment** (`.github/workflows/deploy-frontend.yml`):
- Triggers on push to `main` or `production` branches when frontend files change
- Can also be triggered manually via workflow_dispatch

### Manual Deployments

You can manually trigger deployments from GitHub:

1. Go to Actions tab in your GitHub repository
2. Select the workflow (Deploy Backend/Frontend to Railway)
3. Click "Run workflow"
4. Choose the environment (production/staging)
5. Click "Run workflow"

## Database Migrations

When you implement database migrations (Alembic), uncomment the migration step in `.github/workflows/deploy-backend.yml`:

```yaml
- name: Run Database Migrations
  env:
    RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
  run: |
    cd backend
    railway run --service backend alembic upgrade head
```

## Environment-Specific Configuration

### Production vs Staging

To set up separate staging and production environments:

1. Create two Railway projects: `polito-log-production` and `polito-log-staging`
2. Repeat the setup steps for each environment
3. Create environment-specific GitHub secrets:
   - `RAILWAY_TOKEN_PRODUCTION`
   - `RAILWAY_TOKEN_STAGING`
4. Modify workflows to use the appropriate token based on branch/environment

### Branch Strategy

Recommended branch strategy:
- `main` branch → staging environment
- `production` branch → production environment

Update workflow triggers accordingly.

## Monitoring and Logs

### View Logs

1. Go to Railway dashboard
2. Select your service (backend/frontend/postgres)
3. Click on "Deployments" tab
4. Click on latest deployment to view logs

### Monitoring

Railway provides built-in monitoring:
- CPU and Memory usage
- Network traffic
- Request metrics
- Deployment history

Access these from each service's "Metrics" tab.

## Troubleshooting

### Common Issues

1. **"Could not find Dockerfile" Error**
   - Cause: Root directory misconfigured in Railway dashboard
   - Solution: Set Root Directory to empty/blank in service Settings
   - Verify `railway.json` has correct `dockerfilePath` (e.g., `backend/Dockerfile`)

2. **"Could not find root directory: /backend" Error (GitHub Actions)**
   - Cause: GitHub Actions workflow running from subdirectory
   - Solution: Already fixed in workflows - `railway up` runs from project root
   - Verify you're using the updated workflow files

3. **Monorepo Detection Issues**
   - Cause: Railway not recognizing monorepo structure
   - Solution: Ensure `watchPatterns` are set in railway.json files
   - Verify Railway dashboard shows correct Watch Paths in Settings → Build

4. **Build Failures**
   - Check Railway build logs for errors
   - Verify Dockerfile paths are correct in railway.json
   - Ensure all dependencies are in requirements.txt/package.json

5. **Database Connection Errors**
   - Verify `DATABASE_URL` is correctly linked to Postgres service
   - Check database service is running
   - Verify network connectivity between services

6. **Frontend Can't Connect to Backend**
   - Verify `VITE_API_URL` is set correctly
   - Check CORS configuration in backend
   - Ensure backend domain is accessible

7. **GitHub Actions Failing**
   - Verify `RAILWAY_TOKEN` secret is set correctly
   - Check token has not expired
   - Verify service names match in Railway dashboard
   - Ensure GitHub repository is connected in Railway project settings

### Health Checks

- **Backend**: `https://<backend-url>/` - Should return API info
- **Frontend**: `https://<frontend-url>/health` - Should return "healthy"
- **API Docs**: `https://<backend-url>/api/v1/docs` - Swagger UI

## Security Considerations

1. **Environment Variables**: Never commit secrets to git
2. **Database**: PostgreSQL is private by default, only accessible within Railway network
3. **HTTPS**: Railway automatically provides SSL certificates
4. **CORS**: Configure allowed origins in backend
5. **Secrets Rotation**: Regularly rotate API tokens and secrets

## Cost Optimization

Railway pricing considerations:
- Free tier includes $5 credit/month
- Database: Charged based on usage
- Services: Charged based on CPU/Memory usage
- Consider using sleep mode for non-production environments

## Backup and Recovery

### Database Backups

1. Railway provides automatic daily backups for PostgreSQL
2. Access backups from Database service → Backups tab
3. Can restore from any backup point

### Manual Backup

```bash
# Install Railway CLI
curl -fsSL https://railway.app/install.sh | sh

# Login
railway login

# Link to your project
railway link

# Create database dump
railway run --service postgres pg_dump > backup.sql
```

## Next Steps

After completing this setup:

1. Test the deployment by pushing a commit to trigger CI/CD
2. Verify both services are running correctly
3. Check application functionality end-to-end
4. Set up monitoring and alerts
5. Configure custom domains (if needed)
6. Implement database migrations (Alembic)
7. Add health check monitoring
8. Set up staging environment

## Support

- Railway Documentation: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
- GitHub Actions Documentation: https://docs.github.com/en/actions

## Checklist

Use this checklist to ensure everything is configured:

- [ ] Railway project created
- [ ] PostgreSQL database provisioned
- [ ] Backend service created and configured
- [ ] Frontend service created and configured
- [ ] Backend environment variables set (DATABASE_URL, ENVIRONMENT, DEBUG, PORT)
- [ ] Frontend environment variable set (VITE_API_URL)
- [ ] Database linked to backend service
- [ ] Railway token generated
- [ ] GitHub secret RAILWAY_TOKEN added
- [ ] Backend domain generated
- [ ] Frontend domain generated
- [ ] Frontend VITE_API_URL updated with backend URL
- [ ] Test deployment triggered
- [ ] Application accessible and functional
- [ ] API documentation accessible
- [ ] Health checks passing

## Additional Configuration Files

The following files have been created for Railway deployment:

- `.github/workflows/deploy-backend.yml` - Backend CI/CD workflow
- `.github/workflows/deploy-frontend.yml` - Frontend CI/CD workflow
- `backend/railway.json` - Backend Railway configuration
- `frontend/railway.json` - Frontend Railway configuration
- `frontend/Dockerfile` - Frontend containerization
- `frontend/nginx.conf` - Nginx configuration for serving static files
