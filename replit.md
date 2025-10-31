# Living Lytics API

## Overview
Living Lytics API is a production-ready analytics engine and data integration platform built with FastAPI. It connects to a Supabase PostgreSQL database for robust data management, supporting data ingestion, aggregation for dashboards, and integrations with external services like GitHub, Google Analytics 4, and Instagram. The API powers analytics across various data sources, offering insights, reporting capabilities, automatic token refresh for long-lived OAuth connections, and secure operations with CORS configuration and comprehensive logging.

## User Preferences
- Using Supabase for PostgreSQL database (not Replit DB)
- **Direct connection preferred** over connection pooler (port 5432 vs 6543) to avoid pgBouncer prepared statement conflicts
- **JWT-based authentication** with email/password registration and Google OAuth sign-in
- **bcrypt 4.0.1** for password hashing (passlib compatibility, avoids 72-byte password limit issues)
- **Proper HTTP status codes**: 400 for validation errors (duplicate email), 401 for authentication failures, 200 for success
- **OAuth disconnection** actually deletes DataSource records to sever connections completely
- Bearer token authentication for API security (FASTAPI_SECRET_KEY)
- **Admin endpoints protected** with separate ADMIN_TOKEN for sensitive operations
- Idempotent schema management approach with startup migrations for adding columns
- GitHub integration via Replit connector for automatic OAuth management
- **Google OAuth integration** for GA4 analytics with automatic 30-day backfill
- **Instagram OAuth integration** via Facebook Graph API for reach/engagement metrics with automatic 30-day backfill
- **Meta/Facebook OAuth** environment variables (META_APP_ID, META_APP_SECRET, META_OAUTH_REDIRECT) for Instagram Graph API integration
- **Automatic token refresh** for Instagram long-lived tokens (60 days) when expiring within 7 days
- **Admin manual token refresh** endpoint for Instagram connections
- **OAuth callbacks redirect** to frontend `/connect/callback?provider=X&status=success/error`
- Public-only data exposure for GitHub endpoints (private repos filtered)
- **Onboarding flow**: After login, new users complete onboarding questions (industry, role, goal), then connect data sources before accessing dashboard
- **AuthGuard routing**: Enforces login → onboarding → connect → dashboard sequence; unauthenticated users redirected to /signin when accessing app routes
- **Shared Auth State**: Centralized auth state management with AuthProvider context (src/state/auth.tsx) eliminates duplicate fetches and prevents redirect loops
- **AuthBootstrap**: Single auth fetch on app mount sets ready flag; all components wait for ready before routing decisions
- **GlobalCtaInterceptor**: Automatically opens sign-in modal for unauthenticated CTA clicks; deactivates when authenticated to prevent interference
- **Redirect Loop Prevention**: AuthGuard uses lastRedirectRef to redirect at most once per state change; allows free navigation to all app routes (/dashboard, /connect, /settings, /insights) once prerequisites met
- **OAuth Replace Navigation**: ConnectCallback uses replace navigation to prevent back-button re-triggering of OAuth flow
- **Theme support**: Light/dark mode toggle in Settings page, persisted to localStorage, applied via Tailwind dark: classes
- **App vs Marketing navigation**: AppTopNav shows for authenticated app routes (/dashboard, /connect, /settings, /insights, /onboarding); marketing nav shows for public pages without "Connections" link
- **Google OAuth with cookies**: Backend uses state parameter to encode next URL (defaults to https://www.livinglytics.com/onboarding); supports ?next= parameter on /v1/auth/google/start; callback sets HttpOnly cookie (domain=.livinglytics.com, SameSite=None, Secure) and 302 redirects to next URL
- **JWT Bearer Authentication**: All API requests use Authorization: Bearer headers with JWT tokens stored in localStorage (ll_token key)
- **/v1/auth/status tolerant**: Returns 200 with authenticated:false for unauthenticated users (no token) instead of 403, properly rejects invalid/expired tokens with 401
- **Onboarding redirect after OAuth**: First-time Google OAuth users automatically redirected to /onboarding before accessing other app routes
- **Vite proxy configuration**: Proxies both /api/* and /v1/* to backend for dev environment OAuth callback handling
- **Structured logging** with user_id, period, and status for digest operations
- **Cache-Control headers** on timeline endpoint (5 minutes) for performance
- INFO-level logging for production visibility (including weekly digest tracking)

## System Architecture

### Deployment Architecture
The project consists of two services running simultaneously:
- **Marketing Site** (Vite + React): Runs on port 5000 (webview output for Replit preview)
- **Backend API** (FastAPI): Runs on port 8080 (console output)

The marketing site uses a Vite proxy to forward `/api/*` requests to the backend API on port 8080, avoiding CORS issues during development. Configuration:
- `.env.local`: `VITE_API_BASE=/api`, `VITE_API_HEALTH=/v1/health/liveness`
- `vite.config.js`: Proxy rewrites `/api` → `http://localhost:8080`

### Tech Stack
The API is built with Python 3.11 and FastAPI. It uses SQLAlchemy 2.x with psycopg 3.x for PostgreSQL connectivity, Pydantic for data validation, PyGithub and Replit GitHub Connector for GitHub integration, and httpx for Resend API integration.

The marketing site is built with Vite, React, and Tailwind CSS. It includes:
- **Public Pages**: Features, pricing, integrations, case studies, contact, and marketing content
- **App Pages**: Dashboard, Onboarding, Settings, Insights, and Connections management
- **Theme System**: Light/dark mode support with localStorage persistence via ThemeProvider
- **App Navigation**: Dedicated AppTopNav for authenticated users with dashboard, connections, insights, and settings links
- **Auth Guard**: Route guard that enforces login → onboarding → connect → dashboard flow
- **Onboarding Flow**: First-time user experience with industry, role, and goal questions (localStorage-tracked with optional backend sync to `/v1/onboarding`)

### Database Schema
A PostgreSQL database stores user information, data source connections (including OAuth tokens), selected GA4 properties, collected metric data, email delivery events, and weekly digest run logs. Row-Level Security (RLS) is enabled on all tables with a default-deny policy.

### API Endpoints
The API provides endpoints for:
- **Health Checks**: Liveness and readiness probes.
- **User Authentication**: Email/password registration and login with JWT tokens (POST /v1/auth/register, POST /v1/auth/login), authentication status endpoint (GET /v1/auth/status), Google OAuth sign-in flow (GET /v1/auth/google/start, GET /v1/auth/google/callback), and OAuth disconnect endpoints (POST /v1/auth/google/disconnect, POST /v1/auth/instagram/disconnect).
- **Analytics**: Data ingestion, dashboard tile aggregation, and daily/hourly/monthly metric timelines.
- **GitHub Integration**: Authenticated user and public repository information.
- **Google OAuth / GA4 Integration**: OAuth flow initiation and callback, connection status, listing GA4 properties, and saving selected GA4 properties.
- **GA4 Data Sync**: Auto-backfill (30 days) on first property save. Admin-protected endpoint to manually trigger GA4 data synchronization.
- **Instagram OAuth Integration**: OAuth flow initiation via Facebook OAuth dialog and callback with automatic long-lived token exchange (60 days via Facebook Graph API).
- **Instagram OAuth Flow**: Frontend calls `/v1/auth/instagram/start` with Authorization header (fetch API), receives OAuth URL, then navigates to it; backend `/v1/auth/instagram/start` returns JSON with `url` field instead of redirecting to support Bearer token authentication.
- **Instagram Token Refresh**: Automatic refresh when token expires within 7 days, admin-protected manual refresh endpoint.
- **Instagram Data Sync**: Auto-backfill (30 days) on first connection for reach and engagement metrics. Admin-protected endpoint for manual sync.
- **Email Digests**: Sending personalized weekly digests to users, admin-triggered scheduled runs, previewing digests, testing, status monitoring, scheduling info, and unsubscribe functionality.
- **Webhooks**: Resend webhook event reception for email delivery monitoring.
- **Email Events Monitoring**: Summaries and delivery health KPIs (open, click, bounce rates).
- **System Status**: Public endpoint for system health, environment info, and version.
- **Development & Testing**: Admin-protected endpoints for seeding metric and email event data.

### Authentication
The API implements a comprehensive authentication system with multiple sign-in methods:
- **Email/Password Authentication**: Users can register and log in with email and password. Passwords are hashed using bcrypt (version 4.0.1 for passlib compatibility). JWT tokens are issued with 30-day expiry, containing user email and user_id claims.
- **Google OAuth Sign-In**: Users can authenticate using their Google account. The OAuth flow stores the `google_sub` (Google user ID) in the users table and creates a `google_analytics` DataSource record when connecting GA4.
- **JWT Tokens**: All authenticated endpoints use Bearer token authentication with `FASTAPI_SECRET_KEY`. Tokens are validated on each request to extract user identity.
- **HTTP Status Codes**: Authentication endpoints return proper HTTP status codes (400 for duplicate email, 401 for invalid credentials, 200 for success) to ensure correct frontend error handling.
- **OAuth Disconnection**: Disconnect endpoints actually delete DataSource records and clear OAuth identifiers, properly severing connections.
- **Admin Endpoints**: Sensitive admin endpoints require a separate `ADMIN_TOKEN` and are hidden from the OpenAPI schema.

Database schema additions for authentication:
- `users.password_hash`: TEXT column storing bcrypt-hashed passwords
- `users.google_sub`: TEXT column storing Google OAuth user identifier (nullable)

### Configuration
The backend API runs on `0.0.0.0:8080`. The marketing site runs on `0.0.0.0:5000` (Replit webview port). CORS is restricted to `livinglytics.base44.app`, `preview--livinglytics.base44.app`, `livinglytics.com`, and `localhost:5173`. Environment variables manage database connections, Supabase keys, FastAPI secrets, Resend API keys, and Google OAuth credentials. Structured JSON logging is implemented with optional Sentry integration and thread-safe in-memory rate limiting for admin endpoints.

### Production Deployment (Option B: Separate API Subdomain)
The production deployment uses a dual-domain architecture for optimal performance and separation of concerns:

**Domain Structure:**
- **livinglytics.com** - Frontend (Marketing Site + App) deployed as Autoscale on Replit
- **api.livinglytics.com** - Backend API deployed separately as Autoscale on Replit

**Environment Variables (Production):**
- Backend: `FRONTEND_URL=https://livinglytics.com`, `GOOGLE_REDIRECT_URI=https://api.livinglytics.com/v1/auth/google/callback`, `META_OAUTH_REDIRECT=https://api.livinglytics.com/v1/connections/instagram/callback`
- Frontend: `VITE_API_BASE=https://api.livinglytics.com` (no Vite proxy in production)

**OAuth Provider Configuration:**
- Google Cloud Console: Authorized redirect URI `https://api.livinglytics.com/v1/auth/google/callback`
- Meta for Developers: Valid OAuth Redirect URI `https://api.livinglytics.com/v1/connections/instagram/callback`

**Deployment Steps:**
1. Deploy Backend API as Autoscale, link api.livinglytics.com custom domain
2. Deploy Marketing Site as Autoscale, link livinglytics.com custom domain
3. Configure DNS A and TXT records at domain registrar for both domains
4. Update OAuth providers with production redirect URIs
5. Verify all flows work end-to-end

See `DEPLOYMENT_GUIDE.md` for detailed step-by-step instructions.

## External Dependencies
- **Supabase PostgreSQL**: Primary database.
- **GitHub API**: For user and repository data, via Replit GitHub Connector.
- **Resend API**: Email service for transactional digests and webhooks.
- **Uvicorn**: ASGI server.
- **SQLAlchemy**: ORM.
- **psycopg**: PostgreSQL adapter.
- **PyGithub**: Python GitHub API client.
- **httpx**: HTTP client.
- **email-validator**: Email validation.
- **passlib + bcrypt 4.0.1**: Password hashing and verification.
- **python-jose**: JWT token generation and validation.
- **python-multipart**: Form data parsing for OAuth callbacks.