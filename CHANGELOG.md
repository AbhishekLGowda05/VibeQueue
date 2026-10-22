# VibeQueue — Changelog

All notable changes to this project will be documented in this file.

---

## [2026-08-24] — Cloud Migration, Security Hardening & Production Readiness

Moved from "verified locally" to "verified against real cloud Supabase" and hardened for two-venue Bangalore pilot with real paying customers.

### Cloud Supabase Migration (Verified Against Cloud)
- Applied Alembic migration `a1b2c3d4e5f6` to real Supabase cloud project (ap-southeast-1)
- Confirmed all 11 tables exist in cloud with `alembic upgrade head`
- Seed data already present from prior session: 2 venues, 2 owners, 62 songs
- Enabled Realtime on 5 specific tables: `queue_entries`, `table_sessions`, `boosts`, `playback_commands`, `playback_events`
- NOT enabled on: `users`, `venues`, `songs`, `payments`, `audit_logs`

### Row-Level Security (Verified Against Cloud)
- Enabled RLS on all 10 data tables (not `alembic_version`)
- Created 5 SELECT-only policies for `anon` role on Realtime tables
- Zero policies on sensitive tables (`users`, `payments`, `audit_logs`, `venues`, `songs`) — anon has no access
- Architecture: frontend (anon key) gets read-only Realtime; all writes go through FastAPI backend (postgres user, bypasses RLS)
- Confirmed `service_role` key is never referenced in any frontend file

### Critical Bug Fix: Realtime Table Names (Code Fix)
- **Bug:** `frontend/src/lib/supabase.ts` subscribed to wrong table names — `queue` instead of `queue_entries`, `sessions` instead of `table_sessions`, and a nonexistent `alerts` table
- **Impact:** All live-update features (queue reordering, billing triggers, ambient display) were silently broken
- **Fix:** Corrected table names, removed `subscribeToAlerts` (no alerts table exists in schema), cleaned up DashboardView.tsx import

### Spend Cap Race Condition Fix (Code Fix)
- **Bug:** `queue_engine.py:152-178` had a TOCTOU race — Redis GET then check then INCRBY as three separate operations. Two concurrent boosts could both pass the cap check.
- **Fix:** Replaced with atomic Lua script (`SPEND_CAP_SCRIPT` in `redis.py`) that does check-and-increment in a single Redis `eval()` call. If cap would be exceeded, returns -1 without modifying the value.
- **Impact:** Prevents a table from exceeding its spend cap (₹150) under any concurrency pattern. This is real money.

### Webhook Idempotency (Code Fix)
- **Bug:** `payments.py` webhook handler had no check for duplicate `razorpay_payment_id`. Razorpay retries webhooks at-least-once.
- **Fix:** Added application-level idempotency guard (checks if payment already has `razorpay_payment_id` set before processing) + database-level unique partial index on `payments.razorpay_payment_id`
- **Impact:** Duplicate webhook deliveries now return `{"status": "already_processed"}` safely

### Production Hardening
- **JWT Secret:** Replaced dev placeholder `local-jwt-secret-key-change-in-production` with real 48-byte cryptographic secret. Added startup guard in `events.py` that refuses to boot in production mode with the placeholder.
- **Rate Limiting on /sessions/join:** Added `rate_limit_join` dependency (5 attempts/min/IP). Brute-forcing 6-digit table codes is now impractical (~7,200 attempts/day vs 1M keyspace).
- **Error Boundaries:** Created 6 Next.js 16 error boundary files using the correct `retry` prop (not `reset`):
  - `app/error.tsx` — root
  - `app/global-error.tsx` — catches root layout errors
  - `app/join/[venue]/error.tsx` — guest interface
  - `app/display/[venue]/error.tsx` — ambient display (auto-retries after 10s)
  - `app/dashboard/error.tsx` — staff dashboard
  - `app/playback/[venue]/error.tsx` — playback tab (auto-retries after 5s)
- **PWA Manifest:** Added `manifest: "/manifest.json"` to `layout.tsx` metadata (was missing)
- **Error Disclosure:** Verified `error_handler.py` already returns generic 500s with no stack traces — no change needed

### Framer Motion Animations (Written)
- **QueueCard.tsx:** `motion.div` with `layout` + `layoutId` for smooth reorder animation on boost. Spring transition (stiffness: 500, damping: 35). Entry/exit animations.
- **QueueView.tsx:** Wrapped queue list with `<AnimatePresence mode="popLayout">` so exiting items animate out while remaining items fill gaps. Wrapped BoostSheet with `<AnimatePresence>`.
- **BoostSheet.tsx:** Replaced CSS `animate-slide-up` with Framer Motion spring slide-up (`initial={{ y: "100%" }}`).
- **AmbientDisplay.tsx:** Now Playing uses `<AnimatePresence mode="wait">` with crossfade (opacity + scale). Next Up list uses `layout` animation for smooth reordering.

### PWA Icons (Written)
- Generated `icon-192.png` and `icon-512.png` — violet (#8b5cf6) background with white "VQ" text
- `manifest.json` already referenced these paths — now they exist

### YouTube Catalogue Validation (Verified Against Cloud)
- Created `scripts/validate_catalogue.py` using existing `check_videos_embeddable()` service
- Ran against real YouTube Data API with the configured API key
- **Result:** 16/62 songs passed, 46 songs disabled (not embeddable or removed from YouTube)
- Seed catalogue needs refreshing with valid video IDs before pilot launch

### Documentation
- Created `DEPLOY.md` with copy-pasteable commands for Vercel (frontend) + Railway (backend + Celery)
- Includes Razorpay webhook setup, sandbox test procedure, CORS update checklist, post-deploy verification

### Build Verification
- **pytest:** 42 passed, 0 failed (unchanged)
- **Frontend build:** zero TypeScript errors, all routes generating correctly
- **Alembic:** 2 migrations applied (initial schema + RLS/Realtime/hardening)

---

## [2026-08-23] — Local Verification Session

First time the full stack has been executed against real infrastructure. Moved from "code complete, never run" to "verified working locally."

### Infrastructure Setup
- Connected to Supabase PostgreSQL (session mode pooler, port 5432 — transaction mode port 6543 is incompatible with asyncpg prepared statements)
- Local Redis via Homebrew (redis-server on localhost:6379)
- Created `backend/.env` with local development values; all third-party API keys left as commented placeholders

### Bug Fixes (8 issues found and fixed)
- **config.py**: Made all third-party credentials optional (Razorpay, YouTube, WhatsApp, R2) — previously the app could not even import without every key set
- **config.py**: Fixed `CORS_ORIGINS` type annotation from `str` to `List[str]` (pydantic-settings v2 parse error)
- **config.py**: Added `@field_validator` to derive `CELERY_BROKER_URL`/`CELERY_RESULT_BACKEND` from `REDIS_URL` when not explicitly set
- **health.py**: Moved `JSONResponse` import from line 48 to top of file (was used at line 39, before its import)
- **alembic/env.py**: Rewrote from async (asyncpg) to sync (psycopg2) — asyncpg cannot run through PgBouncer for DDL operations
- **database.py**: Added `statement_cache_size=0` and `prepared_statement_cache_size=0` connect_args for Supabase pooler detection
- **logging.py**: Removed `structlog.stdlib.add_logger_name` from processor chain (crashed with PrintLogger)
- **seed_catalogue.py**: Changed from hardcoded UUIDs to slug-based venue lookup

### Database
- Generated Alembic initial migration from 11 SQLAlchemy models (auto-generated)
- Applied migration to Supabase — 11 tables created: venues, users, songs, table_sessions, queue_entries, boosts, payments, playback_commands, playback_events, audit_logs, alembic_version
- Seeded: 2 venues (Koramangala Social, Indiranagar Hammered), 2 venue owners, 62 songs

### Test Results
- **pytest**: 42 passed, 0 failed (unit tests for scoring, boost, billing; integration stubs pass)
- Fixed `test_tie_broken_by_older_timestamp` — original test had incorrect math (entries with equal boost but different ages have different time-decay scores; fixed with compensating boost values)

### Smoke Test (all steps passed)
- Health check: `{"status":"ok","database":"ok","redis":"ok"}`
- Staff login (JWT auth): working
- Open table session (generates 6-digit code): working
- Guest join via table code: working
- Song search: working (returns matching songs from catalogue)
- Song request: working (adds to queue)
- Boost song: working (increases score, reorders queue)
- Queue retrieval: working (returns scored, ordered queue)
- Boost tiers: working (returns venue-specific tier configuration)

### Backend Verification
- FastAPI boots on port 8000, all routes registered
- Celery worker starts, connects to Redis, registers all tasks across 6 queues
- Celery beat starts, loads periodic task schedule

### Frontend Verification
- `npm install`: 285 packages, zero vulnerabilities
- `npm run build`: successful, zero TypeScript errors
- `npm run dev`: boots on port 3000, landing page renders correctly
- **Not verified**: actual frontend ↔ backend communication in the browser (API calls, WebSocket subscriptions, Razorpay checkout)

### What's Still Unverified
- Razorpay payment flow (no API key)
- YouTube Data API integration (no API key)
- WhatsApp Cloud API notifications (no credentials)
- Cloudflare R2 asset storage (no credentials)
- Frontend ↔ backend integration in the browser
- WebSocket real-time sync across all 4 interfaces
- YouTube IFrame playback with real YouTube Premium account
- Supabase RLS policies (none configured)
- Production deployment (Vercel + Supabase)

---

## [2026-08-23] — Full Frontend Implementation

### Added — Core Infrastructure
- Initialized Next.js 16 frontend project with TypeScript, Tailwind CSS, ESLint
- Installed dependencies: zustand (state), @supabase/supabase-js (real-time), framer-motion (animations), lucide-react (icons)
- Created TypeScript type definitions for all backend models (Venue, Session, Queue, Boost, Payment, Playback, etc.)
- Built REST API client (`lib/api.ts`) with full endpoint coverage matching FastAPI backend
- Built Supabase real-time subscription helpers (`lib/supabase.ts`) for queue, playback, alerts, and session channels
- Built Zustand stores for guest state and dashboard state management
- Created utility functions for INR formatting, time display, score calculation
- Created tracking files: STATUS.md, TODO.md, CHANGELOG.md

### Added — Guest Interface (`/join/[venue]`)
- **JoinScreen**: 6-digit table code entry with numeric input, validation, and error display
- **QueueView**: Main screen with now playing banner, live queue (8 active songs), real-time search, and collapsible "My Songs" section
- **NowPlaying**: Gradient card with song title, artist, and table attribution with pulsing glow animation
- **QueueCard**: Position number, song info, table attribution, boost score badge, and Boost button
- **BoostSheet**: Bottom sheet with 3 boost tiers (₹15/₹25/₹35), estimated new position, spend remaining display
- **MySongs**: Collapsible section showing personal queue entries with status icons (active/waiting/played)
- **BillingScreen**: Pre-billing review with played/pending items, GST calculation, remove pending boosts, confirm button
- Real-time WebSocket subscription for queue updates and billing trigger

### Added — Venue Dashboard (`/dashboard`)
- **LoginForm**: Staff email/password authentication
- **DashboardView**: Full single-page dashboard with 6 zones:
  - Zone A: Now Playing with Skip and Pause All controls
  - Zone B: Queue preview (next 5 songs with table attributions and boost scores)
  - Zone C: Active Tables (open/close/flag with table codes and spend tracking)
  - Zone D: Tonight's Numbers (tables served, music revenue, songs played, boost conversion)
  - Zone E: Alert Banner (dismissible alerts for playback issues, YouTube errors)
  - Zone F: Mode Toggle (A: Automated / B: Manual with manual confirmation flow)
- **ActiveTables**: Table management with Open New Table, Close (billing), and Flag controls
- **OpenTableDialog**: Modal to generate 6-digit table code for new tables

### Added — YouTube Playback Page (`/playback/[venue]`)
- YouTube IFrame Player API integration with auto-initialization
- WebSocket listener for playback commands (play, pause, resume, skip)
- Automatic event reporting to backend (PLAYING, ENDED, ERROR, PAUSED, BUFFERING)
- Tab keep-alive via silent Web Audio API oscillator to prevent browser tab sleeping
- Connection status indicator (green/red)
- Minimal UI: 320x180 player, current song info, status bar

### Added — Ambient Display (`/display/[venue]`)
- Full-screen dark theme optimized for TV viewing from 10+ metres
- Now Playing: large song title (6xl), artist, table attribution with gradient text
- Animated progress bar showing estimated song progress
- Next Up: top 3 queued songs with position, table number, and boost score
- QR scan CTA at bottom: "WANT YOUR SONG NEXT? SCAN THE QR ON YOUR TABLE"
- Queue Paused overlay
- Real-time updates via Supabase WebSocket subscriptions

### Added — Landing Page (`/`)
- Interface selector with links to all 4 interfaces
- Violet gradient branding

### Added — PWA Configuration
- Web app manifest with standalone display mode
- Theme color (violet #8b5cf6) and dark background

### Build
- Production build successful with zero TypeScript errors
- All routes generating correctly (static + dynamic)

### Pre-existing (from initial commit)
- Full FastAPI backend with 13 API route modules
- 11 SQLAlchemy ORM models
- 12 service modules with business logic
- 9 repository modules for database access
- Celery workers with beat scheduler
- Docker + Docker Compose setup
- Test infrastructure
