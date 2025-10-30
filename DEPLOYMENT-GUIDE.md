# 🚀 Python Backend Deployment Guide

## 📋 Prerequisites
- GitHub account
- Render account (free tier available)
- Supabase project with Service Role Key

## 🔧 Step 1: Prepare Files

Ensure your `python-backend` folder contains:
```
python-backend/
├── main.py
├── requirements.txt
├── .env (for local testing)
└── DEPLOYMENT-GUIDE.md
```

## 📤 Step 2: Push to GitHub

1. **Initialize Git:**
```bash
cd python-backend
git init
git add .
git commit -m "Initial Python backend"
```

2. **Create GitHub repo** and push:
```bash
git remote add origin https://github.com/yourusername/church-app-backend.git
git push -u origin main
```

## 🌐 Step 3: Deploy to Render

### 3.1 Create Web Service
1. Go to [render.com](https://render.com)
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub account
4. Select your repository

### 3.2 Configure Service
**Basic Settings:**
- **Name:** `church-app-backend`
- **Region:** Choose closest to your users
- **Branch:** `main`
- **Root Directory:** `python-backend` (if backend is in subfolder)

**Build & Deploy:**
- **Runtime:** `Python 3`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `python main.py`

### 3.3 Environment Variables
Click **"Advanced"** and add:
```
SUPABASE_URL = https://your-project.supabase.co
SUPABASE_SERVICE_KEY = your-service-role-key-here
```

**⚠️ Get Service Role Key:**
1. Go to Supabase Dashboard
2. Settings → API
3. Copy **"service_role"** key (NOT anon key)

### 3.4 Deploy
1. Click **"Create Web Service"**
2. Wait for deployment (5-10 minutes)
3. Your API will be available at: `https://your-app-name.onrender.com`

## 🔗 Step 4: Connect to React Native

Update your React Native `.env`:
```env
EXPO_PUBLIC_PYTHON_EXTRACTION_API=https://your-app-name.onrender.com/extract-text
```

## ✅ Step 5: Test Deployment

**Test API endpoint:**
```bash
curl -X POST https://your-app-name.onrender.com/extract-text \
  -H "Content-Type: application/json" \
  -d '{"file_url": "https://example.com/test.pdf"}'
```

**Check health:**
```bash
curl https://your-app-name.onrender.com/health
```

## 🐛 Troubleshooting

**Build Fails:**
- Check `requirements.txt` syntax
- Ensure Python 3.8+ compatibility

**API Errors:**
- Verify Supabase environment variables
- Check Render logs in dashboard

**File Extraction Fails:**
- Ensure file URLs are publicly accessible
- Check supported formats: PDF, DOCX, DOC, TXT

## 📊 Monitoring

**Render Dashboard:**
- View logs in real-time
- Monitor resource usage
- Check deployment status

**Free Tier Limits:**
- 750 hours/month
- Sleeps after 15 minutes of inactivity
- First request after sleep takes ~30 seconds

## 🔄 Updates

**To update your backend:**
1. Push changes to GitHub
2. Render auto-deploys from `main` branch
3. Check deployment logs for success

## 💡 Production Tips

**For production use:**
- Upgrade to paid Render plan
- Add custom domain
- Enable auto-scaling
- Set up monitoring alerts