# Living Lytics Frontend

A React + Vite + TypeScript dashboard for visualizing analytics data from Google Analytics 4 and Instagram Business accounts.

## Features

- **Dashboard**: KPI tiles and timeline visualizations for GA4 and Instagram metrics
- **Connections Management**: OAuth integration for connecting Google Analytics and Instagram Business accounts  
- **Settings**: User preferences and account management
- **OAuth Callbacks**: Automatic handling of Google and Instagram OAuth flows
- **Real-time Updates**: Zustand state management with automatic connection status refresh
- **Responsive Design**: TailwindCSS styling with mobile-first approach

## Tech Stack

- **React 19** with TypeScript
- **Vite 7** for fast development and building
- **React Router 7** for client-side routing
- **Zustand** for state management
- **Axios** for API communication
- **TailwindCSS v4** for styling
- **Recharts** for data visualization

## ⚠️ Authentication & Security

**CRITICAL**: The backend API currently requires bearer token authentication for most endpoints. The frontend has been designed to **NOT** bundle the backend's shared secret for security reasons.

### Current Limitations

1. **No User Authentication**: The frontend currently cannot make authenticated API calls to protected endpoints
2. **Public Endpoints Only**: Only public endpoints (`/health`, `/ready`, `/v1/debug/*`) are accessible
3. **OAuth Flows**: OAuth initiation and callbacks work through direct redirects (not API calls)

### Required Backend Changes

To make the frontend fully functional, you must implement one of these solutions on the backend:

**Option 1: Make API Endpoints Public** (Simplest)
- Remove bearer token authentication from user-facing endpoints
- Keep admin endpoints protected with ADMIN_TOKEN
- Implement rate limiting and request validation

**Option 2: Implement User Authentication** (Recommended)
- Add user login/registration system
- Issue per-user JWT tokens that can be safely stored in browser
- Use short-lived tokens with refresh token mechanism
- Store tokens in HTTP-only cookies or secure sessionStorage

**Option 3: Session-Based Auth**
- Implement server-side sessions
- Use cookies for session management
- CSRF protection required

### What's Been Removed for Security

- ❌ `VITE_API_KEY` environment variable (prevented bundling backend secret)
- ❌ `Authorization: Bearer` headers in API client (prevented credential exposure)

### Development Workaround

For local development testing, you can temporarily:
1. Disable authentication on specific endpoints in the backend
2. Use the public debug endpoints for connection status
3. Test OAuth flows which work without frontend authentication

## Development Setup

### Prerequisites

- Node.js 20+
- Backend API running on `localhost:8000`

### Installation

```bash
cd client
npm install
```

### Environment Configuration

Copy `.env.example` to `.env` and configure:

```env
# Backend API (proxied through Vite during development)
VITE_API_BASE=

# OAuth Endpoints (point to backend)
VITE_OAUTH_IG_INIT=http://localhost:8000/v1/connections/instagram/init
VITE_OAUTH_GA_INIT=http://localhost:8000/v1/connections/google/init

# Frontend URL (for OAuth callbacks)
VITE_REDIRECT_BASE=http://localhost:5000
```

### Running Development Server

```bash
npm run dev
```

The app will be available at `http://localhost:5000`.

**Note**: The Vite dev server proxies API requests to the backend:
- `/v1/*` → `http://localhost:8000/v1/*`
- `/health` → `http://localhost:8000/health`
- `/ready` → `http://localhost:8000/ready`

## Project Structure

```
client/
├── src/
│   ├── components/       # Reusable UI components
│   │   ├── Page.tsx     # Page layout wrapper
│   │   └── Toast.tsx    # Toast notification system
│   ├── routes/          # Page components
│   │   ├── Dashboard.tsx          # Main dashboard view
│   │   ├── Connections.tsx        # Connection management
│   │   ├── Settings.tsx           # User settings
│   │   ├── CallbackGoogle.tsx     # Google OAuth callback
│   │   └── CallbackInstagram.tsx  # Instagram OAuth callback
│   ├── lib/             # Utilities and services
│   │   ├── api.ts       # API client (axios)
│   │   └── useStore.ts  # Zustand state store
│   ├── styles/          # Global styles
│   │   └── index.css    # Tailwind directives + custom CSS
│   ├── App.tsx          # Root component with routing
│   └── main.tsx         # Application entry point
├── vite.config.ts       # Vite configuration
├── tailwind.config.js   # Tailwind configuration
└── postcss.config.js    # PostCSS configuration
```

## Building for Production

```bash
npm run build
```

This creates an optimized production build in the `dist/` directory.

## Deployment to Base44

### Prerequisites

1. Base44 account configured
2. Living Lytics API deployed at `https://api.livinglytics.com`
3. OAuth redirect URIs configured in Google Cloud Console and Meta App

### Deployment Steps

1. **Update Environment Variables** for production (create `.env.production`):

```env
VITE_API_BASE=
VITE_OAUTH_IG_INIT=https://api.livinglytics.com/v1/connections/instagram/init
VITE_OAUTH_GA_INIT=https://api.livinglytics.com/v1/connections/google/init
VITE_REDIRECT_BASE=https://livinglytics.com
```

2. **Build the Application**:

```bash
npm run build
```

3. **Deploy to Base44**:
   - Upload the `dist/` folder contents to Base44
   - Configure the domain: `livinglytics.com`
   - Configure all routes to serve `index.html` for client-side routing

4. **Update OAuth Redirect URIs**:
   - **Google Cloud Console**: Add `https://livinglytics.com/oauth/callback/google`
   - **Meta for Developers**: Add `https://livinglytics.com/oauth/callback/instagram`

5. **Verify Backend CORS**:

Ensure the backend API includes `livinglytics.com` in allowed origins (already configured in `main.py`).

## API Integration

### Key Endpoints

- `GET /v1/connections/status` - Get current connection status
- `GET /v1/connections/google/init?email=user@example.com` - Initiate Google OAuth
- `GET /v1/connections/instagram/init?email=user@example.com` - Initiate Instagram OAuth
- `GET /v1/dashboard/tiles?range=last_7d` - Get KPI tiles
- `GET /v1/timeline?metrics=ga_sessions,ig_reach&grain=daily&range=last_30d` - Get timeline data
- `POST /v1/disconnect/{provider}` - Disconnect specific provider
- `POST /v1/disconnect/all` - Disconnect all accounts

## Troubleshooting

### Blank Page in Replit Preview

The Replit screenshot/webview may show a blank page due to caching. The app is functional when accessed via:
- Direct Replit preview URL: `https://<slug>.<user>.repl.co`
- Local development: `http://localhost:5000`
- Production deployment on Base44

### OAuth Redirect Errors

Ensure redirect URIs match exactly in Google Cloud Console, Meta for Developers, and environment variables.

### API Connection Issues

If the frontend can't connect to the backend:
1. Verify backend is running on port 8000
2. Check Vite proxy configuration in `vite.config.ts`
3. Ensure CORS is configured correctly on the backend
4. **Implement proper authentication** - See "Authentication & Security" section above

## License

MIT
