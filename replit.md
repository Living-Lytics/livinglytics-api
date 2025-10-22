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
The API is built using Python 3.11 and FastAPI for high-performance web services. SQLAlchemy 2.x with psycopg 3.x is used for ORM and PostgreSQL connectivity. Data validation is handled by Pydantic. GitHub integration utilizes PyGithub and the Replit GitHub Connector for OAuth.

### Database Schema
The system uses a PostgreSQL database with three core tables:
- **Users**: Stores user information (`id`, `email`, `org_id`, `created_at`).
- **Data Sources**: Manages connections to external data sources, including OAuth tokens (`id`, `user_id`, `source_name`, `account_ref`, `access_token`, `refresh_token`, `expires_at`, `created_at`, `updated_at`).
- **Metrics**: Stores collected metric data, linked to users and sources (`id`, `user_id`, `source_name`, `metric_date`, `metric_name`, `metric_value`, `meta`, `created_at`).
Row-Level Security (RLS) is enabled on all tables, with a default-deny policy, ensuring data access is managed through the backend service role.

### API Endpoints
The API provides several categories of endpoints:
- **Health Checks**: Liveness and readiness endpoints for service monitoring.
- **Development**: Endpoint for seeding users for testing purposes.
- **Analytics**:
    - `POST /v1/metrics/ingest`: For ingesting metrics data from various sources.
    - `GET /v1/dashboard/tiles`: Aggregates and returns metrics suitable for dashboard display.
- **GitHub Integration**:
    - `GET /v1/github/user`: Retrieves authenticated GitHub user information.
    - `GET /v1/github/repos`: Lists public repositories for the authenticated user.
- **Scheduled Tasks**:
    - `POST /v1/digest/weekly`: Generates a weekly digest summary, designed for scheduled execution.

### Authentication
All protected API endpoints require Bearer token authentication using a `FASTAPI_SECRET_KEY`.

### Configuration
The application is configured to run on `0.0.0.0` at port `5000`. CORS is intelligently managed via the `ALLOW_ORIGINS` environment variable, supporting flexible development and secure production deployments that automatically allow www.livinglytics.com and Base44 domains. Environment variables manage database connection strings (DATABASE_URL for direct connection on port 5432), Supabase keys, and the FastAPI secret key. Logging is configured at INFO level for production visibility.

## External Dependencies
- **Supabase PostgreSQL**: The primary database for the application, accessed via direct connection (port 5432) for production stability.
- **GitHub API**: Integrated for fetching user and repository information, leveraging the Replit GitHub Connector for OAuth.
- **Uvicorn**: ASGI server used to run the FastAPI application.
- **SQLAlchemy**: Python SQL toolkit and Object Relational Mapper.
- **psycopg**: PostgreSQL adapter for Python.
- **PyGithub**: Python library for interacting with the GitHub API.

## Production Deployment Notes
- Use DATABASE_URL with direct connection string (port 5432) in deployment secrets
- Set ALLOW_ORIGINS=https://www.livinglytics.com for production CORS
- Weekly digest endpoint designed for Base44 scheduled functions (Mondays 08:00 AM PT)
- Monitor logs for [WEEKLY DIGEST] entries to track scheduled function execution