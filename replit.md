# Living Lytics API

## Overview
Backend API for Living Lytics – an analytics engine and data integration service built with FastAPI and connected to Supabase PostgreSQL.

**Project Type:** Backend API  
**Language:** Python 3.11  
**Framework:** FastAPI  
**Database:** Supabase PostgreSQL (via connection pooler)  
**Current State:** Fully connected to Supabase with authentication, health checks, and analytics endpoints

## Recent Changes
- **2025-10-22:** Row-Level Security (RLS) Implementation
  - Enabled RLS on all tables (users, data_sources, metrics) for Supabase security compliance
  - RLS with no policies = default deny all access via PostgREST API
  - FastAPI backend continues to work (service_role connection bypasses RLS)
  - Updated schema_sql.py to include RLS setup for future deployments
  - Verified backend functionality with RLS enabled (tested seed-user and dashboard endpoints)

- **2025-10-20:** GitHub API Integration Complete
  - Integrated Replit GitHub connector for automatic OAuth and token management
  - Installed PyGithub library for GitHub API interaction
  - Added GET /v1/github/user endpoint (authenticated user info)
  - Added GET /v1/github/repos endpoint (public repositories only, max 100)
  - Both GitHub endpoints secured with Bearer token authentication
  - Proper error handling for GitHub API failures and missing connections

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
- **PyGithub:** Python library for GitHub API v3
- **Replit GitHub Connector:** Automatic OAuth and token management

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

#### Root Endpoint
0. **GET /**
   - Friendly welcome message with API docs link
   - Response: `{"message": "Living Lytics API is running", "docs": "/docs"}`
   - No authentication required

#### Health Endpoints
1. **GET /v1/health/liveness**
   - Returns service liveness status
   - Response: `{"status": "ok"}`
   - No authentication required

2. **GET /v1/health/readiness**
   - Returns service readiness (checks all required secrets and database connection)
   - Response: `{"ready": true, "database": true, "environment": true}` or with false values
   - No authentication required

#### Development Endpoints
3. **POST /v1/dev/seed-user**
   - Creates a user for testing/development
   - Query parameter: `email` (string)
   - Requires: Bearer token authentication
   - Response: `{"created": true}` or `{"created": false}`

#### Analytics Endpoints
4. **POST /v1/metrics/ingest**
   - Ingest metrics data for a user
   - Requires: Bearer token authentication
   - Request body:
     ```json
     {
       "email": "user@example.com",
       "source_name": "meta",
       "metric_date": "2025-10-21",
       "data": {
         "reach": 1500,
         "engagement": 62
       }
     }
     ```
   - Response: `{"ingested": 2, "metrics": ["reach", "engagement"]}`
   - Notes: 
     - Accepts multiple metrics in the `data` object
     - Skips non-numeric values gracefully
     - Date format must be ISO 8601 (YYYY-MM-DD)

5. **GET /v1/dashboard/tiles**
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

#### GitHub Integration Endpoints
5. **GET /v1/github/user**
   - Returns authenticated GitHub user information
   - Requires: Bearer token authentication
   - Response:
     ```json
     {
       "username": "string",
       "name": "string",
       "email": "string",
       "bio": "string",
       "company": "string",
       "location": "string",
       "public_repos": 0,
       "followers": 0,
       "following": 0,
       "created_at": "2025-10-19T19:26:03+00:00",
       "avatar_url": "string",
       "html_url": "string"
     }
     ```

6. **GET /v1/github/repos**
   - Returns list of public GitHub repositories for authenticated user
   - Query parameter: `limit` (integer, default: 30, max: 100)
   - Requires: Bearer token authentication
   - Security: Only returns public repositories (private repos filtered out)
   - Response:
     ```json
     {
       "total_public_repos": 0,
       "returned_count": 2,
       "repositories": [
         {
           "name": "repo-name",
           "full_name": "user/repo-name",
           "description": "Repository description",
           "html_url": "https://github.com/user/repo-name",
           "clone_url": "https://github.com/user/repo-name.git",
           "private": false,
           "fork": false,
           "language": "Python",
           "stargazers_count": 0,
           "forks_count": 0,
           "open_issues_count": 0,
           "created_at": "2025-10-19T19:34:28+00:00",
           "updated_at": "2025-10-20T22:43:12+00:00",
           "pushed_at": "2025-10-20T22:43:07+00:00"
         }
       ]
     }
     ```

7. **GET /docs** - Interactive API documentation
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
- **ALLOW_ORIGINS** (optional): CORS origin configuration (defaults to `*`)
  - Default: `*` (allows all origins - suitable for development and testing)
  - **Important:** When set to `*`, cookies and other credentials aren't sent (but Authorization headers still work if explicitly set)
  - For Production with Base44: Set to any non-`*` value (e.g., `production`) to enable secure CORS
  - When enabled, automatically allows these specific domains only:
    - `https://app.base44.com` - Main Base44 platform
    - `https://*.base44.com` - All Base44 subdomains
    - `https://*.onrender.com` - Base44 app hosting (backend)
    - `https://*.replit.app` - Replit deployment URLs
    - `https://*.repl.co` - Replit development URLs
- **APP_NAME** (optional): API application name (defaults to "Living Lytics API")

### Configuration
- **Host:** 0.0.0.0 (accessible from Replit webview)
- **Port:** 5000 (Replit standard port, configurable via $PORT)
- **CORS:** Smart CORS configuration via ALLOW_ORIGINS environment variable
  - **Development Mode (default):** `ALLOW_ORIGINS=*` - Allows all origins for easy testing
    - Note: Credentials (Authorization headers) are disabled in this mode per CORS spec
  - **Production Mode:** Set `ALLOW_ORIGINS` to any non-`*` value to automatically enable Base44 domains
    - Credentials are enabled (Authorization headers work in browser)
  - **Automatic Base44 Support:** When production mode is enabled, the API automatically allows:
    - All Base44 platform domains (`app.base44.com`, `*.base44.com`)
    - Base44 app hosting infrastructure (`*.onrender.com`)
    - Replit deployment and development URLs
  - **Note:** Custom domains outside these patterns are NOT automatically allowed
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

# GitHub user info (requires auth)
curl -H "Authorization: Bearer <FASTAPI_SECRET_KEY>" \
  "http://localhost:5000/v1/github/user"

# GitHub repositories (requires auth, public repos only)
curl -H "Authorization: Bearer <FASTAPI_SECRET_KEY>" \
  "http://localhost:5000/v1/github/repos?limit=10"
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
- PyGithub==2.*
- requests==2.*

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
- GitHub integration via Replit connector for automatic OAuth management
- Public-only data exposure for GitHub endpoints (private repos filtered)
