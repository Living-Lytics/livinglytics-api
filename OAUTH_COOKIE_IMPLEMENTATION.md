# Google OAuth Cookie-Based Authentication

## Overview

The Google OAuth flow now uses **secure HttpOnly cookies** instead of query parameters for authentication. This is more secure since cookies can't be accessed by JavaScript.

## Flow

### 1. Start OAuth Flow
**Endpoint:** `GET /v1/auth/google/start?next={url}`

**Parameters:**
- `next` (optional): URL to redirect to after authentication
  - Default: `https://www.livinglytics.com/onboarding`
  - Example: `?next=https://www.livinglytics.com/dashboard`

**What it does:**
1. Accepts the `next` URL parameter
2. Encodes it into the OAuth `state` parameter (base64)
3. Redirects to Google OAuth consent screen

**Example:**
```
GET /v1/auth/google/start?next=https://www.livinglytics.com/dashboard
→ Redirects to Google OAuth with state parameter
```

### 2. OAuth Callback
**Endpoint:** `GET /v1/auth/google/callback?code={code}&state={state}`

**What it does:**
1. Receives OAuth code and state from Google
2. Decodes state to extract the `next` URL
3. Exchanges code for Google access token
4. Fetches user info from Google
5. Creates or updates user in database
6. Creates JWT access token
7. Sets secure cookie with JWT
8. Redirects to `next` URL (302)

**Cookie Attributes:**
```javascript
{
  key: "ll_session",
  value: "{JWT_TOKEN}",
  domain: ".livinglytics.com",  // Works for www and non-www
  path: "/",                     // Available on all paths
  secure: true,                  // HTTPS only
  httponly: true,                // Not accessible via JavaScript
  samesite: "none",              // Cross-site requests allowed
  max_age: 2592000               // 30 days (in seconds)
}
```

## CORS Configuration

The backend CORS is configured to allow cookies:

```python
ALLOW_ORIGINS = [
    "https://livinglytics.com",
    "https://www.livinglytics.com",
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOW_ORIGINS,
    allow_credentials=True,  # Required for cookies
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Logging

On successful authentication, the backend logs:

```
[OAUTH-SUCCESS] User authenticated via Google: user@example.com
[OAUTH-SUCCESS] Cookie set: domain=.livinglytics.com, path=/, secure=True, httponly=True, samesite=none, max_age=2592000
[OAUTH-SUCCESS] Redirecting to: https://www.livinglytics.com/onboarding
```

## Frontend Implementation

### Reading the Cookie

The frontend needs to read the cookie to check authentication status. Since it's HttpOnly, it can't be accessed via JavaScript, so you'll need to:

**Option 1: Send cookie with API requests**
```javascript
// Browser automatically includes cookies in requests to api.livinglytics.com
fetch('https://api.livinglytics.com/v1/auth/status', {
  credentials: 'include'  // Include cookies in request
})
```

**Option 2: Update /v1/auth/status to read from cookie**
The backend can read the `ll_session` cookie in the `/v1/auth/status` endpoint instead of expecting a Bearer token.

### Initiating OAuth

```javascript
// Redirect user to start OAuth flow
window.location.href = 'https://api.livinglytics.com/v1/auth/google/start?next=https://www.livinglytics.com/dashboard';
```

After authentication, the user is automatically redirected back to the `next` URL with the cookie set.

## Google Cloud Console Configuration

Add this redirect URI to your Google Cloud Console:

```
https://api.livinglytics.com/v1/auth/google/callback
```

**Steps:**
1. Go to: https://console.cloud.google.com/apis/credentials
2. Edit your OAuth 2.0 Client ID
3. Add to "Authorized redirect URIs": `https://api.livinglytics.com/v1/auth/google/callback`
4. Save

The exact URI is printed in the backend startup logs for easy copying.

## Environment Variables

**Backend (api.livinglytics.com):**
```
GOOGLE_CLIENT_ID=<from-google-cloud-console>
GOOGLE_CLIENT_SECRET=<from-google-cloud-console>
GOOGLE_REDIRECT_URI=https://api.livinglytics.com/v1/auth/google/callback
FRONTEND_URL=https://www.livinglytics.com
```

**Frontend (livinglytics.com):**
No environment variables needed for OAuth! The frontend just needs to redirect to the backend OAuth endpoints.

## Security Benefits

✅ **HttpOnly Cookie** - JavaScript can't access the token (prevents XSS attacks)
✅ **Secure Flag** - Cookie only sent over HTTPS
✅ **SameSite=None** - Works across domains (api.livinglytics.com → livinglytics.com)
✅ **Domain=.livinglytics.com** - Cookie works for both www and non-www subdomains
✅ **30-day expiry** - Auto-logout after 30 days

## Migration Notes

If you were previously using localStorage for JWT tokens, you'll need to update your frontend to:

1. Remove localStorage token management
2. Always include `credentials: 'include'` in fetch requests
3. Update auth status checks to rely on cookies instead of localStorage

The backend `/v1/auth/status` endpoint should be updated to read from cookies instead of requiring a Bearer token header.

## Testing

**Local Development:**
- Use `localhost` instead of production domains
- Cookies may not work cross-domain in development
- Consider using query parameter approach for local testing

**Production:**
- Cookie should work automatically between www.livinglytics.com and api.livinglytics.com
- Verify cookie is set in browser DevTools → Application → Cookies
- Check that cookie attributes match the configuration above
