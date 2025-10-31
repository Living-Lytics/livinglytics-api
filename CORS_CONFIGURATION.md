# CORS Configuration Guide

## Overview

The Living Lytics API backend has CORS (Cross-Origin Resource Sharing) configured to allow requests from:
- Production domains (`livinglytics.com`, `www.livinglytics.com`)
- Legacy domains (`livinglytics.base44.app`)
- **All Replit dev domains** (`*.replit.dev`)
- Local development (`localhost:5173`)

## Configuration

### Backend (FastAPI)

Located in `main.py`:

```python
ALLOW_ORIGINS = [
    "https://livinglytics.base44.app",
    "https://preview--livinglytics.base44.app",
    "https://livinglytics.com",
    "https://www.livinglytics.com",
    "http://localhost:5173",
]

# CORS middleware with support for Replit domains (*.replit.dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOW_ORIGINS,
    allow_origin_regex=r"https://.*\.replit\.dev",  # Match all Replit dev domains
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Request-ID"],
    expose_headers=["X-Request-ID"],
)
```

### Key Features

**1. Specific Origins**
- Explicitly listed domains are always allowed
- Includes production, staging, and local development

**2. Pattern Matching for Replit**
- `allow_origin_regex=r"https://.*\.replit\.dev"` matches any subdomain
- Examples: 
  - `https://my-app.username.replit.dev`
  - `https://living-lytics-api.myusername.replit.dev`
  - `https://frontend-v2.teamname.replit.dev`

**3. Credentials Support**
- `allow_credentials=True` enables cookie-based authentication
- Required for HttpOnly cookies to work cross-domain
- Frontend must use `credentials: 'include'` in fetch requests

**4. Headers**
- Allows: `Content-Type`, `Authorization`, `X-Request-ID`
- Exposes: `X-Request-ID` (for request tracing)

**5. Methods**
- Supports: GET, POST, PUT, DELETE, OPTIONS
- OPTIONS is required for preflight requests

## Frontend Configuration

### Using Cookies (Recommended)

For cookie-based authentication with the backend:

```javascript
fetch('https://api.livinglytics.com/v1/auth/status', {
  method: 'GET',
  credentials: 'include',  // Send cookies with request
  headers: {
    'Content-Type': 'application/json'
  }
})
```

### Using Bearer Tokens

For JWT token authentication:

```javascript
const token = localStorage.getItem('ll_token');

fetch('https://api.livinglytics.com/v1/auth/status', {
  method: 'GET',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
})
```

## Testing CORS

### Test from Browser Console

On your frontend (e.g., `https://yourapp.username.replit.dev`):

```javascript
// Test with credentials
fetch('https://api.livinglytics.com/v1/auth/status', {
  credentials: 'include'
})
  .then(r => r.json())
  .then(console.log)
  .catch(console.error);

// Should NOT see CORS errors
```

### Common CORS Errors

**❌ "No 'Access-Control-Allow-Origin' header"**
- Your origin is not in the allowed list
- Check that your domain matches the regex pattern
- Verify the backend is running and accessible

**❌ "Credentials flag is 'true', but 'Access-Control-Allow-Credentials' is not"**
- Backend needs `allow_credentials=True`
- Already configured in this project ✓

**❌ "Wildcard '*' cannot be used with credentials"**
- Cannot use `allow_origins=["*"]` when `allow_credentials=True`
- Must specify exact origins or use regex
- Already handled in this project ✓

## Development vs Production

### Development
When developing locally or on Replit:
- Replit domains automatically allowed via regex
- `localhost:5173` explicitly allowed for Vite dev server

### Production
When deployed to `api.livinglytics.com`:
- `livinglytics.com` and `www.livinglytics.com` explicitly allowed
- Replit domains still allowed for testing/staging
- Consider removing Replit regex in production for tighter security

## Security Notes

✅ **Credentials require specific origins** - Can't use wildcards
✅ **Pattern matching for development** - Easy testing on Replit
✅ **HttpOnly cookies** - JavaScript can't access (prevents XSS)
✅ **Secure flag** - Cookies only sent over HTTPS
✅ **Request ID tracking** - X-Request-ID header for debugging

## Troubleshooting

**Frontend still getting CORS errors?**
1. Check the browser console for the exact error message
2. Verify the request origin matches an allowed pattern
3. Ensure `credentials: 'include'` if using cookies
4. Check that the backend is running and accessible
5. Try a preflight request manually to debug OPTIONS

**Need to add a new origin?**
Add to `ALLOW_ORIGINS` list in `main.py`:
```python
ALLOW_ORIGINS = [
    "https://livinglytics.com",
    "https://www.livinglytics.com",
    "https://your-new-domain.com",  # Add here
]
```

**Need to change the regex pattern?**
Update `allow_origin_regex` in `main.py`:
```python
allow_origin_regex=r"https://.*\.replit\.dev|https://.*\.vercel\.app",  # Multiple patterns
```
