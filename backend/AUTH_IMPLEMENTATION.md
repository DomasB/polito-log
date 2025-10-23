# Authentication Implementation Guide

This document describes the magic link authentication system implemented in the Polito-Log backend.

## Overview

The authentication system uses **passwordless magic link authentication** with **JWT tokens** for session management. No cookies are used - the frontend receives and stores JWT tokens.

## Architecture

### Components

1. **User Model** (`app/models/user.py`)
   - Stores user information (id, email, username)
   - Tracks user status (is_active)
   - Records last login time

2. **MagicLink Model** (`app/models/magic_link.py`)
   - Stores temporary authentication tokens
   - Links to users or email addresses
   - Tracks expiration and usage status

3. **Security Module** (`app/core/security.py`)
   - JWT token creation and verification
   - Secure magic link token generation
   - Uses cryptographically secure random tokens

4. **Email Sender** (`app/core/email.py`)
   - Abstract interface for email sending
   - ConsoleEmailSender for development (prints to console)
   - Extensible for production email services

5. **Auth Service** (`app/services/auth.py`)
   - Business logic for authentication
   - Magic link generation and verification
   - User creation and profile management

6. **Auth Dependencies** (`app/core/dependencies.py`)
   - FastAPI dependencies for route protection
   - JWT token extraction from Authorization header
   - User authentication and authorization checks

## Authentication Flow

### 1. Request Magic Link

**Endpoint:** `POST /api/v1/auth/magic-link`

**Request:**
```json
{
  "email": "user@example.com"
}
```

**Response:**
```json
{
  "message": "Magic link sent successfully",
  "email": "user@example.com"
}
```

**What happens:**
1. System checks if user with email exists
2. Generates secure random token (32 bytes, URL-safe)
3. Creates MagicLink record with 15-minute expiration
4. Sends email with magic link URL
5. If user doesn't exist, they'll be created upon verification

### 2. Verify Magic Link

**Endpoint:** `POST /api/v1/auth/verify`

**Request:**
```json
{
  "token": "secure-random-token-from-email"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_at": "2025-10-30T12:00:00Z",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "username": "user"
  }
}
```

**What happens:**
1. System validates token (not expired, not used)
2. Gets or creates user for the email
4. Marks magic link as used
5. Creates JWT access token (7 days expiry)
6. Returns token and user info

### 3. Access Protected Routes

**Authorization Header:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Example Protected Endpoint:** `GET /api/v1/auth/me`

The frontend must include the JWT token in the Authorization header for all protected routes.

## JWT Token Structure

The JWT token contains:
```json
{
  "sub": "1",              // User ID
  "email": "user@example.com",
  "username": "user",
  "exp": 1730000000,       // Expiration timestamp
  "iat": 1729000000        // Issued at timestamp
}
```

## Protected Routes

Use the authentication dependencies to protect routes:

```python
from app.core.dependencies import get_current_user

# Require any authenticated user
@router.get("/protected")
def protected_route(current_user: User = Depends(get_current_user)):
    return {"message": f"Hello {current_user.username}"}
```

## API Endpoints

### Public Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/magic-link` | Request magic link |
| POST | `/api/v1/auth/verify` | Verify magic link and get token |

### Protected Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/auth/me` | Get current user profile |
| PUT | `/api/v1/auth/me` | Update current user profile |

## Configuration

Add these environment variables to your `.env` file:

```bash
# JWT Settings
JWT_SECRET_KEY=your-super-secret-key-change-this-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=10080  # 7 days

# Magic Link Settings
MAGIC_LINK_EXPIRE_MINUTES=15
FRONTEND_URL=http://localhost:5173
```

**IMPORTANT:** Change `JWT_SECRET_KEY` to a secure random value in production!

Generate a secure key with:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Security Features

1. **Cryptographically Secure Tokens**
   - Magic links use `secrets.token_urlsafe(32)` (256 bits of entropy)
   - Tokens are URL-safe and unpredictable

2. **Token Expiration**
   - Magic links expire in 15 minutes
   - JWT tokens expire in 7 days (configurable)
   - Used magic links are marked and cannot be reused

3. **No Cookies**
   - JWT tokens sent via Authorization header
   - Frontend manages token storage
   - No CSRF vulnerabilities

4. **User Verification**
   - Email-based identity verification
   - Automatic user creation on first login
   - Active user checks on each request

## Development Mode

In development, magic links are printed to the console instead of being emailed:

```
================================================================================
MAGIC LINK EMAIL (Development Mode)
================================================================================
To: user@example.com
Username: john_doe

Magic Link: http://localhost:5173/auth/verify?token=abc123...

Click the link above to log in.
================================================================================
```

## Production Deployment

For production, replace `ConsoleEmailSender` with a real email service:

1. Create a new email sender class implementing `EmailSender` interface
2. Update `get_email_sender()` dependency in `app/core/dependencies.py`
3. Configure your email service credentials
4. Set `JWT_SECRET_KEY` to a secure random value

Example email sender implementations:
- SMTPEmailSender (traditional SMTP)
- SendGridEmailSender (SendGrid API)
- SESEmailSender (AWS SES)

## Testing

### Test Magic Link Flow

1. Start the backend server
2. Request a magic link:
```bash
curl -X POST http://localhost:8000/api/v1/auth/magic-link \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'
```

3. Copy the token from console output
4. Verify the magic link:
```bash
curl -X POST http://localhost:8000/api/v1/auth/verify \
  -H "Content-Type: application/json" \
  -d '{"token": "your-token-here"}'
```

5. Use the returned JWT token:
```bash
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer your-jwt-token-here"
```

## Database Tables

The system creates two new tables:

### `users` table
- `id` (primary key)
- `email` (unique, indexed)
- `username` (unique, indexed)
- `is_active`
- `created_at`
- `updated_at`

### `magic_links` table
- `id` (primary key)
- `token` (unique, indexed)
- `email` (indexed)
- `user_id` (foreign key, nullable)
- `is_used`
- `expires_at`
- `created_at`
- `used_at`

## Frontend Integration

The frontend should:

1. Collect user email and call `/api/v1/auth/magic-link`
2. Show success message to check email
3. Handle magic link route (e.g., `/auth/verify?token=...`)
4. Call `/api/v1/auth/verify` with token from URL
5. Store JWT token in localStorage or secure storage
6. Include token in Authorization header for all API calls
7. Handle token expiration (redirect to login)
8. Clear token on logout

Example frontend code:
```javascript
// Request magic link
async function requestMagicLink(email) {
  const response = await fetch('/api/v1/auth/magic-link', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email })
  });
  return response.json();
}

// Verify magic link
async function verifyMagicLink(token) {
  const response = await fetch('/api/v1/auth/verify', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ token })
  });
  const data = await response.json();
  localStorage.setItem('access_token', data.access_token);
  return data;
}

// Make authenticated request
async function fetchProtected(url) {
  const token = localStorage.getItem('access_token');
  const response = await fetch(url, {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  return response.json();
}
```

## Troubleshooting

### "Invalid or expired magic link"
- Token has expired (15 minutes)
- Token has already been used
- Token doesn't exist in database

### "Not authenticated"
- No Authorization header provided
- Invalid JWT token format
- Token has expired (7 days)
- User account is inactive

### "Username already taken"
- When updating profile, chosen username exists
- Choose a different username

## Future Enhancements

Potential improvements:
- Rate limiting for magic link requests
- Email verification for sensitive operations
- Two-factor authentication (2FA)
- OAuth integration (Google, GitHub, etc.)
- Refresh tokens for longer sessions
- User roles and permissions
- Account deletion and data export
