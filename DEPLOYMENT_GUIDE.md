# Living Lytics Deployment Guide - Option B: Separate API Subdomain

This guide walks you through deploying Living Lytics with a dual-domain setup:
- **livinglytics.com** → Frontend (Marketing Site + App)
- **api.livinglytics.com** → Backend API

## Prerequisites
- Domain name registered (livinglytics.com)
- Access to domain registrar's DNS settings
- Replit account with deployment access
- Google Cloud Console project
- Meta for Developers app

## Step 1: Deploy Backend API

### 1.1 Publish Backend API Deployment
1. In Replit, click the **"Deploy"** button at the top
2. Select **"Autoscale"** deployment type (recommended for APIs)
3. Configure the deployment:
   - **Name**: Living Lytics API
   - **Build command**: (leave empty, not needed)
   - **Run command**: Already configured in `.replit`
4. Click **"Deploy"**

### 1.2 Add Custom Domain (api.livinglytics.com)
1. Go to **Deployments** → **Settings** tab
2. Click **"Link a domain"**
3. Enter: `api.livinglytics.com`
4. Replit will show DNS records (save these for Step 3)
   - Example: `A` record pointing to Replit's IP
   - Example: `TXT` record for verification

### 1.3 Configure Backend Environment Variables
In Deployment → **Secrets**, add these environment variables:

```
DATABASE_URL=<automatically provided by Replit PostgreSQL>
FASTAPI_SECRET_KEY=<your-secret-key>
ADMIN_TOKEN=<your-admin-token>
FRONTEND_URL=https://livinglytics.com
GOOGLE_CLIENT_ID=<your-google-client-id>
GOOGLE_CLIENT_SECRET=<your-google-client-secret>
GOOGLE_REDIRECT_URI=https://api.livinglytics.com/v1/auth/google/callback
META_APP_ID=<your-meta-app-id>
META_APP_SECRET=<your-meta-app-secret>
META_OAUTH_REDIRECT=https://api.livinglytics.com/v1/connections/instagram/callback
RESEND_API_KEY=<your-resend-api-key>
RESEND_FROM_EMAIL=noreply@livinglytics.com
```

> **Note**: Copy values from your existing Replit Secrets in development

## Step 2: Deploy Frontend

### 2.1 Publish Marketing Site Deployment
1. Click **"Deploy"** → Create a **new deployment**
2. Select **"Autoscale"** deployment type
3. Configure:
   - **Name**: Living Lytics Website
   - **Build command**: `cd living-lytics-marketing && npm run build`
   - **Run command**: Already configured in `.replit`
4. Click **"Deploy"**

### 2.2 Add Custom Domain (livinglytics.com)
1. Go to **Deployments** → **Settings** tab
2. Click **"Link a domain"**
3. Enter: `livinglytics.com`
4. Replit will show DNS records (save these for Step 3)

## Step 3: Configure DNS Records

Log in to your domain registrar (e.g., Namecheap, GoDaddy, Cloudflare) and add:

### For api.livinglytics.com:
```
Type: A
Host: api
Value: <IP from Replit>
TTL: Automatic or 300

Type: TXT
Host: api
Value: <verification code from Replit>
TTL: Automatic or 300
```

### For livinglytics.com:
```
Type: A
Host: @ (or root/blank)
Value: <IP from Replit>
TTL: Automatic or 300

Type: TXT
Host: @ (or root/blank)
Value: <verification code from Replit>
TTL: Automatic or 300
```

⏰ **Wait for DNS Propagation**: Can take 5 minutes to 48 hours
- Check status: `dig api.livinglytics.com` or use https://dnschecker.org

## Step 4: Update OAuth Provider Settings

### 4.1 Google Cloud Console
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to **APIs & Services** → **Credentials**
3. Click on your OAuth 2.0 Client ID
4. Under **Authorized redirect URIs**, add:
   ```
   https://api.livinglytics.com/v1/auth/google/callback
   ```
5. Click **Save**

### 4.2 Meta for Developers
1. Go to [Meta for Developers](https://developers.facebook.com/)
2. Select your app
3. Go to **Facebook Login** → **Settings** (or **App Settings** → **Basic**)
4. Find **"Valid OAuth Redirect URIs"**
5. Add:
   ```
   https://api.livinglytics.com/v1/connections/instagram/callback
   ```
6. Click **"Save Changes"**
7. Ensure app is in **"Live" mode** (not Development)

## Step 5: Test Production Deployment

### 5.1 Verify Domains Are Live
- Visit `https://livinglytics.com` - Should load the marketing site
- Visit `https://api.livinglytics.com` - Should return API health check

### 5.2 Test OAuth Flows
1. Go to `https://livinglytics.com`
2. Click **"Get Started"** or **"Sign In"**
3. Test email/password registration
4. Test Google OAuth sign-in
5. Go to `/connect` page
6. Test Google Analytics connection
7. Test Instagram Business connection
8. Verify disconnect functionality

### 5.3 Verify Callbacks
Check that after OAuth:
- Google: Redirects to `https://livinglytics.com/connect/callback?provider=google&status=success&token=...`
- Instagram: Redirects to `https://livinglytics.com/connect/callback?provider=instagram&status=success`

## Step 6: Monitor & Troubleshoot

### Common Issues

**CORS Errors**
- Verify CORS origins in `main.py` include `https://livinglytics.com`
- Check browser console for specific errors

**OAuth Not Working**
- Verify redirect URIs match exactly (no trailing slashes)
- Check environment variables in deployment (FRONTEND_URL, GOOGLE_REDIRECT_URI, META_OAUTH_REDIRECT)
- Ensure OAuth apps are in Live/Production mode

**DNS Not Resolving**
- Wait longer for propagation (can take up to 48 hours)
- Use `dig` or online DNS checker tools
- Verify DNS records match exactly what Replit provided

**Database Connection Errors**
- Ensure DATABASE_URL is set in deployment secrets
- Check Replit PostgreSQL is enabled for the deployment

## Rollback Plan

If you need to roll back:
1. Update DNS to point back to Replit dev domain
2. Revert environment variables in Replit Secrets
3. Update OAuth providers back to dev URIs

## Post-Deployment

- Set up monitoring/alerts (optional: Sentry, Uptime Robot)
- Configure email domain authentication (SPF, DKIM for Resend)
- Consider SSL certificate renewal (Replit handles this automatically)
- Document any custom configuration in `replit.md`

## Support

- Replit Docs: https://docs.replit.com/hosting/deployments/about-deployments
- Custom Domains: https://docs.replit.com/hosting/deployments/custom-domains

---

**Last Updated**: $(date +%Y-%m-%d)
**Deployment Type**: Option B - Separate API Subdomain
**Domains**: livinglytics.com (frontend), api.livinglytics.com (backend)
