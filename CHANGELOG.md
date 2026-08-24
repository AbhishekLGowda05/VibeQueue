# VibeQueue — Changelog

All notable changes to this project will be documented in this file.

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
