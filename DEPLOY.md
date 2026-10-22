# VibeQueue — Deployment Guide

Do NOT run these commands blindly. Read each section, fill in your values, then execute step by step.

---

## Prerequisites

- Node.js 20+
- Python 3.13+
- A running Redis instance (Railway add-on or Upstash)
- Supabase project (already created — ap-southeast-1 region)
- Razorpay account with test/live keys
- YouTube Data API v3 key (Google Cloud Console)
- Domain names: `vibequeue.in` (frontend) and `api.vibequeue.in` (backend)

---

## 1. Frontend — Deploy to Vercel

```bash
cd frontend
npx vercel login          # interactive — log in to your Vercel account
npx vercel --prod         # deploys to production
```

### Set environment variables in Vercel Dashboard

Go to Project Settings > Environment Variables and add:

| Variable | Value |
|----------|-------|
| `NEXT_PUBLIC_API_URL` | `https://api.vibequeue.in/api/v1` |
| `NEXT_PUBLIC_SUPABASE_URL` | `https://qnnxflnvmwvlrzflkdgh.supabase.co` |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | *(your anon key from Supabase Dashboard > API)* |

### Custom domain

In Vercel Dashboard > Domains, add `vibequeue.in` and `www.vibequeue.in`.
Point DNS to the values Vercel provides (typically a CNAME to `cname.vercel-dns.com`).

---

## 2. Backend — Deploy to Railway

Railway is recommended over Render because:
- Native Docker support (uses the existing `backend/Dockerfile` as-is)
- Multiple services from one repo (web + worker + beat)
- Redis add-on with zero config
- TCP connections supported (needed for Redis pub/sub)

### Install Railway CLI and login

```bash
npm install -g @railway/cli
railway login               # interactive — opens browser
```

### Create the project

```bash
cd backend
railway init                # creates a new Railway project
railway link                # links local dir to the project
```

### Deploy the API service

```bash
railway up                  # builds from Dockerfile, deploys
```

### Set environment variables

```bash
# Core
railway variables set APP_ENV=production
railway variables set APP_DEBUG=false
railway variables set SECRET_KEY="<generate with: python -c 'import secrets; print(secrets.token_urlsafe(48))'>"
railway variables set DATABASE_URL="<your Supabase pooler URL>"
railway variables set REDIS_URL="<Railway Redis URL — get from add-on>"
railway variables set JWT_SECRET_KEY="<same value as in your .env>"
railway variables set JWT_ALGORITHM=HS256

# CORS — update with your actual Vercel URL
railway variables set CORS_ORIGINS="https://vibequeue.in,https://www.vibequeue.in"

# Razorpay
railway variables set RAZORPAY_KEY_ID="<your live key>"
railway variables set RAZORPAY_KEY_SECRET="<your live secret>"
railway variables set RAZORPAY_WEBHOOK_SECRET="<from Razorpay webhook settings>"

# YouTube
railway variables set YOUTUBE_API_KEY="<your YouTube Data API key>"
```

### Add Redis

In the Railway Dashboard, click "New" > "Database" > "Redis". It auto-sets `REDIS_URL`.

### Add Celery Worker service

In Railway Dashboard, create a new service from the same repo:
- **Start command:** `celery -A app.workers.celery_app worker --loglevel=info --concurrency=2 -Q catalogue,payments,notifications,playback,analytics,cleanup`
- Same environment variables as the API service.

### Add Celery Beat service

Another service from the same repo:
- **Start command:** `celery -A app.workers.celery_app beat --loglevel=info`
- Same environment variables.

### Custom domain

In Railway Dashboard > Settings > Networking:
- Add custom domain `api.vibequeue.in`
- Point DNS A/CNAME record to Railway's provided value

---

## 3. Database Migration (run once after first deploy)

```bash
cd backend
# Ensure DATABASE_URL points to the cloud Supabase project
alembic upgrade head
```

---

## 4. Seed Data (run once after migration)

```bash
cd backend
python scripts/seed_db.py
python scripts/seed_catalogue.py
python scripts/validate_catalogue.py   # disables non-embeddable songs
```

---

## 5. Razorpay Webhook Configuration

1. Go to [Razorpay Dashboard](https://dashboard.razorpay.com) > Settings > Webhooks
2. Click "Add New Webhook"
3. **Webhook URL:** `https://api.vibequeue.in/api/v1/payments/verify`
4. **Secret:** Generate one and save it — set the same value as `RAZORPAY_WEBHOOK_SECRET` in your backend env
5. **Events to enable:** `payment.captured`
6. Save

### Razorpay Sandbox Test Procedure

Before going live, test with Razorpay test keys:

1. Start backend locally: `cd backend && uvicorn app.main:app --port 8000`
2. Start frontend: `cd frontend && npm run dev`
3. Open a table session via the dashboard
4. Join as guest, request a song, boost it
5. Navigate to billing, confirm charges
6. The `create-order` endpoint creates a Razorpay test order
7. Use test card `4111 1111 1111 1111` (any expiry, any CVV)
8. To receive the webhook locally, use [ngrok](https://ngrok.com):
   ```bash
   ngrok http 8000
   # Update the Razorpay webhook URL to the ngrok URL temporarily
   ```
9. Verify:
   - Payment status changes from "created" to "paid"
   - `razorpay_payment_id` is populated in the payments table
   - A duplicate webhook delivery returns `{"status": "already_processed"}`

---

## 6. CORS Update Checklist

After deploying frontend to Vercel:

1. Note the actual production URL (e.g., `https://vibequeue.in` or `https://vibequeue.vercel.app`)
2. Update `CORS_ORIGINS` in the backend environment:
   ```
   CORS_ORIGINS=https://vibequeue.in,https://www.vibequeue.in
   ```
3. Restart the backend service
4. Test: open the frontend in a browser, check the Network tab for CORS errors

---

## 7. Post-Deploy Verification Checklist

- [ ] Frontend loads at `https://vibequeue.in`
- [ ] API health check: `curl https://api.vibequeue.in/api/v1/health/`
- [ ] Staff login works (dashboard)
- [ ] Guest join works (table code)
- [ ] Song search returns results
- [ ] Song request adds to queue
- [ ] Boost updates queue order
- [ ] Ambient display shows live updates via Realtime
- [ ] Playback tab loads and connects
- [ ] Razorpay test payment completes
- [ ] "Add to Home Screen" works on mobile (PWA)
- [ ] No CORS errors in browser console
- [ ] No stack traces visible in API error responses

---

## What's NOT Covered

- WhatsApp notifications (no credentials yet)
- Cloudflare R2 storage (no credentials yet)
- YouTube IFrame playback testing (requires YouTube Premium in browser)
- NFC table tap (post-pilot feature)
- Multi-venue analytics dashboard (post-pilot)
