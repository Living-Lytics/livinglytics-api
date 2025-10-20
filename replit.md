# Living Lytics API

## Overview
Backend API for Living Lytics – an analytics engine and data integration service built with FastAPI and connected to Supabase PostgreSQL.

**Project Type:** Backend API  
**Language:** Python 3.11  
**Framework:** FastAPI  
**Database:** Supabase PostgreSQL (via connection pooler)  
**Current State:** Fully connected to Supabase with authentication, health checks, and analytics endpoints

## Recent Changes
- **2025-10-20:** Supabase Integration Complete
  - Connected to Supabase PostgreSQL via connection pooler (port 6543)
  - Installed SQLAlchemy 2.x and psycopg 3.x for database connectivity
  - Created database models: User, DataSource, and Metric
  - Implemented idempotent schema creation (users, data_sources, metrics tables)
  - Added Bearer token authentication with FASTAPI_SECRET_KEY
  - Implemented health check endpoints (liveness and readiness)
  - Added user seeding endpoint for development
  - Created dashboard tiles endpoint for metrics aggregation
  - Updated CORS configuration to use ALLOW_ORIGINS environment variable

- **2025-10-20:** Initial project setup in Replit environment
  - Installed Python 3.11 and FastAPI dependencies
  - Created basic API structure with three endpoints
  - Configured workflow to run on port 5000
  - Verified API is running and accessible

## Project Architecture

### Tech Stack
- **Python 3.11:** Core language
- **FastAPI:** Modern, high-performance web framework
- **Uvicorn:** ASGI server with hot reload support
- **SQLAlchemy 2.x:** ORM for database operations
- **psycopg 3.x:** PostgreSQL adapter (binary version)
- **Supabase:** PostgreSQL database hosting with connection pooler
- **Pydantic:** Data validation using Python type annotations

### Project Structure
```
.
├── main.py              # FastAPI application with health, auth, and analytics endpoints
├── db.py                # SQLAlchemy database engine and session management
├── models.py            # Database ORM models (User, DataSource, Metric)
├── schema_sql.py        # Idempotent DDL schema creation script
├── supabase_client.py   # Supabase configuration stub for future frontend use
├── requirements.txt     # Python dependencies
├── README.md           # Project description
└── replit.md           # This documentation file
```

### Database Schema

#### Users Table
- `id` (UUID): Primary key
- `email` (TEXT): Unique user email
- `org_id` (UUID): Optional organization reference
- `created_at` (TIMESTAMPTZ): Creation timestamp

#### Data Sources Table
- `id` (UUID): Primary key
- `user_id` (UUID): Foreign key to users
- `source_name` (TEXT): Name of the data source (e.g., "google_analytics", "instagram")
- `account_ref` (TEXT): External account reference
- `access_token` (TEXT): OAuth access token
- `refresh_token` (TEXT): OAuth refresh token
- `expires_at` (TIMESTAMPTZ): Token expiration time
- `created_at` (TIMESTAMPTZ): Creation timestamp
- `updated_at` (TIMESTAMPTZ): Last update timestamp

#### Metrics Table
- `id` (BIGSERIAL): Primary key
- `user_id` (UUID): Foreign key to users
- `source_name` (TEXT): Source of the metric
- `metric_date` (DATE): Date of the metric
- `metric_name` (TEXT): Name of the metric (e.g., "sessions", "conversions")
- `metric_value` (NUMERIC): Metric value
- `meta` (JSONB): Additional metadata
- `created_at` (TIMESTAMPTZ): Creation timestamp

### API Endpoints

#### Health Endpoints
1. **GET /v1/health/liveness**
   - Returns service liveness status
   - Response: `{"status": "ok"}`
   - No authentication required

2. **GET /v1/health/readiness**
   - Returns service readiness (checks all required secrets)
   - Response: `{"ready": true}` or `{"ready": false}`
   - No authentication required

#### Development Endpoints
3. **POST /v1/dev/seed-user**
   - Creates a user for testing/development
   - Query parameter: `email` (string)
   - Requires: Bearer token authentication
   - Response: `{"created": true}` or `{"created": false}`

#### Analytics Endpoints
4. **GET /v1/dashboard/tiles**
   - Returns aggregated metrics for dashboard display
   - Query parameter: `email` (string)
   - Requires: Bearer token authentication
   - Response:
     ```json
     {
       "sessions": 0.0,
       "conversions": 0.0,
       "ig_reach": 0.0,
       "engagement": 0.0
     }
     ```

5. **GET /docs** - Interactive API documentation
   - Automatically generated Swagger UI documentation
   - Allows testing endpoints directly from the browser

### Authentication
All protected endpoints require Bearer token authentication:
```
Authorization: Bearer <FASTAPI_SECRET_KEY>
```

### Environment Variables
The following secrets are required (stored in Replit Secrets):
- **DATABASE_URL**: Supabase connection pooler URI (port 6543, psycopg format)
  - Format: `postgresql+psycopg://postgres:<password>@<pooler-host>:6543/postgres?sslmode=require`
- **SUPABASE_PROJECT_URL**: Supabase project URL
- **SUPABASE_ANON_KEY**: Supabase anonymous key for client-side operations
- **FASTAPI_SECRET_KEY**: Secret key for API authentication
- **ALLOW_ORIGINS** (optional): Comma-separated CORS origins (defaults to *)
- **APP_NAME** (optional): API application name (defaults to "Living Lytics API")

### Configuration
- **Host:** 0.0.0.0 (accessible from Replit webview)
- **Port:** 5000 (Replit standard port, configurable via $PORT)
- **CORS:** Configurable via ALLOW_ORIGINS environment variable
- **Auto-reload:** Enabled for development
- **Database:** Connection pooling via Supabase pgBouncer (port 6543)
- **SSL Mode:** Required for all database connections

## Development Notes

### Running the Application
The application runs automatically via the configured workflow. To manually run:
```bash
uvicorn main:app --host 0.0.0.0 --port ${PORT:-5000} --reload
```

### Database Schema Setup
To ensure the database schema is created (idempotent):
```bash
python schema_sql.py
```

### Testing Endpoints
```bash
# Health check (no auth)
curl http://localhost:5000/v1/health/liveness
curl http://localhost:5000/v1/health/readiness

# Seed a user (requires auth)
curl -X POST -H "Authorization: Bearer <FASTAPI_SECRET_KEY>" \
  "http://localhost:5000/v1/dev/seed-user?email=demo@livinglytics.app"

# Get dashboard tiles (requires auth)
curl -H "Authorization: Bearer <FASTAPI_SECRET_KEY>" \
  "http://localhost:5000/v1/dashboard/tiles?email=demo@livinglytics.app"
```

### Installing Dependencies
Dependencies are managed via `requirements.txt`:
```bash
pip install -r requirements.txt
```

### Current Dependencies
- fastapi==0.115.0
- uvicorn[standard]==0.32.0
- pydantic==2.9.2
- sqlalchemy==2.*
- psycopg[binary]==3.*
- python-dotenv==1.*

## Future Enhancements
- OAuth integrations for data sources (Google Analytics, Instagram, etc.)
- Automated metric collection and storage
- Time-series analytics and reporting
- Advanced dashboard visualizations
- User organization management
- Rate limiting and advanced security features
- Webhook support for real-time data updates
- Scheduled jobs for data synchronization

## User Preferences
- Using Supabase for PostgreSQL database (not Replit DB)
- Connection pooler preferred over direct connections (port 6543 vs 5432)
- Bearer token authentication for API security
- Idempotent schema management approach
