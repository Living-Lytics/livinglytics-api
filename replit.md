# Living Lytics API

## Overview
Living Lytics API is a production-ready analytics engine and data integration platform built with FastAPI. It connects to a Supabase PostgreSQL database for robust data management, supporting data ingestion, aggregation for dashboards, and integrations with external services like GitHub, Google Analytics 4, and Instagram. The API powers analytics across various data sources, offering insights, reporting capabilities, automatic token refresh for long-lived OAuth connections, and secure operations with CORS configuration and comprehensive logging.

## User Preferences
- Using Supabase for PostgreSQL database (not Replit DB)
- **Direct connection preferred** over connection pooler (port 5432 vs 6543) to avoid pgBouncer prepared statement conflicts
- Bearer token authentication for API security (FASTAPI_SECRET_KEY)
- **Admin endpoints protected** with separate ADMIN_TOKEN for sensitive operations
- Idempotent schema management approach
- GitHub integration via Replit connector for automatic OAuth management
- **Google OAuth integration** for GA4 analytics with automatic 30-day backfill
- **Instagram OAuth integration** via Facebook Graph API for reach/engagement metrics with automatic 30-day backfill
- **Meta/Facebook OAuth** environment variables (META_APP_ID, META_APP_SECRET, META_OAUTH_REDIRECT) for Instagram Graph API integration
- **Automatic token refresh** for Instagram long-lived tokens (60 days) when expiring within 7 days
- **Admin manual token refresh** endpoint for Instagram connections
- Public-only data exposure for GitHub endpoints (private repos filtered)
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

The marketing site is built with Vite, React, and Tailwind CSS. It includes pages for features, pricing, integrations, case studies, and contact information.

### Database Schema
A PostgreSQL database stores user information, data source connections (including OAuth tokens), selected GA4 properties, collected metric data, email delivery events, and weekly digest run logs. Row-Level Security (RLS) is enabled on all tables with a default-deny policy.

### API Endpoints
The API provides endpoints for:
- **Health Checks**: Liveness and readiness probes.
- **Analytics**: Data ingestion, dashboard tile aggregation, and daily/hourly/monthly metric timelines.
- **GitHub Integration**: Authenticated user and public repository information.
- **Google OAuth / GA4 Integration**: OAuth flow initiation and callback, connection status, listing GA4 properties, and saving selected GA4 properties.
- **GA4 Data Sync**: Auto-backfill (30 days) on first property save. Admin-protected endpoint to manually trigger GA4 data synchronization.
- **Instagram OAuth Integration**: OAuth flow initiation via Facebook OAuth dialog and callback with automatic long-lived token exchange (60 days via Facebook Graph API).
- **Instagram Token Refresh**: Automatic refresh when token expires within 7 days, admin-protected manual refresh endpoint.
- **Instagram Data Sync**: Auto-backfill (30 days) on first connection for reach and engagement metrics. Admin-protected endpoint for manual sync.
- **Email Digests**: Sending personalized weekly digests to users, admin-triggered scheduled runs, previewing digests, testing, status monitoring, scheduling info, and unsubscribe functionality.
- **Webhooks**: Resend webhook event reception for email delivery monitoring.
- **Email Events Monitoring**: Summaries and delivery health KPIs (open, click, bounce rates).
- **System Status**: Public endpoint for system health, environment info, and version.
- **Development & Testing**: Admin-protected endpoints for seeding metric and email event data.

### Authentication
Standard endpoints use Bearer token authentication with `FASTAPI_SECRET_KEY`. Admin endpoints require a separate `ADMIN_TOKEN` and are hidden from the OpenAPI schema.

### Configuration
The backend API runs on `0.0.0.0:8080`. The marketing site runs on `0.0.0.0:5000` (Replit webview port). CORS is restricted to `livinglytics.base44.app`, `preview--livinglytics.base44.app`, `livinglytics.com`, and `localhost:5173`. Environment variables manage database connections, Supabase keys, FastAPI secrets, Resend API keys, and Google OAuth credentials. Structured JSON logging is implemented with optional Sentry integration and thread-safe in-memory rate limiting for admin endpoints.

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