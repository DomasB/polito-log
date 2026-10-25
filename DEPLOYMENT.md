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
   - **Root Directory**: Set to `/backend`
   - Click "Deploy"

5. After initial deployment, verify configuration:
   - Go to service Settings → General
   - Verify "Root Directory" is set to `/backend`
   - Go to service Settings → Build
   - Verify the builder is "Railpack" (see [Infrastructure as Code](#infrastructure-as-code))
   - Railway will build from the `/backend` directory

#### Backend Environment Variables

Add the following environment variables to the backend service:

**Required:**
```bash
DATABASE_URL=${{Postgres.DATABASE_URL}}
ENVIRONMENT=production
DEBUG=False
PORT=8000
JWT_SECRET_KEY=<long random string, e.g. `openssl rand -hex 32`>
BREVO_API_KEY=<Brevo API key, see backend/BREVO_SETUP.md>
```

With `ENVIRONMENT=production` the backend **refuses to start** if `JWT_SECRET_KEY` is unset (or left at the code default) or `BREVO_API_KEY` is missing. The deploy then fails its health check, and Railway keeps the previous version running.

**To link database:**
- In Railway dashboard, the `${{Postgres.DATABASE_URL}}` variable reference will automatically connect to your PostgreSQL service

### 4. Create Frontend Service

1. Click "New" → "GitHub Repo"
2. Select your `polito-log` repository again
3. Configure the service:
   - **Service Name**: `frontend`
   - **Root Directory**: Set to `/frontend`
   - Click "Deploy"

4. After initial deployment, verify configuration:
   - Go to service Settings → General
   - Verify "Root Directory" is set to `/frontend`
   - Go to service Settings → Build
   - Verify the builder is "Railpack" (see [Infrastructure as Code](#infrastructure-as-code))
   - Railway will build from the `/frontend` directory

#### Frontend Environment Variables

**IMPORTANT:** The frontend needs to know the backend URL at build time.

Add the following environment variable to the frontend service:

```bash
VITE_API_URL=https://<your-backend-service>.railway.app
```

Replace `<your-backend-service>` with your actual backend Railway URL.

**How to find your backend URL:**
1. Go to backend service in Railway
2. Click Settings → Generate Domain (if not already done)
3. Copy the generated URL (e.g., `https://polito-log-backend-production-xxxx.up.railway.app`)
4. Set this as `VITE_API_URL` in frontend service

**Important Notes:**
- Vite bakes environment variables into the build at build time
- If you change `VITE_API_URL`, you must redeploy the frontend for changes to take effect
- Railway automatically passes environment variables as Docker build arguments
- The Dockerfile uses `ARG` and `ENV` to make `VITE_API_URL` available during the build

### 5. Configure Watch Paths and Wait for CI

Railway deploys each service straight from GitHub. GitHub Actions only runs tests (see [How Deploys Work](#how-deploys-work)). Configure both app services in the Railway dashboard:

1. **Watch paths** (service → Settings → Source / Build → Watch Paths), so a service only redeploys when its own code changes:
   - backend: `/backend/**`
   - frontend: `/frontend/**`
2. **Wait for CI** (service → Settings → Source, toggle "Wait for CI"). Railway then holds each new deployment in `WAITING` until the GitHub Actions runs for that commit finish, and skips it if any run fails.
3. Make sure the deploy branch (Settings → Source → Branch) is `main`.

No Railway token is stored in GitHub. See [Security Considerations](#security-considerations).

### 6. Configure Service Domains

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

## How Deploys Work

```
push / merge to main
        │
        ├─► GitHub Actions CI (tests only)
        │     backend-ci.yml   if backend/** changed:  pytest against Postgres 17
        │     frontend-ci.yml  if frontend/** changed: type-check + build + vitest
        │
        └─► Railway GitHub autodeploy (per service, filtered by watch paths)
              deployment status: WAITING  (Wait for CI)
                    │
                    ├─ all CI runs green  → build + deploy → SUCCESS
                    └─ any CI run failed  → SKIPPED, production stays on the previous version
```

- **GitHub Actions never deploys.** The workflows in `.github/workflows/` (`backend-ci.yml`, `frontend-ci.yml`) only run tests, on pushes to `main` and on pull requests.
- **Railway deploys.** Each service watches the repo through Railway's GitHub integration. Wait for CI waits for every GitHub Actions run on the commit. A workflow skipped by its path filter doesn't count, so a docs-only commit deploys nothing and blocks nothing.
- **Pull requests** run the same CI workflows, so a red check on the PR means the merge will not deploy.

### Redeploy or Roll Back

All of this happens in the Railway dashboard. No GitHub workflow is involved.

- **Redeploy the current commit:** service → Deployments → latest deployment → ⋮ → Redeploy.
- **Roll back:** service → Deployments → pick an earlier successful deployment → ⋮ → Rollback. This restores that deployment's image and variables.
- **A commit was SKIPPED because of a flaky CI run:** re-run the job in GitHub Actions to confirm it's green. Then deploy it with Redeploy on the skipped deployment, or push a new commit.

## Database Migrations

Alembic migrations run as a Railway pre-deploy command, declared in `.railway/railway.ts` (`preDeploy: "python -m app.cli migrate"` on the backend). Railway runs it in a separate container with the service's variables, before the new version goes live; if it fails, the deploy stops and the old version keeps serving. The app no longer creates tables on startup. Details, including how the first migration adopts the existing production schema: `backend/MIGRATIONS.md`.

## Infrastructure as Code

`.railway/railway.ts` is the source of truth for services, source repo and root directories, watch patterns, `preDeploy`, health checks, replicas, domains, and the set of variable names. Variable values are never in git (`preserve()`). Railway does not read this file during deploys; it takes effect only when applied:

```bash
npm install --prefix .railway   # once
railway config plan             # show the diff against production
railway config apply            # apply it
```

Always read the plan first. A resource missing from the file is deleted on apply, and variables are managed, so a variable missing from `env` is deleted too. Do not use `--include-variables` when pulling. After a dashboard change, run `railway config pull --force --variables=managed` and review the diff, or the next apply reverts it.

`.github/workflows/railway-config.yml` runs `plan` on pull requests that touch `.railway/**` and `apply` when such a PR merges. It needs a production project token as the `RAILWAY_TOKEN` repository secret.

The old `railway.json` files were never read by these services and are removed (Config as Code is deprecated).

**Dashboard-only settings** (the DSL cannot express them):
- Restart policy: left at Railway's default.
- Builder: set to the default, Railpack, for both services, so `frontend/Dockerfile`, `nginx.conf` and `docker-entrypoint.sh` are not used in production. Check `railway config plan` after any dashboard change.

## Environment-Specific Configuration

### Production vs Staging

To set up separate staging and production environments:

1. Add a `staging` environment to the Railway project (or create a separate project)
2. Point each staging service at the branch it should deploy from (Settings → Source → Branch)
3. Set the environment's variables, with its own secrets

### Branch Strategy

Recommended branch strategy:
- `main` branch → staging environment
- `production` branch → production environment

If you deploy from a branch other than `main`, add it to the `push` branches of the CI workflows. Otherwise Wait for CI has no runs to wait for.

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

1. **"Service Unavailable" or Health Check Failures**
   - Cause: Port mismatch - application not listening on Railway's assigned PORT
   - Solution: Ensure application uses `${PORT}` environment variable
   - **Backend**: Dockerfile CMD uses `${PORT:-8000}`
   - **Frontend**: Use entrypoint script with `envsubst` to replace PORT in nginx config
   - Railway assigns random ports via `$PORT` environment variable
   - The application MUST listen on the port specified by `$PORT`
   - Check deployment logs to see what port Railway expects vs. what your app uses

2. **"Could not find Dockerfile" Error**
   - Cause: Root directory not set correctly in Railway dashboard
   - Solution: Set Root Directory to `/backend` for backend, `/frontend` for frontend

3. **Deployment Stuck in WAITING or Marked SKIPPED**
   - WAITING: Railway is waiting for GitHub Actions runs on that commit. Check the Actions tab.
   - SKIPPED: a CI run failed. Fix it and push again. If the failure was flaky, see [Redeploy or Roll Back](#redeploy-or-roll-back).

4. **Monorepo Detection Issues**
   - Cause: Railway not recognizing monorepo structure
   - Solution: Set Root Directory correctly for each service
   - Backend: Root Directory = `/backend`
   - Frontend: Root Directory = `/frontend`

5. **Dockerfile COPY Errors in Monorepo** (e.g., "/backend/app: not found")
   - Cause: Dockerfile paths don't match Root Directory setting
   - Solution: When Root Directory is `/backend`, use relative paths in Dockerfile
   - Correct: `COPY app ./app` (from backend/ directory)
   - Incorrect: `COPY backend/app ./app` (looking for backend/backend/app)

6. **Frontend Still Using Localhost After Setting VITE_API_URL**
   - Cause: Environment variable not passed to Docker build stage
   - Solution: Dockerfile must declare `ARG VITE_API_URL` before build
   - Verify: Check Railway build logs for "VITE_API_URL" being set
   - Always redeploy after changing environment variables

7. **Build Failures**
   - Check Railway build logs for errors
   - Verify the root directory and builder in `.railway/railway.ts`
   - Ensure all dependencies are in requirements.txt/package.json

8. **Database Connection Errors**
   - Verify `DATABASE_URL` is correctly linked to Postgres service
   - Check database service is running
   - Verify network connectivity between services

9. **Frontend Can't Connect to Backend**
   - Verify `VITE_API_URL` is set correctly
   - Check CORS configuration in backend
   - Ensure backend domain is accessible

10. **Backend Crashes on Start in Production**
   - Check the deploy logs for `Production requires these secrets to be set: ...`
   - Set the named variables (`JWT_SECRET_KEY`, `BREVO_API_KEY`) on the backend service

### Health Checks

- **Backend**: `https://<backend-url>/` - Should return API info
- **Frontend**: `https://<frontend-url>/health` - Should return "healthy"
- **API Docs**: `https://<backend-url>/api/v1/docs` - Swagger UI

## Important: Railway PORT Configuration

Railway dynamically assigns ports to services. Your application MUST:

1. **Listen on Railway's PORT variable:**
   - Railway injects a `$PORT` environment variable
   - Your app must bind to this port, not a hardcoded port
   - Backend uses: `uvicorn --port ${PORT:-8000}`
   - The `:-8000` provides a fallback for local development

2. **Why This Matters:**
   - Railway's health checks probe the assigned PORT
   - If your app listens on a different port, health checks fail
   - This causes "Service Unavailable" errors during deployment

3. **Dockerfile Configuration:**
   - Use shell form CMD to interpolate environment variables
   - Example: `CMD uvicorn app:app --port ${PORT:-8000}`
   - NOT: `CMD ["uvicorn", "app:app", "--port", "8000"]` (array form can't interpolate)

4. **Nginx/Frontend PORT Configuration:**
   - Nginx cannot directly use environment variables in config
   - Solution: Use entrypoint script with `envsubst` to replace `${PORT}` placeholder
   - The frontend uses `/docker-entrypoint.sh` to substitute PORT at runtime
   - nginx.conf template has `listen ${PORT};` which gets replaced with actual port

## Security Considerations

1. **Environment Variables**: Never commit secrets to git. Production secrets (`JWT_SECRET_KEY`, `BREVO_API_KEY`) live only in Railway variables.
2. **Database**: PostgreSQL is private by default, only accessible within Railway network
3. **HTTPS**: Railway automatically provides SSL certificates
4. **CORS**: Configure allowed origins in backend
5. **Secrets Rotation**: Regularly rotate API tokens and secrets
6. **No Railway Token in GitHub**: Deploys come from Railway's GitHub integration, so GitHub never needs a `RAILWAY_TOKEN`. An earlier setup also deployed with `railway up` from GitHub Actions, using a token stored as a repo secret. That gave every workflow (and anyone who could change one) a credential to the whole Railway project, and it was dropped after the October 2026 incident. Don't add a Railway token to GitHub again.

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

1. Test the deployment by merging a change to `main`, then watch CI go green and Railway go WAITING → SUCCESS
2. Verify both services are running correctly
3. Check application functionality end-to-end
4. Set up monitoring and alerts
5. Configure custom domains (if needed)
6. Add health check monitoring
7. Set up staging environment

## Support

- Railway Documentation: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
- GitHub Actions Documentation: https://docs.github.com/en/actions

## Checklist

Use this checklist to ensure everything is configured:

- [ ] Railway project created
- [ ] PostgreSQL database provisioned
- [ ] Backend service created and configured
- [ ] Backend Root Directory set to `/backend`
- [ ] Frontend service created and configured
- [ ] Frontend Root Directory set to `/frontend`
- [ ] Backend environment variables set (DATABASE_URL, ENVIRONMENT, DEBUG, PORT, JWT_SECRET_KEY, BREVO_API_KEY)
- [ ] Frontend environment variable set (VITE_API_URL)
- [ ] Database linked to backend service
- [ ] Watch paths set (`/backend/**`, `/frontend/**`)
- [ ] Wait for CI enabled on backend and frontend
- [ ] No `RAILWAY_TOKEN` secret in the GitHub repo
- [ ] Backend domain generated
- [ ] Frontend domain generated
- [ ] Frontend VITE_API_URL updated with backend URL
- [ ] Test deployment triggered
- [ ] Application accessible and functional
- [ ] API documentation accessible
- [ ] Health checks passing

## Local Development Setup

For local development, create a `.env` file in the frontend directory:

```bash
# frontend/.env
VITE_API_URL=http://localhost:8000
```

This file is gitignored. The `.env.example` file serves as a template.

**How it works:**
- Local dev: Uses `VITE_API_URL` from `.env` file or defaults to `http://localhost:8000`
- Production: Uses `VITE_API_URL` environment variable set in Railway dashboard
- The API client configuration happens in `frontend/src/main.ts`

## Additional Configuration Files

The following files are used for CI and Railway deployment:

- `.github/workflows/backend-ci.yml` - Backend tests (gate for Railway's Wait for CI)
- `.github/workflows/frontend-ci.yml` - Frontend type-check, build and tests (gate for Railway's Wait for CI)
- `.railway/railway.ts` - Railway Infrastructure as Code (see above)
- `.github/workflows/railway-config.yml` - Plans and applies `.railway/railway.ts`
- `frontend/Dockerfile` - Frontend containerization (local Docker only; production uses Railpack)
- `frontend/nginx.conf` - Nginx configuration for serving static files
- `frontend/docker-entrypoint.sh` - Script to configure nginx with Railway PORT
- `frontend/.env.example` - Template for environment variables
- `frontend/.env.production` - Production environment defaults
