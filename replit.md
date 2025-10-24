# Living Lytics API

## Overview
Living Lytics API is a production-ready analytics engine and data integration platform built with FastAPI. It connects to a Supabase PostgreSQL database for robust data management, supporting data ingestion, aggregation for dashboards, and integrations with external services like GitHub and Google Analytics 4. The API powers analytics across various data sources, offering insights, reporting capabilities, and secure operations with CORS configuration and comprehensive logging.

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
The API is built with Python 3.11 and FastAPI. It uses SQLAlchemy 2.x with psycopg 3.x for PostgreSQL connectivity, Pydantic for data validation, PyGithub and Replit GitHub Connector for GitHub integration, and httpx for Resend API integration.

### Database Schema
A PostgreSQL database stores user information, data source connections (including OAuth tokens), selected GA4 properties, collected metric data, email delivery events, and weekly digest run logs. Row-Level Security (RLS) is enabled on all tables with a default-deny policy.

### API Endpoints
The API provides endpoints for:
- **Health Checks**: Liveness and readiness probes.
- **Analytics**: Data ingestion, dashboard tile aggregation, and daily/hourly/monthly metric timelines.
- **GitHub Integration**: Authenticated user and public repository information.
- **Google OAuth / GA4 Integration**: OAuth flow initiation and callback, connection status, listing GA4 properties, and saving selected GA4 properties.
- **GA4 Data Sync**: Auto-backfill (30 days) on first property save. Admin-protected endpoint to manually trigger GA4 data synchronization.
- **Email Digests**: Sending personalized weekly digests to users, admin-triggered scheduled runs, previewing digests, testing, status monitoring, scheduling info, and unsubscribe functionality.
- **Webhooks**: Resend webhook event reception for email delivery monitoring.
- **Email Events Monitoring**: Summaries and delivery health KPIs (open, click, bounce rates).
- **System Status**: Public endpoint for system health, environment info, and version.
- **Development & Testing**: Admin-protected endpoints for seeding metric and email event data.

### Authentication
Standard endpoints use Bearer token authentication with `FASTAPI_SECRET_KEY`. Admin endpoints require a separate `ADMIN_TOKEN` and are hidden from the OpenAPI schema.

### Configuration
The application runs on `0.0.0.0:5000`. CORS is restricted to `livinglytics.base44.app`, `livinglytics.com`, and `localhost:5173`. Environment variables manage database connections, Supabase keys, FastAPI secrets, Resend API keys, and Google OAuth credentials. Structured JSON logging is implemented with optional Sentry integration and thread-safe in-memory rate limiting for admin endpoints.

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