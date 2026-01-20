# Vercel Deployment Guide

## Critical Changes Made for Vercel Compatibility

Your Flask app has been updated to work with Vercel's serverless environment:

### Files Created:
1. **`vercel.json`** - Vercel configuration
2. **`api/index.py`** - Serverless function entry point
3. **`.vercelignore`** - Files to exclude from deployment

### Files Modified:
1. **`config.py`** - Updated to use `/tmp` directory for Vercel
2. **`modules/database.py`** - Added error handling for DB failures
3. **`modules/cache_manager.py`** - Added error handling for cache failures

## Important Limitations on Vercel

### ⚠️ Database Won't Persist
- **SQLite database will reset on every deployment** 
- `/tmp` directory is cleared between function invocations
- **Solution**: Migrate to Vercel Postgres or another cloud database

### ⚠️ File Uploads Won't Persist
- Uploaded files are stored in `/tmp` and will be lost
- **Solution**: Use cloud storage like Vercel Blob or AWS S3

### ⚠️ Cache Won't Persist
- Cache is temporary and will be cleared
- This still works but won't persist between cold starts

## Deployment Steps

### 1. Set Environment Variables in Vercel
Go to your Vercel project settings and add:
```
OPENAI_API_KEY=your-openai-api-key
SECRET_KEY=your-secret-key
FLASK_ENV=production
```

### 2. Deploy
```bash
# Install Vercel CLI if you haven't
npm i -g vercel

# Deploy
vercel
```

Or push to GitHub and connect to Vercel dashboard.

## Recommended Next Steps

### Option 1: Use Vercel Postgres (Recommended)
1. Install Vercel Postgres in your project
2. Replace SQLite code with PostgreSQL
3. Benefits: Persistent storage, better for production

### Option 2: Use Vercel Blob for File Storage
1. Install `@vercel/blob` package
2. Update OCR upload handler to use Blob storage
3. Benefits: Persistent file storage

### Option 3: Deploy Elsewhere
If you need persistent SQLite:
- **Railway**: Supports persistent storage
- **Render**: Supports persistent disks
- **DigitalOcean App Platform**: Supports volumes
- **Traditional VPS**: Full control

## Testing the Deployment

After deploying, test these endpoints:
1. `/health` - Should return `{"status": "ok"}`
2. `/login` - Login page should load
3. `/analyze` - After login, test text analysis

## Current Behavior

✅ **What Works:**
- Text analysis (main feature)
- OCR processing
- PDF generation
- Login/authentication (session-based, resets on redeploy)

⚠️ **What Doesn't Persist:**
- Analysis history (resets on cold start)
- Student database (resets on cold start)
- Uploaded images (cleared after processing)
- Cache (cleared on cold start)

## Error Messages

If you see database errors in logs, that's expected on Vercel. The app will continue to work for analysis, but won't save history.

## Questions?

Feel free to ask about:
- Migrating to Vercel Postgres
- Setting up cloud file storage
- Alternative deployment options
