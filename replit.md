# Living Lytics API

## Overview
Living Lytics API is a backend service built with FastAPI, designed as an analytics engine and data integration platform. It connects to a Supabase PostgreSQL database to provide a robust data management solution. The API supports data ingestion, aggregation for dashboards, and integrations with external services like GitHub. Its primary purpose is to power analytics for various data sources, offering insights and reporting capabilities. The project is production-ready, featuring secure database connections, CORS configuration, and logging for operational visibility.

## User Preferences
- Using Supabase for PostgreSQL database (not Replit DB)
- **Direct connection preferred** over connection pooler (port 5432 vs 6543) to avoid pgBouncer prepared statement conflicts
- Bearer token authentication for API security
- Idempotent schema management approach
- GitHub integration via Replit connector for automatic OAuth management
- Public-only data exposure for GitHub endpoints (private repos filtered)
- INFO-level logging for production visibility (including weekly digest tracking)

## System Architecture

### Tech Stack
The API is built using Python 3.11 and FastAPI for high-performance web services. SQLAlchemy 2.x with psycopg 3.x is used for ORM and PostgreSQL connectivity. Data validation is handled by Pydantic (with email-validator for EmailStr). GitHub integration utilizes PyGithub and the Replit GitHub Connector for OAuth. Email sending uses httpx to integrate with the Resend API for transactional emails.

### Database Schema
The system uses a PostgreSQL database with five core tables:
- **Users**: Stores user information (`id`, `email`, `org_id`, `created_at`).
- **Data Sources**: Manages connections to external data sources, including OAuth tokens (`id`, `user_id`, `source_name`, `account_ref`, `access_token`, `refresh_token`, `expires_at`, `created_at`, `updated_at`).
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
- **Email Digests** (Resend integration with rate limiting and retry):
    - `POST /v1/digest/run`: Send digest to a specific user. Body: `{user_email, days}`. Resolves email to account_id (strict match), queries metrics for that account only, sends personalized digest. Returns `{sent, user_email, period_start, period_end, days}`.
    - `POST /v1/digest/run-all`: Admin endpoint to send digest to all users. Body: `{days}`. Iterates all users with 0.5s throttling to avoid provider limits.
    - `POST /v1/digest/weekly`: Legacy weekly digest endpoint. Supports `scope: "email"` for single user or `scope: "all"` for all users. Includes rate limiting (10-minute cooldown) and automatic retry with exponential backoff (3 attempts: 0.5s, 1s, 2s).
    - `GET /v1/digest/preview`: Returns HTML preview of digest email for visual QA (no email sent).
    - `POST /v1/digest/test`: Sends test digest email to specified address for integration verification.
    - `GET /v1/digest/status`: Returns status of the last digest run (started_at, finished_at, sent count, error count).
- **Webhooks** (no auth required):
    - `POST /v1/webhooks/resend`: Receives webhook events from Resend (delivered, bounced, complained, opened, clicked). Stores events in email_events table for monitoring.
- **Email Events Monitoring**:
    - `GET /v1/email-events/summary`: Returns summary of email events from last 24 hours with breakdown by type and latest 10 events.

### Authentication
All protected API endpoints require Bearer token authentication using a `FASTAPI_SECRET_KEY`.

### Configuration
The application is configured to run on `0.0.0.0` at port `5000`. **CORS is locked down** to Base44 domains: `livinglytics.base44.app`, `livinglytics.com`, and `localhost:5173` (for local development). Only GET, POST, and OPTIONS methods are allowed with Authorization and Content-Type headers. Environment variables manage database connection strings (DATABASE_URL for direct connection on port 5432, with automatic fallback to connection pooler on port 6543 for IPv6 issues), Supabase keys, and the FastAPI secret key. Logging is configured at INFO level for production visibility, including [WEEKLY DIGEST], [DIGEST RUN], [DIGEST RUN-ALL], [METRICS TIMELINE], [DIGEST PREVIEW], [DIGEST TEST], [RESEND WEBHOOK], and [RESEND] retry logging.

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
- **Required Resend Environment Variables**:
  - `RESEND_API_KEY`: API key from Resend dashboard
  - `MAIL_FROM`: Verified sender email address (e.g., noreply@livinglytics.com)
  - `MAIL_FROM_NAME`: Display name for emails (default: "Living Lytics")
- **Resend Webhook Configuration**:
  - **Webhook URL**: `POST /v1/webhooks/resend`
  - **Secret**: Set `RESEND_WEBHOOK_SECRET` environment variable in deployment
  - **Header verified**: `X-Resend-Signature` (HMAC-SHA256 over raw body)
  - **Idempotency**: Unique index on `provider_id`, uses `ON CONFLICT DO NOTHING` to prevent duplicate events
  - **Events tracked**: email.delivered, email.bounced, email.complained, email.opened, email.clicked
  - **Security**: HMAC signature verification protects against spoofed webhook requests
  - **Verification endpoint**: `GET /v1/webhooks/resend/check` (Bearer-protected) to verify secret is configured
  - Monitor email delivery via `/v1/email-events/summary` endpoint
- Weekly digest endpoint designed for Base44 scheduled functions (Mondays 08:00 AM PT)
- **Rate Limiting**: Digest runs are limited to one every 10 minutes to prevent duplicate sends
- **Retry Logic**: Email sending retries up to 3 times with exponential backoff (0.5s, 1s, 2s) on rate limits (429) or server errors (5xx)
- Monitor logs for [WEEKLY DIGEST], [RESEND WEBHOOK], and [RESEND] entries
- Email digests include KPI metrics (sessions, conversions, reach, engagement) with automatic insights and action items
- Use `/v1/digest/status` to check last digest run status before triggering new runs