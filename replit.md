# Living Lytics API

## Overview
Backend API for Living Lytics – an analytics engine and data integration service built with FastAPI.

**Project Type:** Backend API  
**Language:** Python 3.11  
**Framework:** FastAPI  
**Current State:** Initialized with basic API structure and running successfully

## Recent Changes
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
- **Pydantic:** Data validation using Python type annotations

### Project Structure
```
.
├── main.py              # Main API application with endpoints
├── requirements.txt     # Python dependencies
├── README.md           # Project description
└── replit.md           # This documentation file
```

### API Endpoints
The API currently provides the following endpoints:

1. **GET /** - Root endpoint
   - Returns welcome message and API status
   - Response: `{"message": "Welcome to Living Lytics API", "status": "active", "version": "1.0.0"}`

2. **GET /health** - Health check endpoint
   - Returns API health status
   - Response: `{"status": "healthy"}`

3. **GET /api/analytics** - Analytics endpoint
   - Returns analytics data (currently returns empty array)
   - Response: `{"data": [], "message": "Analytics endpoint ready"}`

4. **GET /docs** - Interactive API documentation
   - Automatically generated Swagger UI documentation
   - Allows testing endpoints directly from the browser

### Configuration
- **Host:** 0.0.0.0 (accessible from Replit webview)
- **Port:** 5000 (Replit standard port)
- **CORS:** Enabled for all origins (development configuration)
- **Auto-reload:** Enabled for development

## Development Notes

### Running the Application
The application runs automatically via the configured workflow. To manually run:
```bash
uvicorn main:app --host 0.0.0.0 --port 5000 --reload
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

## Future Enhancements
This is a foundational setup. Potential areas for expansion:
- Database integration for analytics data storage
- Authentication and authorization
- Additional analytics endpoints
- Data integration connectors
- Logging and monitoring
- Rate limiting and security features

## User Preferences
No specific user preferences recorded yet.
