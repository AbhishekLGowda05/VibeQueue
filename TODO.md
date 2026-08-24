# VibeQueue — TODO

## Completed
- [x] Backend API (FastAPI) — all routes, services, models, workers
- [x] Frontend project initialization (Next.js + TypeScript + Tailwind)
- [x] Project directory structure
- [x] Core frontend infrastructure (API client, types, auth, WebSocket, stores)
- [x] Guest Interface — Join screen (table code entry)
- [x] Guest Interface — Main queue view (now playing, live queue, search, my songs)
- [x] Guest Interface — Boost selection bottom sheet
- [x] Guest Interface — Pre-billing review screen
- [x] Venue Dashboard — Staff authentication/login
- [x] Venue Dashboard — Now Playing zone + Skip/Pause controls
- [x] Venue Dashboard — Queue preview (next 5 songs)
- [x] Venue Dashboard — Active tables management (open/close/flag)
- [x] Venue Dashboard — Tonight's numbers strip
- [x] Venue Dashboard — Alert banner system
- [x] Venue Dashboard — Mode A/B toggle
- [x] YouTube Playback — IFrame Player integration
- [x] YouTube Playback — WebSocket listener for playback commands
- [x] YouTube Playback — Event reporting (ENDED, ERROR, PLAYING)
- [x] YouTube Playback — Tab keep-alive mechanism
- [x] Ambient Display — Now Playing (large text, dark theme)
- [x] Ambient Display — Next Up queue (top 3)
- [x] Ambient Display — Song progress bar
- [x] Ambient Display — QR scan CTA
- [x] PWA manifest
- [x] Production build verification (zero TS errors)
- [x] Alembic database migrations — generated and applied to Supabase (11 tables)
- [x] Backend config hardened — third-party credentials now optional, CORS type fixed
- [x] Seed data — 2 venues, 2 owners, 62 songs loaded into Supabase
- [x] Health endpoint verified — database + Redis both OK
- [x] Celery worker + beat verified running locally
- [x] pytest suite — 42 passed, 0 failed
- [x] Smoke test — full core loop verified (staff login → open table → guest join → search → request → boost → queue reorder → boost tiers)
- [x] Frontend build — zero TS errors, dev server boots, landing page renders

## Pending — Infrastructure
- [ ] Environment variable configuration for production (real secrets, not dev placeholders)
- [ ] Vercel deployment configuration
- [ ] Supabase RLS policies (currently no row-level security)
- [ ] PWA service worker for offline support
- [ ] PWA icons (icon-192.png, icon-512.png)

## Pending — Third-Party Integrations (need real API keys)
- [ ] Razorpay payment integration (need key from https://dashboard.razorpay.com)
- [ ] YouTube Data API v3 integration (need key from Google Cloud Console)
- [ ] WhatsApp Cloud API integration (need credentials from Meta Business)
- [ ] Cloudflare R2 asset storage (need credentials from Cloudflare dashboard)

## Pending — Integration Testing
- [ ] End-to-end test: guest join → request → boost → billing flow
- [ ] End-to-end test: dashboard open table → guest joins → song plays
- [ ] WebSocket real-time sync verification across all 4 interfaces
- [ ] YouTube IFrame playback test with real YouTube Premium account
- [ ] Razorpay payment integration test

## Pending — Polish
- [ ] Framer Motion animations for queue reordering
- [ ] Loading skeletons for initial data fetch
- [ ] Error boundary components
- [ ] Toast notification system
- [ ] Responsive breakpoints fine-tuning for dashboard on smaller laptops
- [ ] Ambient Display font size optimization for different TV sizes

## Future (Post-Pilot)
- [ ] NFC table tap (replace verbal code)
- [ ] JioSaavn/licensed music API integration
- [ ] Multi-venue analytics dashboard
- [ ] WhatsApp notification integration
- [ ] Venue song catalogue management UI
