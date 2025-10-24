# Living Lytics API

## Overview
Living Lytics API is a backend service built with FastAPI, designed as an analytics engine and data integration platform. It connects to a Supabase PostgreSQL database to provide a robust data management solution. The API supports data ingestion, aggregation for dashboards, and integrations with external services like GitHub. Its primary purpose is to power analytics for various data sources, offering insights and reporting capabilities. The project is production-ready, featuring secure database connections, CORS configuration, and logging for operational visibility.

## User Preferences
- Using Supabase for PostgreSQL database (not Replit DB)
- **Direct connection preferred** over connection pooler (port 5432 vs 6543) to avoid pgBouncer prepared statement conflicts
- Bearer token authentication for API security (FASTAPI_SECRET_KEY)
- **Admin endpoints protected** with separate ADMIN_TOKEN for sensitive operations
- Idempotent schema management approach
- GitHub integration via Replit connector for automatic OAuth management
- Public-only data exposure for GitHub endpoints (private repos filtered)
- **Structured logging** with user_id, period, and status for digest operations
- **Cache-Control headers** on timeline endpoint (5 minutes) for performance
- INFO-level logging for production visibility (including weekly digest tracking)

## System Architecture

### Tech Stack
The API is built using Python 3.11 and FastAPI for high-performance web services. SQLAlchemy 2.x with psycopg 3.x is used for ORM and PostgreSQL connectivity. Data validation is handled by Pydantic (with email-validator for EmailStr). GitHub integration utilizes PyGithub and the Replit GitHub Connector for OAuth. Email sending uses httpx to integrate with the Resend API for transactional emails.

### Database Schema
The system uses a PostgreSQL database with five core tables:
- **Users**: Stores user information (`id`, `email`, `org_id`, `created_at`).
- **Data Sources**: Manages connections to external data sources, including OAuth tokens (`id`, `user_id`, `source_name`, `account_ref`, `access_token`, `refresh_token`, `expires_at`, `created_at`, `updated_at`). Used for Google OAuth (source_name="google") and other integrations.
- **Metrics**: Stores collected metric data, linked to users and sources (`id`, `user_id`, `source_name`, `metric_date`, `metric_name`, `metric_value`, `meta`, `created_at`).
- **Email Events**: Tracks email delivery events from Resend webhooks (`id`, `email`, `event_type`, `provider_id`, `subject`, `payload`, `created_at`). Used for monitoring email delivery, bounces, opens, clicks, and complaints.
- **Digest Runs**: Tracks weekly digest execution with rate limiting (`id`, `started_at`, `finished_at`, `sent`, `errors`). Prevents duplicate runs within 10 minutes.
Row-Level Security (RLS) is enabled on all tables, with a default-deny policy, ensuring data access is managed through the backend service role.

### API Endpoints
The API provides several categories of endpoints:
- **Root**:
    - `GET /`: Friendly welcome message with API documentation link.
- **Health Checks**: 
    - `GET /v1/health/liveness`: Simple liveness check (returns 200).
    - `GET /v1/health/readiness`: Database and environment readiness check.
- **Development**: Endpoint for seeding users for testing purposes.
- **Analytics**:
    - `POST /v1/metrics/ingest`: For ingesting metrics data from various sources.
    - `GET /v1/dashboard/tiles`: Aggregates and returns metrics suitable for dashboard display.
    - `GET /v1/metrics/timeline`: Returns daily metrics timeline for a user (params: user_email, days). Returns array of `{date, sessions, conversions, reach, engagement}`. Enforces strict user isolation (no cross-tenant data).
- **GitHub Integration**:
    - `GET /v1/github/user`: Retrieves authenticated GitHub user information.
    - `GET /v1/github/repos`: Lists public repositories for the authenticated user.
- **Google OAuth / GA4 Integration**:
    - `GET /v1/connections/google/init`: Initiate Google OAuth flow for GA4. Query param: `email`. Redirects to Google consent screen with analytics.readonly scope. Uses state parameter to track user email.
    - `GET /v1/connections/google/callback`: OAuth callback endpoint. Receives authorization code, exchanges for access/refresh tokens, stores in data_sources table. Logs "[OAUTH] Google connected for user=<email>".
    - `GET /v1/connections/status`: **Auth required** - Returns list of connected providers (google, etc.) with token expiration timestamps for a user. Query param: `email`.
- **Email Digests** (Resend integration with rate limiting and retry):
    - `POST /v1/digest/run`: Send digest to a specific user. Body: `{user_email, days}`. Resolves email to account_id (strict match), queries metrics for that account only, sends personalized digest. Returns `{sent, user_email, period_start, period_end, days}`.
    - `POST /v1/digest/scheduled-run-all`: **Admin endpoint** (requires ADMIN_TOKEN) to manually trigger weekly digest for all opted-in users. Hidden from schema. Uses scheduler logic with idempotent tracking.
    - `POST /v1/digest/weekly`: Legacy weekly digest endpoint. Supports `scope: "email"` for single user or `scope: "all"` for all users. Includes rate limiting (10-minute cooldown) and automatic retry with exponential backoff (3 attempts: 0.5s, 1s, 2s).
    - `GET /v1/digest/preview`: Returns HTML preview of digest email for visual QA (no email sent).
    - `POST /v1/digest/test`: Sends test digest email to specified address for integration verification.
    - `GET /v1/digest/status`: Returns status of the last digest run (started_at, finished_at, sent count, error count).
    - `GET /v1/digest/schedule`: View APScheduler status and next run time (Monday 07:00 PT).
    - `GET /v1/digest/preferences`: Get user's opt-in status for weekly digests.
    - `PUT /v1/digest/preferences`: Update user's opt-in preference.
    - `GET /v1/digest/unsubscribe`: JWT-based unsubscribe from email links (1-year token validity).
- **Webhooks** (no auth required):
    - `POST /v1/webhooks/resend`: Receives webhook events from Resend (delivered, bounced, complained, opened, clicked). Stores events in email_events table for monitoring.
- **Email Events Monitoring**:
    - `GET /v1/email-events/summary`: Returns paginated email events summary with filters (email, start, end, page, limit). Supports date range filtering and pagination with metadata.
    - `GET /v1/email-events/health`: **Delivery health KPIs** - Returns open_rate, click_rate, bounce_rate for a user's email events. Params: email, start, end. **Cached for 5 minutes** with `Cache-Control: max-age=300`.
- **Metrics Analytics**:
    - `GET /v1/metrics/timeline`: Returns daily metrics timeline for a user (params: user_email, days). **Cached for 5 minutes** with `Cache-Control: max-age=300` header. Returns array of `{date, sessions, conversions, reach, engagement}`. Enforces strict user isolation (no cross-tenant data).
    - `GET /v1/metrics/timeline/day`: Returns **24 hourly data points** for intraday analytics. Params: email, hours (default 24). Cached for 5 minutes.
    - `GET /v1/metrics/timeline/month`: Returns **30 daily data points** for monthly trends. Params: email, days (default 30). Cached for 5 minutes.
- **System Status**:
    - `GET /v1/status`: **Public endpoint** returning system status for UI badge/health checks. Returns environment, timezone, scheduler next run, email provider, and version (git SHA). No authentication required.
- **Development & Testing** (admin-protected, hidden from schema):
    - `POST /v1/dev/seed-metrics`: Seeds realistic metric data for testing. Body: `{email, days}`. Requires ADMIN_TOKEN. Rate-limited.
    - `POST /v1/dev/seed-email-events`: Seeds email event data with realistic distribution. Body: `{email, events, start?, end?}`. Requires ADMIN_TOKEN. Rate-limited.

### Authentication
- **Standard endpoints**: Bearer token authentication using `FASTAPI_SECRET_KEY`
- **Admin endpoints**: Separate Bearer token authentication using `ADMIN_TOKEN` (required for `/v1/digest/scheduled-run-all` and other admin operations)
- Admin endpoints are hidden from OpenAPI schema (`include_in_schema=False`) to prevent discovery

### Configuration
The application is configured to run on `0.0.0.0` at port `5000`. **CORS is locked down** to Base44 domains: `livinglytics.base44.app`, `livinglytics.com`, and `localhost:5173` (for local development). Only GET, POST, and OPTIONS methods are allowed with Authorization and Content-Type headers. Environment variables manage database connection strings (DATABASE_URL for direct connection on port 5432, with automatic fallback to connection pooler on port 6543 for IPv6 issues), Supabase keys, and the FastAPI secret key. **Structured JSON logging** with request_id tracking for distributed tracing. Optional **Sentry integration** if SENTRY_DSN is set. **Thread-safe in-memory rate limiter** protects admin endpoints (10 capacity, 0.5 refill rate). Logging configured at INFO level for production visibility, including [WEEKLY DIGEST], [DIGEST RUN], [EMAIL HEALTH], [SEED METRICS], [SEED EMAIL EVENTS], and [RESEND] entries.

## External Dependencies
- **Supabase PostgreSQL**: The primary database for the application, accessed via direct connection (port 5432) for production stability.
- **GitHub API**: Integrated for fetching user and repository information, leveraging the Replit GitHub Connector for OAuth.
- **Resend API**: Email service provider for sending transactional weekly digest emails.
- **Uvicorn**: ASGI server used to run the FastAPI application.
- **SQLAlchemy**: Python SQL toolkit and Object Relational Mapper.
- **psycopg**: PostgreSQL adapter for Python.
- **PyGithub**: Python library for interacting with the GitHub API.
- **httpx**: Modern HTTP client library used for Resend API integration.
- **email-validator**: Email validation library for Pydantic EmailStr support.

## Production Deployment Notes
- Use DATABASE_URL with direct connection string (port 5432) in deployment secrets
- CORS is locked to Base44 domains: `livinglytics.base44.app`, `livinglytics.com`, and `localhost:5173` (hardcoded for security)
- **Required Environment Variables**:
  - `FASTAPI_SECRET_KEY`: API key for standard endpoint authentication
  - `ADMIN_TOKEN`: **Required for admin endpoints** (manual digest triggers, data seeders, sensitive operations)
  - `RESEND_API_KEY`: API key from Resend dashboard
  - `MAIL_FROM`: Verified sender email address (e.g., noreply@livinglytics.com)
  - `MAIL_FROM_NAME`: Display name for emails (default: "Living Lytics")
  - `GOOGLE_CLIENT_ID`: Google OAuth client ID from Google Cloud Console
  - `GOOGLE_CLIENT_SECRET`: Google OAuth client secret
  - `GOOGLE_OAUTH_REDIRECT`: OAuth callback URL (e.g., https://api.livinglytics.com/v1/connections/google/callback)
- **Optional Environment Variables**:
  - `SENTRY_DSN`: Sentry DSN for error tracking (optional)
  - `ENV`: Environment name for logging/Sentry (default: "production")
  - `VERSION`: Version identifier (defaults to git SHA: 69a2772)
- **Resend Webhook Configuration**:
  - **Webhook URL**: `POST /v1/webhooks/resend`
  - **Secret**: Set `RESEND_WEBHOOK_SECRET` environment variable in deployment
  - **Header verified**: `X-Resend-Signature` (HMAC-SHA256 over raw body)
  - **Idempotency**: Unique index on `provider_id`, uses `ON CONFLICT DO NOTHING` to prevent duplicate events
  - **Events tracked**: email.delivered, email.bounced, email.complained, email.opened, email.clicked
  - **Security**: HMAC signature verification protects against spoofed webhook requests
  - **Verification endpoint**: `GET /v1/webhooks/resend/check` (Bearer-protected) to verify secret is configured
  - Monitor email delivery via `/v1/email-events/summary` endpoint
- **APScheduler**: Automatic weekly digest system runs Mondays 07:00 AM PT (America/Los_Angeles timezone)
- **Rate Limiting**: Digest runs are limited to one every 10 minutes to prevent duplicate sends
- **Retry Logic**: Email sending retries up to 3 times with exponential backoff (0.5s, 1s, 2s) on rate limits (429) or server errors (5xx)
- **Structured Logging**: All digest operations log `user_id`, `period_start`, `period_end`, and `status` for observability
- Monitor logs for [SCHEDULER], [DIGEST], [ADMIN], [RESEND WEBHOOK], and [RESEND] entries
- Email digests include KPI metrics (sessions, conversions, reach, engagement) with automatic insights and action items
- Use `/v1/digest/status` to check last digest run status before triggering new runs
- **Delivery Health Monitoring**: Use `/v1/email-events/health` to track email delivery rates (open_rate, click_rate, bounce_rate) for quality assurance
- **Data Seeding**: Use admin-protected seeder endpoints for testing and demos (POST /v1/dev/seed-metrics, POST /v1/dev/seed-email-events)
- **Rate Limiting**: Thread-safe token bucket limiter protects admin endpoints (10 requests capacity, refills 1 every 2 seconds)
- **Production Sanity Check**: Run `./scripts/prod_check.sh https://api.livinglytics.com $FASTAPI_SECRET_KEY demo@livinglytics.app` to verify health, scheduler, and timeline endpoints
- **New Features (Oct 2025)**:
  - Timeline variants: hourly (`/v1/metrics/timeline/day`) and monthly (`/v1/metrics/timeline/month`) aggregations
  - Email delivery health KPIs with open/click/bounce rates
  - System status endpoint for UI badges and monitoring
  - Structured JSON logging with request_id for distributed tracing
  - Optional Sentry error tracking
  - Thread-safe rate limiting for admin operations
  - **Google OAuth integration** for GA4 connectivity with analytics.readonly scope, automatic token refresh storage, and connection status tracking