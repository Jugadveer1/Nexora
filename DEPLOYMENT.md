# Nexora - Vercel Deployment Guide

## Prerequisites

- Node.js and npm installed
- Git repository set up
- Vercel account
- Python dependencies installed locally

## Step 1: Install Required Packages

```bash
pip install django-cors-headers whitenoise gunicorn
```

## Step 2: Install Vercel CLI

```bash
npm install -g vercel
```

## Step 3: Login to Vercel

```bash
vercel login
```

## Step 4: Initialize Git Repository (if not done)

```bash
git init
git add .
git commit -m "Initial commit for Vercel deployment"
```

## Step 5: Deploy to Vercel

```bash
vercel --prod
```

## Step 6: Set Environment Variables in Vercel Dashboard

1. Go to your Vercel dashboard
2. Select your project
3. Go to Settings > Environment Variables
4. Add these variables:
   - `DEBUG` = `False`
   - `SECRET_KEY` = `your-secret-key-here`
   - `GROQ_API_KEY` = `your-groq-api-key-here`

## Step 7: Update CORS Settings

After deployment, update `app/settings.py`:

```python
CORS_ALLOWED_ORIGINS = [
    "https://your-actual-vercel-url.vercel.app",
]
```

## Important Notes

- SQLite database will reset on each deployment (use PostgreSQL for production)
- Static files are handled by WhiteNoise
- Environment variables are loaded from Vercel's environment settings

## Troubleshooting

- If deployment fails, check the build logs in Vercel dashboard
- Ensure all dependencies are in requirements.txt
- Check that static files are collected properly

## Production Considerations

1. Use PostgreSQL database instead of SQLite
2. Set up proper domain and SSL
3. Configure proper CORS origins
4. Set DEBUG=False in production
5. Use a secure SECRET_KEY
