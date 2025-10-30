# Frontend Setup Guide - New Replit Project

This guide will help you set up the Living Lytics frontend in a new Replit project for separate deployment.

## Step 1: Create New Replit Project

1. Go to [Replit](https://replit.com) and click **"+ Create Repl"**
2. Choose template: **"Vite"** or **"Node.js"**
3. Name it: `living-lytics-frontend` (or your preferred name)
4. Click **"Create Repl"**

## Step 2: Copy Frontend Files

Copy the entire `living-lytics-marketing` folder from your backend project to the new frontend project. You'll need these files/folders:

### Required Files & Folders:
```
living-lytics-marketing/
├── src/                    # All React components and pages
├── public/                 # Static assets
├── index.html             # Entry HTML file
├── package.json           # Dependencies
├── package-lock.json      # Lock file
├── vite.config.js         # Vite configuration
├── tailwind.config.js     # Tailwind CSS config
├── postcss.config.js      # PostCSS config
├── .env.production        # Production environment variables
└── eslint.config.js       # ESLint configuration (optional)
```

### How to Copy:
**Option A: Download & Upload**
1. In your backend project, download the `living-lytics-marketing` folder as a ZIP
2. In your new frontend project, upload and extract it
3. Move all contents from `living-lytics-marketing/` to the root of your new project

**Option B: Manual Copy-Paste** (for key files)
1. Create the folder structure in your new project
2. Copy-paste each file's contents manually through the Replit editor

## Step 3: Install Dependencies

In your new frontend project's Shell, run:

```bash
npm install
```

This will install all dependencies from `package.json`.

## Step 4: Update Vite Configuration

**IMPORTANT**: Remove the Vite proxy configuration since the frontend will call the API directly in production.

Edit `vite.config.js` and **remove** the `proxy` section:

```javascript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  base: '/',
  server: {
    host: '0.0.0.0',
    port: 5000,
    allowedHosts: true,
    // REMOVE the proxy section - not needed in production
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
    extensions: ['.mjs', '.js', '.jsx', '.ts', '.tsx', '.json']
  },
  optimizeDeps: {
    esbuildOptions: {
      loader: {
        '.js': 'jsx',
      },
    },
  },
})
```

## Step 5: Verify Environment Variables

Make sure `.env.production` exists with:

```env
VITE_API_BASE=https://api.livinglytics.com
VITE_API_HEALTH=/v1/health/liveness
VITE_API_LOGIN=/v1/auth/login
VITE_API_REGISTER=/v1/auth/register
VITE_API_AUTH_STATUS=/v1/auth/status
VITE_API_GOOGLE_START=/v1/auth/google/start
VITE_API_INSTAGRAM_START=/v1/auth/instagram/start
```

For **local development** (optional), create `.env.local`:

```env
VITE_API_BASE=https://api.livinglytics.com
```

Or point to your backend dev URL if testing locally.

## Step 6: Configure Package.json Scripts

Make sure your `package.json` has these scripts:

```json
{
  "scripts": {
    "dev": "vite --host 0.0.0.0 --port 5000",
    "build": "vite build",
    "preview": "vite preview --host 0.0.0.0 --port 5000",
    "lint": "eslint ."
  }
}
```

## Step 7: Test Locally

Run the dev server to verify everything works:

```bash
npm run dev
```

Visit the URL Replit provides - you should see your marketing site.

## Step 8: Configure Replit Deployment

### Set up the Run Configuration:

Click **"Configure the run button"** or edit `.replit` file:

```toml
run = "npm run dev"

[deployment]
build = ["npm", "install"]
run = ["npm", "run", "preview"]
deploymentTarget = "autoscale"
```

### What This Does:
- **Development**: `npm run dev` runs Vite dev server
- **Production**: `npm run preview` serves the built production files

## Step 9: Deploy to livinglytics.com

1. Click **"Deploy"** button
2. Select **"Autoscale"** deployment type
3. Wait for build to complete
4. Go to **Deployments** → **Settings**
5. Click **"Link a domain"**
6. Enter: `livinglytics.com`
7. Copy the DNS records Replit provides (A and TXT records)

## Step 10: Configure DNS

At your domain registrar, add the DNS records from Step 9:

```
Type: A
Host: @ (or blank/root)
Value: <IP from Replit>
TTL: Automatic

Type: TXT  
Host: @ (or blank/root)
Value: <verification code from Replit>
TTL: Automatic
```

Wait for DNS propagation (5 minutes to 48 hours).

## Step 11: Verify It Works

Once DNS propagates:

1. Visit `https://livinglytics.com`
2. You should see your marketing site
3. Test navigation between pages
4. Try the "Get Started" button (should work once backend is deployed)

## Troubleshooting

### Build Fails
- Check that all dependencies installed: `npm install`
- Verify `package.json` has correct build script
- Check for TypeScript errors (if using TS)

### Can't Connect to API
- Verify `.env.production` has correct `VITE_API_BASE`
- Make sure backend is deployed at `api.livinglytics.com`
- Check browser console for CORS errors

### Vite Preview Not Working
- Make sure you ran `npm run build` first (or deployment does this automatically)
- Check port configuration in `vite.config.js`

### DNS Not Resolving
- Wait longer (DNS can take up to 48 hours)
- Use `dig livinglytics.com` to check DNS status
- Verify DNS records match exactly what Replit provided

## Next Steps

After frontend is deployed:
1. Deploy backend to `api.livinglytics.com` (see backend project)
2. Update OAuth redirect URIs in Google Cloud Console and Meta
3. Test full OAuth flows end-to-end

## File Checklist

Before deploying, make sure you have:
- ✅ All `src/` files copied
- ✅ `package.json` with dependencies
- ✅ `vite.config.js` (with proxy removed)
- ✅ `.env.production` with API URL
- ✅ `tailwind.config.js` for styling
- ✅ `index.html` entry point
- ✅ Build script working locally

---

**Questions?** See the main `DEPLOYMENT_GUIDE.md` in the backend project for the full deployment process.
