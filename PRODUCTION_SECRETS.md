# Production Environment Variables Setup

## Backend Deployment (api.livinglytics.com)

When deploying the backend to production, you need to add the following secrets in the Replit Secrets tool:

### Required Secrets:

#### Database
```
DATABASE_URL=<your-supabase-postgres-url>
```
Example: `postgresql://postgres:[password]@[host].supabase.co:5432/postgres`

#### Authentication
```
FASTAPI_SECRET_KEY=<random-secret-key>
ADMIN_TOKEN=<random-admin-token>
```
Generate these with: `openssl rand -hex 32`

#### Google OAuth
```
GOOGLE_CLIENT_ID=<from-google-cloud-console>
GOOGLE_CLIENT_SECRET=<from-google-cloud-console>
GOOGLE_REDIRECT_URI=https://api.livinglytics.com/v1/auth/google/callback
```

#### Frontend URL
```
FRONTEND_URL=https://livinglytics.com
```

#### Instagram/Meta OAuth
```
META_APP_ID=<from-meta-for-developers>
META_APP_SECRET=<from-meta-for-developers>
META_OAUTH_REDIRECT=https://api.livinglytics.com/v1/connections/instagram/callback
```

#### Email (Resend)
```
RESEND_API_KEY=<from-resend-dashboard>
```

#### Optional - Sentry
```
SENTRY_DSN=<from-sentry-dashboard>
ENV=production
```

---

## Frontend Deployment (livinglytics.com)

**The frontend does NOT need any secrets!**

All configuration is done via environment variables that are baked into the build:

### `.env.production` (already in your project):
```env
VITE_API_BASE=https://api.livinglytics.com
VITE_API_HEALTH=/v1/health/liveness
VITE_API_LOGIN=/v1/auth/login
VITE_API_REGISTER=/v1/auth/register
VITE_API_AUTH_STATUS=/v1/auth/status
VITE_API_GOOGLE_START=/v1/auth/google/start
VITE_API_INSTAGRAM_START=/v1/auth/instagram/start
```

These are automatically used during the build process. **No Replit secrets needed for frontend.**

---

## OAuth Provider Configuration

### Google Cloud Console
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Navigate to APIs & Services → Credentials
3. Edit your OAuth 2.0 Client ID
4. Add to **Authorized redirect URIs**:
   - `https://api.livinglytics.com/v1/auth/google/callback`
5. Save

### Meta for Developers
1. Go to [Meta for Developers](https://developers.facebook.com)
2. Open your app → Products → Facebook Login → Settings
3. Add to **Valid OAuth Redirect URIs**:
   - `https://api.livinglytics.com/v1/connections/instagram/callback`
4. Save Changes

---

## Deployment Checklist

### Backend (api.livinglytics.com):
- [ ] Add all secrets listed above to Replit Secrets
- [ ] Deploy as Autoscale
- [ ] Link custom domain: api.livinglytics.com
- [ ] Add DNS records (A and TXT)
- [ ] Wait for DNS propagation
- [ ] Test: `curl https://api.livinglytics.com/v1/health/liveness`

### Frontend (livinglytics.com):
- [ ] Verify `.env.production` has correct API URL
- [ ] Deploy as Autoscale (or Static if preferred)
- [ ] Link custom domain: livinglytics.com
- [ ] Add DNS records (A and TXT)
- [ ] Wait for DNS propagation
- [ ] Test: Visit `https://livinglytics.com`

### OAuth:
- [ ] Update Google OAuth redirect URI
- [ ] Update Meta OAuth redirect URI
- [ ] Test Google sign-in flow
- [ ] Test Instagram connection flow

---

## Troubleshooting

### White Screen on Frontend
- Check browser console for errors
- Verify API URL in `.env.production` is correct
- Ensure backend is deployed and accessible
- Check CORS errors (backend should allow livinglytics.com)

### CORS Errors
- Verify backend CORS allows `https://livinglytics.com`
- Check that `allow_credentials=True` is set
- Ensure proper headers are exposed

### OAuth Not Working
- Verify redirect URIs match exactly in OAuth provider settings
- Check environment variables (GOOGLE_REDIRECT_URI, META_OAUTH_REDIRECT)
- Ensure FRONTEND_URL points to correct domain

### 401 Unauthorized
- Verify JWT tokens are being sent in Authorization header
- Check that FASTAPI_SECRET_KEY is set correctly
- Ensure tokens haven't expired (30-day expiry)

---

## Quick Copy-Paste for Backend Secrets

```
DATABASE_URL=
FASTAPI_SECRET_KEY=
ADMIN_TOKEN=
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=https://api.livinglytics.com/v1/auth/google/callback
FRONTEND_URL=https://livinglytics.com
META_APP_ID=
META_APP_SECRET=
META_OAUTH_REDIRECT=https://api.livinglytics.com/v1/connections/instagram/callback
RESEND_API_KEY=
```

Fill in the blank values and add them one by one to Replit Secrets.
