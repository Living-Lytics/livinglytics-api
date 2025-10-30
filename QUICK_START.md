# Quick Start: Dual-Domain Deployment

## Overview
You're setting up Living Lytics with two separate Replit projects:
- **This Project** → Backend API → api.livinglytics.com
- **New Project** → Frontend → livinglytics.com

## Your Action Items

### ✅ Already Done (In This Project)
- Backend-only configuration complete
- Frontend workflow removed
- Deployment config set for backend API
- Documentation created

### 📋 What You Need to Do

#### 1. Create New Frontend Project
- Go to Replit → Create new Repl
- Choose "Vite" or "Node.js" template
- Name it: `living-lytics-frontend`

#### 2. Copy Frontend Files
Follow **FRONTEND_SETUP_GUIDE.md** to:
- Copy the `living-lytics-marketing` folder to new project
- Install dependencies
- Remove Vite proxy from config
- Verify environment variables

#### 3. Deploy Backend (This Project)
- Click "Deploy" button
- Link domain: `api.livinglytics.com`
- Add environment variables from `.env.production.example`
- Copy DNS records

#### 4. Deploy Frontend (New Project)
- Click "Deploy" button in new project
- Link domain: `livinglytics.com`
- Copy DNS records

#### 5. Configure DNS
At your domain registrar:
- Add A and TXT records for `api.livinglytics.com`
- Add A and TXT records for `livinglytics.com`
- Wait for propagation

#### 6. Update OAuth Providers
**Google Cloud Console:**
- Add: `https://api.livinglytics.com/v1/auth/google/callback`

**Meta for Developers:**
- Add: `https://api.livinglytics.com/v1/connections/instagram/callback`

#### 7. Test Everything
- Visit `https://livinglytics.com`
- Test registration, login
- Test Google OAuth
- Test Instagram OAuth

## 📖 Detailed Guides

- **Frontend Setup**: See `FRONTEND_SETUP_GUIDE.md`
- **Full Deployment**: See `DEPLOYMENT_GUIDE.md`
- **Environment Variables**: See `.env.production.example`

## 🎯 Current Status

**Backend (This Project):**
- ✅ Configured for backend-only
- ✅ Deployment config ready
- ⏳ Waiting for deployment

**Frontend (New Project):**
- ⏳ Needs to be created
- ⏳ Files need to be copied
- ⏳ Needs deployment

## Need Help?

Refer to the detailed guides above or ask if you get stuck at any step!
