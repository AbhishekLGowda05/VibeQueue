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
- [x] Environment variable configuration for production (real JWT secret generated)
- [ ] Vercel deployment (DEPLOY.md written, not deployed — need `vercel login`)
- [x] Supabase RLS policies (10 tables RLS-enabled, 5 anon SELECT policies)
- [ ] PWA service worker for offline support
- [x] PWA icons (icon-192.png, icon-512.png generated)
- [x] Supabase Realtime enabled on 5 tables
- [ ] CORS_ORIGINS update with real Vercel URL (after deployment)

## Pending — Third-Party Integrations
- [ ] Razorpay sandbox test (keys configured, DEPLOY.md has test procedure, needs ngrok + manual test)
- [x] YouTube Data API v3 catalogue validation (ran — 16/62 songs embeddable, 46 disabled)
- [ ] Refresh seed catalogue with working YouTube video IDs (only 16 of 62 are valid)
- [ ] WhatsApp Cloud API integration (not on pilot critical path)
- [ ] Cloudflare R2 asset storage (not on pilot critical path)

## Pending — Integration Testing
- [ ] End-to-end test: guest join → request → boost → billing flow (against cloud Supabase)
- [ ] End-to-end test: dashboard open table → guest joins → song plays
- [ ] WebSocket real-time sync verification across all 4 interfaces (against cloud)
- [ ] YouTube IFrame playback test with real YouTube Premium account (manual step)
- [ ] Razorpay payment integration test (sandbox — manual step, see DEPLOY.md)

## Pending — Polish
- [x] Framer Motion animations for queue reordering
- [ ] Loading skeletons for initial data fetch
- [x] Error boundary components (Next.js 16 error.tsx on all routes)
- [ ] Toast notification system
- [ ] Responsive breakpoints fine-tuning for dashboard on smaller laptops
- [ ] Ambient Display font size optimization for different TV sizes

## Future (Post-Pilot)
- [ ] NFC table tap (replace verbal code)
- [ ] JioSaavn/licensed music API integration
- [ ] Multi-venue analytics dashboard
- [ ] WhatsApp notification integration
- [ ] Venue song catalogue management UI
