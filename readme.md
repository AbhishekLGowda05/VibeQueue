# VibeQueue

**Real-time competitive song queue for bars and restaurants.**

Guests scan a QR code, request songs, and pay to boost them up the queue. The venue keeps full control — approved catalogue, spend caps, a pause button. Revenue splits 60/40 (venue/VibeQueue).

Built for a two-venue Bengaluru pilot (Koramangala Social, Indiranagar Hammered).

---

## How It Works

1. Staff opens a table on the dashboard, gets a 6-digit code
2. Guest scans the QR on the table tent, enters the code on their phone
3. Guest searches the venue's approved catalogue and requests a song
4. Song enters the live queue (max 8 active, rest in waiting pool)
5. Guest can boost (₹15 / ₹25 / ₹35) to move their song up — visible to the whole room
6. YouTube IFrame on the venue laptop auto-plays the next song
7. When the song ends (`ENDED` event), the boost charge is confirmed
8. At bill time, guest reviews charges — only played songs are billed

No app download. No venue Wi-Fi required for guests. Music plays through the venue's existing speakers via their own YouTube Premium account.

---

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  Guest Phone     │     │  Venue Laptop    │     │  Ambient TV      │
│  (Mobile Data)   │     │  (Venue Wi-Fi)   │     │  (Venue Wi-Fi)   │
│                  │     │                  │     │                  │
│  /join/[venue]   │     │  Tab 1: /dashboard│    │  /display/[venue]│
│                  │     │  Tab 2: /playback │     │                  │
└────────┬─────────┘     └────────┬─────────┘     └────────┬─────────┘
         │                        │                         │
         │         HTTPS + WebSocket (Supabase Realtime)    │
         │                        │                         │
    ┌────▼────────────────────────▼─────────────────────────▼────┐
    │                    FastAPI Backend                          │
    │    REST API · JWT Auth · Queue Engine · Billing · Payments  │
    ├────────────────────────────────────────────────────────────-┤
    │  PostgreSQL (Supabase)  │  Redis  │  Celery Workers + Beat │
    └────────────────────────────────────────────────────────────-┘
```

**Stack:**
- **Backend:** FastAPI + SQLAlchemy (async) + Celery + Redis
- **Frontend:** Next.js 16 (App Router) + TypeScript + Tailwind CSS + Zustand + Framer Motion
- **Database:** Supabase PostgreSQL (ap-southeast-1) via session-mode pooler
- **Real-time:** Supabase Realtime (WebSocket subscriptions on 5 tables)
- **Payments:** Razorpay (integrated, sandbox-tested procedure documented)
- **Playback:** YouTube IFrame Player API via dedicated browser tab

---

## Four Interfaces

| Interface | Route | Device | Purpose |
|---|---|---|---|
| Guest | `/join/[venue]` | Customer phone | Request songs, boost, review bill |
| Dashboard | `/dashboard` | Venue laptop (Tab 1) | Staff control — queue, tables, stats, mode toggle |
| Playback | `/playback/[venue]` | Venue laptop (Tab 2) | Automated YouTube player, WebSocket-driven |
| Ambient Display | `/display/[venue]` | Venue TV | Now playing, next up, QR CTA — dark theme, large text |

---

## Project Status (as of 2026-08-24)

### Verified Against Cloud Supabase
- 11 database tables (Alembic migrations applied)
- Row-Level Security on all 10 data tables (anon: SELECT-only on 5 Realtime tables, zero access elsewhere)
- Supabase Realtime enabled on `queue_entries`, `table_sessions`, `boosts`, `playback_commands`, `playback_events`
- Seed data: 2 venues, 2 owners, 62 songs (16 embeddable after YouTube validation)
- Backend health check: database + Redis both OK
- Full smoke test: staff login → open table → guest join → search → request → boost → queue reorder

### Verified Locally
- pytest: 42 passed, 0 failed
- Frontend build: zero TypeScript errors, all routes generating
- Celery worker + beat start and connect to Redis

### Security Hardening Applied
- **Spend cap race condition fixed:** Atomic Redis Lua script replaces non-atomic GET/check/INCRBY (prevents double-charging)
- **Webhook idempotency:** Application guard + unique partial DB index on `razorpay_payment_id` (prevents duplicate payment processing)
- **JWT startup guard:** Refuses production boot with dev placeholder secret
- **Rate limiting on `/sessions/join`:** 5 req/min/IP (brute-forcing 6-digit codes now impractical)
- **Error boundaries:** Next.js 16 error.tsx on all 4 routes + global-error.tsx (ambient/playback auto-retry)
- **RLS architecture:** Frontend anon key gets read-only Realtime; all writes go through backend (postgres user, bypasses RLS); `service_role` key never referenced in any frontend file

### Written (Not Yet Tested End-to-End)
- Frontend ↔ backend integration in the browser
- WebSocket real-time sync across all 4 interfaces
- Razorpay payment flow (keys configured, sandbox test procedure documented in DEPLOY.md)
- YouTube IFrame playback (requires YouTube Premium in browser — manual venue setup step)
- Framer Motion animations (queue reorder, boost sheet slide, ambient crossfade)
- PWA manifest + icons (icon-192.png, icon-512.png)

---

## What Blocks Pilot Launch

| Blocker | Type | Action Required |
|---|---|---|
| YouTube catalogue only 16/62 songs valid | Data | Refresh seed catalogue with working video IDs |
| Frontend ↔ backend never tested in browser | Integration | Run all 4 interfaces against cloud backend |
| Razorpay sandbox payment not tested | Integration | Follow procedure in DEPLOY.md §5 (needs ngrok) |
| YouTube IFrame playback not tested | Manual | Open playback tab with YouTube Premium, verify autoplay |
| Not deployed | Infra | `vercel login` + `vercel --prod` (frontend), Railway (backend) — see DEPLOY.md |
| CORS_ORIGINS needs real Vercel URL | Config | Update backend env after deployment |

---

## Local Development

### Prerequisites

- Python 3.13+, Node.js 20+
- Redis running locally (`brew services start redis`)
- Supabase project (remote — no local Postgres needed)
- `backend/.env` filled with real credentials

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Terminal 1 — API
uvicorn app.main:app --reload --port 8000

# Terminal 2 — Celery worker
celery -A app.workers.celery_app worker --loglevel=info \
  -Q catalogue,payments,notifications,playback,analytics,cleanup

# Terminal 3 — Celery beat
celery -A app.workers.celery_app beat --loglevel=info
```

### Frontend

```bash
cd frontend
npm install
npm run dev    # http://localhost:3000
```

### Tests

```bash
cd backend && source .venv/bin/activate
pytest tests/ -v --tb=short           # 42 passed, 0 failed
curl http://localhost:8000/api/v1/health/
python scripts/smoke_test.py          # full core loop
```

### Database

```bash
cd backend
alembic upgrade head                  # apply migrations
python scripts/seed_db.py             # venues + owners
python scripts/seed_catalogue.py      # 62 songs
python scripts/validate_catalogue.py  # disable non-embeddable songs
```

---

## Database Schema (11 tables)

| Table | Purpose | RLS | Realtime |
|---|---|---|---|
| `venues` | Venue config (name, slug, spend cap, mode) | Enabled (no anon access) | No |
| `users` | Venue owners/staff (hashed passwords) | Enabled (no anon access) | No |
| `songs` | Song catalogue (title, artist, youtube_video_id, genre) | Enabled (no anon access) | No |
| `table_sessions` | Active table sessions (code, venue, expiry) | Enabled (anon SELECT) | Yes |
| `queue_entries` | Song queue (song, table, score, status) | Enabled (anon SELECT) | Yes |
| `boosts` | Boost transactions (amount, tier, status) | Enabled (anon SELECT) | Yes |
| `payments` | Razorpay payment records | Enabled (no anon access) | No |
| `playback_commands` | Play/pause/skip instructions | Enabled (anon SELECT) | Yes |
| `playback_events` | PLAYING/ENDED/ERROR events from IFrame | Enabled (anon SELECT) | Yes |
| `audit_logs` | System audit trail | Enabled (no anon access) | No |

---

## Queue Scoring

```
score = sum_of_boosts_paise + (1000 / minutes_since_request)
```

- Boosts dominate: ₹15 (1500 paise) beats any time-decay score
- Time-decay prevents starvation: unboosted songs eventually reach top
- Tie-breaker: oldest `requested_at` timestamp wins
- Active queue: positions 1–8 (shown on ambient display)
- Waiting pool: position 9+ (visible only to the requesting guest, cannot be boosted)

---

## Billing Model

- Boosts are **pending** until the YouTube `ENDED` event confirms playback
- Only played songs generate real charges — "you only pay for songs that actually play"
- Pre-billing review: guest sees played vs. pending items, can remove pending ones
- Spend cap: ₹150/table/session (enforced atomically via Redis Lua script)
- Revenue: venue collects 100% from guest → VibeQueue invoices 40% weekly

---

## Key Files

```
backend/
├── app/
│   ├── api/v1/routes/       13 route modules (auth, queue, boosts, billing, payments, ...)
│   ├── services/            12 service modules (queue_engine, billing, payment, ...)
│   ├── models/              11 SQLAlchemy models
│   ├── core/                config, database, redis (Lua scripts), celery, security, events
│   └── workers/             Celery tasks (playback watchdog, payment reconciliation, ...)
├── alembic/versions/        2 migrations (initial schema + RLS/Realtime/hardening)
├── scripts/                 seed_db, seed_catalogue, validate_catalogue, smoke_test
└── tests/                   unit + integration tests (42 passing)

frontend/src/
├── app/                     Next.js 16 App Router (4 interface routes + error boundaries)
├── components/              guest/, dashboard/, playback/, ambient/
├── stores/                  Zustand (guest-store, dashboard-store)
├── lib/                     api.ts, supabase.ts (Realtime), utils.ts
└── types/                   TypeScript interfaces matching backend models
```

---

## Documentation

| File | Purpose |
|---|---|
| `DEPLOY.md` | Step-by-step deployment guide (Vercel + Railway + Razorpay webhook setup) |
| `CHANGELOG.md` | Dated changelog with all changes and their rationale |
| `STATUS.md` | Component-level status matrix with verification levels |
| `TODO.md` | Checklist of completed and pending items |
| `docs/progress_23082026.md` | Synthesis document from local verification session |
| `docs/progress_24082026.md` | Cloud migration & hardening session summary |
| `docs/frontend_spec.md` | Technical reference for all 4 interfaces + YouTube IFrame architecture |
| `docs/AUDIT_REPORT.md` | Detailed audit from initial frontend implementation |

---

## Bugs Fixed

| Bug | Impact | Fix |
|---|---|---|
| Realtime subscribed to wrong table names (`queue` instead of `queue_entries`, etc.) | All live-update features silently broken | Corrected table names in `supabase.ts` |
| Spend cap GET/check/INCRBY not atomic | Two concurrent boosts could both pass cap | Atomic Redis Lua script |
| No webhook idempotency | Razorpay retries could double-process payments | App guard + unique partial DB index |
| `config.py` required all third-party keys at import | App wouldn't start without every API key | Made optional with `""` defaults |
| `CORS_ORIGINS` typed as `str` | Pydantic-settings parse error | Changed to `List[str]` |
| `alembic/env.py` used async asyncpg | Incompatible with PgBouncer for DDL | Rewrote to sync psycopg2 |
| `database.py` missing PgBouncer args | Prepared statement cache errors | Added `statement_cache_size=0` |
| `logging.py` crashed with PrintLogger | Structlog `add_logger_name` incompatible | Removed from processor chain |
| `seed_catalogue.py` used hardcoded UUIDs | Didn't match generated venue IDs | Changed to slug-based lookup |
| Scoring test had wrong math | Tie-breaker test incorrectly set up | Fixed with compensating boost values |

---

## Future (Post-Pilot)

- NFC table tap (replace verbal code entry)
- JioSaavn / licensed music API integration (replace YouTube dependency)
- Multi-venue analytics dashboard
- WhatsApp notification integration
- Venue song catalogue management UI

---

*VibeQueue · August 2026 · Two-venue Bengaluru pilot*
