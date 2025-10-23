# Quick Start: Testing Authentication

## Prerequisites

Make sure your backend is set up and running. The database tables will be created automatically when the server starts.

## Step 1: Start the Backend

```bash
cd backend
./dev.sh
```

Or if running locally:
```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The new tables (`users` and `magic_links`) will be created automatically.

## Step 2: Test Magic Link Request

```bash
curl -X POST http://localhost:8000/api/v1/auth/magic-link \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'
```

**Expected Response:**
```json
{
  "message": "Magic link sent successfully",
  "email": "test@example.com"
}
```

**Console Output:**
You'll see something like this in your backend console:

```
================================================================================
MAGIC LINK EMAIL (Development Mode)
================================================================================
To: test@example.com

Magic Link: http://localhost:5173/auth/verify?token=abc123def456...

Click the link above to log in.
================================================================================
```

## Step 3: Copy the Token

From the console output, copy the token from the URL. For example, if the URL is:
```
http://localhost:5173/auth/verify?token=Kx7dJ9pQr2vB5sYt8wZm4nC6hF1gL3a
```

The token is: `Kx7dJ9pQr2vB5sYt8wZm4nC6hF1gL3a`

## Step 4: Verify the Magic Link

```bash
curl -X POST http://localhost:8000/api/v1/auth/verify \
  -H "Content-Type: application/json" \
  -d '{"token": "Kx7dJ9pQr2vB5sYt8wZm4nC6hF1gL3a"}'
```

**Expected Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiZW1haWwiOiJ0ZXN0QGV4YW1wbGUuY29tIiwidXNlcm5hbWUiOiJ0ZXN0IiwiZXhwIjoxNzMwNjI4MDAwLCJpYXQiOjE3MzAwMjMwMDB9.xxx",
  "token_type": "bearer",
  "expires_at": "2025-10-30T12:00:00Z",
  "user": {
    "id": 1,
    "email": "test@example.com",
    "username": "test",
  }
}
```

## Step 5: Use the JWT Token

Copy the `access_token` from the response and use it to access protected endpoints:

```bash
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Expected Response:**
```json
{
  "id": 1,
  "email": "test@example.com",
  "username": "test",
  "is_active": true,
  "created_at": "2025-10-23T10:30:00Z",
  "updated_at": "2025-10-23T10:30:00Z"
}
```

## Step 6: Update User Profile

```bash
curl -X PUT http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{"username": "john_doe"}'
```

## API Documentation

Visit the interactive API documentation:
- **Swagger UI:** http://localhost:8000/api/v1/docs
- **ReDoc:** http://localhost:8000/api/v1/redoc

You can test all endpoints directly from the Swagger UI!

## Authentication Flow Summary

1. **Request Magic Link** → Email sent (printed to console in dev)
2. **User Clicks Link** → Frontend extracts token from URL
3. **Verify Token** → Backend creates/updates user, returns JWT
4. **Store JWT** → Frontend stores token
5. **Make Requests** → Include `Authorization: Bearer <token>` header

## Token Expiration

- **Magic Links:** 15 minutes (configurable via `MAGIC_LINK_EXPIRE_MINUTES`)
- **JWT Tokens:** 7 days (configurable via `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`)

## Using with Frontend

When the frontend is ready:

1. User enters email in login form
2. Call `POST /api/v1/auth/magic-link` with email
3. Show "Check your email" message
4. User clicks link in email (or console in dev)
5. Frontend route `/auth/verify?token=...` extracts token
6. Call `POST /api/v1/auth/verify` with token
7. Store returned JWT in localStorage
8. Add JWT to Authorization header for all API requests
9. Redirect to dashboard/home page

## Environment Configuration

Make sure your `.env` file has these settings:

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/polito_log

# JWT Settings
JWT_SECRET_KEY=your-super-secret-key-change-this-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=10080

# Magic Link Settings
MAGIC_LINK_EXPIRE_MINUTES=15
FRONTEND_URL=http://localhost:5173
```

## Troubleshooting

### Tables not created?
Restart the backend server. Tables are created automatically on startup.

### Token expired?
Magic links expire in 15 minutes. Request a new one.

### JWT expired?
JWT tokens expire in 7 days. Request a new magic link to log in again.

### "Not authenticated" error?
- Check that Authorization header is present
- Verify format: `Authorization: Bearer <token>`
- Make sure token hasn't expired

## Next Steps

- Implement frontend login/auth UI
- Add protected routes using `get_current_user` dependency
- Configure production email sender
- Set up proper JWT secret key for production
