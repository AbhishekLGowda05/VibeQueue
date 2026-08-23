# VibeQueue — Changelog

All notable changes to this project will be documented in this file.

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
