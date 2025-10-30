# Frontend Deployment Checklist

## Why You're Seeing a White Screen

The white screen usually means one of these issues:

1. **Build failed** - Check the deployment logs
2. **API can't be reached** - Backend not deployed yet or wrong URL
3. **JavaScript errors** - Check browser console (F12)
4. **Wrong environment variables** - .env.production not being used

## Step-by-Step Fix

### 1. Check Your File Structure

Your frontend project should have these files **in the root** (not inside a subfolder):

```
your-frontend-project/
├── src/
├── public/
├── index.html
├── package.json
├── vite.config.js
├── tailwind.config.js
├── postcss.config.js
├── .env.production
├── .gitignore
└── node_modules/
```

**IMPORTANT**: If you have a `living-lytics-marketing` folder, move everything OUT of it to the root!

### 2. Remove Proxy from vite.config.js

Edit `vite.config.js` and **remove** the proxy section (lines 13-23):

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
    // REMOVE proxy section - not needed in production!
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

### 3. Verify .env.production

Make sure you have `.env.production` in the root with:

```env
VITE_API_BASE=https://api.livinglytics.com
VITE_API_HEALTH=/v1/health/liveness
VITE_API_LOGIN=/v1/auth/login
VITE_API_REGISTER=/v1/auth/register
VITE_API_AUTH_STATUS=/v1/auth/status
VITE_API_GOOGLE_START=/v1/auth/google/start
VITE_API_INSTAGRAM_START=/v1/auth/instagram/start
```

### 4. Update Package.json Scripts

Make sure your `package.json` has:

```json
{
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview --host 0.0.0.0 --port 5000"
  }
}
```

### 5. Test Locally First

Before deploying, test locally:

```bash
# Install dependencies
npm install

# Build for production
npm run build

# Test the production build
npm run preview
```

Visit the URL Replit shows. If you see the site, it's ready to deploy!

### 6. Configure .replit for Deployment

Create or edit `.replit` file:

```toml
run = "npm run dev"

[deployment]
build = ["npm", "install", "&&", "npm", "run", "build"]
run = ["npm", "run", "preview"]
deploymentTarget = "autoscale"
```

Or use this simpler version:

```toml
run = "npm run dev"

[deployment]
deploymentTarget = "autoscale"
```

### 7. Deploy

1. Click the **Deploy** button
2. Wait for the build to complete
3. Check the **Deployment logs** for errors

### 8. Check Browser Console

Once deployed:

1. Visit your deployed URL
2. Press **F12** to open Developer Tools
3. Go to the **Console** tab
4. Look for errors (red text)

Common errors and fixes:

**"Failed to fetch" or "Network error"**
- Backend isn't deployed yet
- Wrong API URL in .env.production
- CORS not configured (backend issue)

**"Cannot read property of undefined"**
- JavaScript error in your code
- Usually shows the file and line number

**Nothing in console, just white screen**
- Build might have failed
- Check deployment logs in Replit

### 9. Verify Environment Variables Were Used

In the browser console, type:

```javascript
console.log(import.meta.env.VITE_API_BASE)
```

It should show: `https://api.livinglytics.com`

If it shows `undefined` or a localhost URL:
- `.env.production` wasn't used during build
- Rebuild: `npm run build` and redeploy

### 10. Test Backend Connection

In browser console:

```javascript
fetch('https://api.livinglytics.com/v1/health/liveness')
  .then(r => r.json())
  .then(console.log)
```

Should show: `{ status: "ok", ... }`

If you get CORS error or network error:
- Backend not deployed yet
- Backend CORS not allowing your frontend domain

---

## Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| White screen, no errors | Check build logs, verify files are in root |
| "Failed to fetch" errors | Deploy backend first, check API URL |
| CORS errors | Add frontend domain to backend CORS config |
| Old API URL showing | Rebuild with `npm run build`, clear browser cache |
| Site works locally but not deployed | Check .replit deployment config |

---

## Still Not Working?

1. **Check build output size**: Should be several MB with all your React components
2. **Verify index.html exists**: In both root and dist/ folder after build
3. **Check for missing dependencies**: Run `npm install` again
4. **Try a fresh deployment**: Delete deployment and redeploy

---

## Backend Not Deployed Yet?

If your backend isn't deployed to `api.livinglytics.com` yet:

1. The frontend will load but **won't work** (can't connect to API)
2. You'll see network errors in browser console
3. **Deploy backend first**, then redeploy frontend

**Backend deployment guide**: See `PRODUCTION_SECRETS.md` in the backend project
