# VibeQueue — Complete Pilot Blueprint
## The Full Technical & Operational Guide for the Two-Venue Bengaluru Pilot
**Version: Pilot-Ready · June 2026 · Confidential**

> This document is your single source of truth for building and running the VibeQueue pilot. It explains every moving part — every device, every piece of software, every data flow, every edge case — through the lens of a real Friday night at a Koramangala bar. No code. No jargon without explanation. By the end of this document, you will be able to close your eyes and walk through exactly what happens, step by step, from the moment a guest scans the QR code to the moment their bill is paid.

---

checkout this youtube playlist - https://youtu.be/lsu-g-_6i_A?si=R9y45VTlDZoZRPcY

## Table of Contents

1. [The Thirty-Second Summary](#1-the-thirty-second-summary)
2. [The Three Devices in the Room](#2-the-three-devices-in-the-room)
3. [The Complete Technology Stack — What, Why, and How](#3-the-complete-technology-stack)
4. [The Real-World Walkthrough — Friday Night at Koramangala](#4-the-real-world-walkthrough)
5. [Every Component Explained](#5-every-component-explained)
6. [The Queue Engine — How Songs Are Ordered](#6-the-queue-engine)
7. [The Billing System — How Money Moves](#7-the-billing-system)
8. [Edge Cases — What Happens When Things Go Wrong](#8-edge-cases)
9. [The Venue Setup Session — What You Actually Install](#9-the-venue-setup-session)
10. [Scalability Confidence — Why This Architecture Grows](#10-scalability-confidence)
11. [The Pilot Success Checklist](#11-the-pilot-success-checklist)

---

## 1. The Thirty-Second Summary

VibeQueue is three things running simultaneously:

**Thing 1 — A guest-facing web app.** Guests open it on their personal phones using mobile data. No app download. No venue Wi-Fi required for guests. They see the queue, request songs, and pay boosts.

**Thing 2 — A venue-facing dashboard.** A web app running on the venue's existing laptop, opened in a browser tab. Staff use it to monitor the queue, mark songs as played (Mode B), and handle billing. The venue's own YouTube Premium account is also open in another tab on this same laptop — that's where music plays.

**Thing 3 — A cloud brain.** Hosted on Vercel and Supabase. This is the invisible engine that takes requests from guest phones, applies the scoring and boost logic, and tells the venue laptop what to play next. It handles all the intelligence, real-time updates, and payment records.

Everything connects through the internet. Guests use their mobile data. The venue laptop uses the venue's Wi-Fi. The cloud brain sits in between, coordinating everything.

---

## 2. The Three Devices in the Room

Understanding VibeQueue starts with knowing exactly which physical objects are involved and what each one does.

### Device 1 — The Guest's Personal Phone

This is the device in every customer's pocket. They use it to join VibeQueue, browse songs, make requests, and pay boosts.

**What it needs:** Mobile data (4G or 5G). That's it. Guests do not need to connect to the venue's Wi-Fi. They do not download any app. They open a URL in their phone's browser — the same way they would open a website.

**What runs on it:** The VibeQueue Guest Interface. This is a web application that looks and feels like a simple, clean mobile app but lives entirely in the browser. It shows the live queue, a search bar, boost options, and the pre-billing review screen.

**What it does NOT do:** It does not play music. It does not control the laptop. It only sends requests and receives queue updates through the internet.

### Device 2 — The Venue's Laptop (Already Exists at the Venue)

This is the laptop or PC that the bar already uses for music. Before VibeQueue, it ran Spotify or YouTube and played music through the venue's speaker system. After VibeQueue, it does all of that plus runs the VibeQueue venue dashboard.

**What it needs:** The venue's Wi-Fi internet connection, a YouTube Premium account logged in on Chrome, and a browser tab open with the VibeQueue Venue Dashboard.

**What runs on it:** Two things, both in Chrome browser tabs.
- **Tab 1:** The VibeQueue Venue Dashboard (the staff control panel)
- **Tab 2:** A VibeQueue-specific YouTube playback page (a web page we build that embeds the YouTube IFrame Player and listens for "play this song next" instructions from the cloud)

**What it does:** It plays music through the venue's existing speaker system. When the cloud brain decides the next song should play, it sends a signal to Tab 2, which tells the YouTube IFrame Player to load and play that video. The audio comes out of the laptop's audio output, which is connected to the bar's speaker system via the existing cable or Bluetooth setup.

**What it does NOT do:** It does not run any software installation. It does not need a dedicated device. It is the venue's existing machine.

### Device 3 (Optional but Recommended) — The Ambient Display TV

This is the bar-facing TV or monitor near the bar. Most modern Bengaluru resto-bars have one. If they don't, this step is skipped for the pilot.

**What it needs:** An Android TV stick (like Mi TV Stick 4K, costs approximately ₹4,000–5,000) plugged into the TV's HDMI port, connected to the venue's Wi-Fi.

**What runs on it:** Chrome browser in full-screen mode showing the VibeQueue Ambient Display — a web page that shows "Now Playing," the upcoming queue, and table attributions in large text. This is the social layer. It's what makes the whole room feel alive.

**What it does NOT do:** It does not play music. Music comes from the laptop only. The TV only displays information.

---

## 3. The Complete Technology Stack

This section explains every piece of software and service involved, why it was chosen, and what role it plays.

### The Cloud Infrastructure

**Vercel — The Application Host**

Vercel is a hosting platform. Think of it like the landlord for all the web pages VibeQueue serves. When a guest opens the VibeQueue link on their phone, their phone contacts Vercel's servers, and Vercel delivers the web page.

Why Vercel specifically:
- It deploys instantly when you update the code. No complicated server management.
- It has a global content delivery network, meaning pages load fast regardless of where the user is.
- The free tier handles pilot-scale traffic comfortably. The Pro plan (approximately ₹1,700/month) handles hundreds of concurrent users.
- It runs "Edge Functions" — small pieces of code that run close to the user and respond in milliseconds. The queue logic can run here.

What Vercel hosts for VibeQueue:
- The Guest Interface (what guests see on their phones)
- The Venue Dashboard (what staff see on the laptop)
- The Ambient Display page (what the TV shows)
- The YouTube Playback page (the tab that plays music on the venue laptop)
- The API endpoints — the "routes" that receive requests (like "Table 7 wants to boost Kesariya") and process them

**Supabase — The Database and Real-Time Engine**

Supabase is the brain's memory. It stores everything: which songs are in the queue, how much each has been boosted, which table requested what, billing records, and venue configurations.

But Supabase does something more important than just storing data — it provides real-time communication. When Table 7 boosts a song and the queue order changes, Supabase instantly pushes that update to every connected device simultaneously: the guest's phone, the staff dashboard, and the ambient display TV all update in under a second without any device needing to refresh or ask again.

This technology is called WebSockets. Think of it like a phone call that stays open — instead of your phone texting the server every few seconds asking "has anything changed?", the server calls all connected devices the moment something changes.

Why Supabase specifically:
- It's built on PostgreSQL, a robust and proven database system
- The real-time WebSocket layer is built in — no separate messaging system needed
- Free tier covers pilot needs. Pro plan (approximately ₹1,700/month) handles production scale.
- It has Row Level Security, meaning the database itself enforces rules about who can read what data

What Supabase stores:
- **Sessions table:** Every active table session (venue, table number, table code, when it started, when it expires)
- **Queue table:** Every song in the active queue and waiting pool (song name, video ID, table that requested it, boost score, timestamp, status)
- **Boosts table:** Every boost transaction (amount, table, song, timestamp, whether the song played)
- **Venues table:** Configuration for each venue (genre packs, spend caps, operating modes, song pool)
- **Songs catalogue table:** The pre-approved song list for each venue (song name, artist, YouTube video ID, genre, enabled/disabled)

**Razorpay — The Payment Processor**

Razorpay handles all money movement. When a guest confirms their bill at the end of the night and pays for their boosts, Razorpay processes the UPI payment or card transaction.

Why Razorpay specifically:
- India's most common payment gateway for startups
- Supports UPI natively (which is how the target demographic pays for everything)
- Standard rate: 2% + 18% GST per transaction
- No setup cost for pilot scale
- Razorpay also provides a settlement layer — VibeQueue's 40% share can be split from the venue's 60% through their Route product

What Razorpay handles:
- Processing the payment when the guest confirms their bill
- Generating receipts
- Settling funds to the venue's bank account
- Recording the transaction for GST purposes

### The Guest Interface

This is a Progressive Web App (PWA). The term means a website that is designed to feel and behave like a native mobile app without being downloaded from an app store. When a guest opens it, it looks full-screen, loads fast, and responds instantly to taps.

Why a PWA and not a native app:
- Zero friction for the guest. No "download this app" step that kills adoption.
- Works on any smartphone — Android, iOS, old phones, new phones.
- Updates automatically. If you fix a bug at 9pm on a Friday, every guest sees the fix immediately. No waiting for app store approvals.
- The link in the QR code takes them directly to the correct venue's session. No searching. No setup.

The PWA is built with React. React is a JavaScript framework that makes it easy to build interfaces that update in real time. When the queue changes, the guest's screen updates without them doing anything. React handles this efficiently.

### The Venue Dashboard

Also a web application, also built with React. It runs in a browser tab on the venue's existing laptop. It is the same codebase as the guest interface but shows a completely different view based on the login role.

The dashboard has five visible elements at all times:
- Now Playing (the current song, which table requested it, a timer)
- Next Up (the next three songs in queue, with table attributions and boost scores)
- Pause/Emergency Stop button
- Flagged Songs (any song requiring review)
- Tonight's Revenue counter

In Mode B, it also has the "Mark as Played" button that appears as an alert when the next song is ready to play.

### The YouTube Playback Page

This is a custom web page that VibeQueue builds and hosts on Vercel. It exists for one purpose only: to embed a YouTube IFrame Player and listen for "play this video now" commands from Supabase in real time.

Here is exactly how it works: The page is opened in a browser tab on the venue's laptop, logged into the venue's YouTube Premium account. It maintains an active WebSocket connection to Supabase. When the queue engine decides it is time to play the next song, it writes a record to a special Supabase table called "playback_commands." The YouTube Playback Page, which is always listening, immediately receives this update and calls the YouTube IFrame Player's "load video" function with the specific YouTube video ID. The song starts playing. Audio comes out of the laptop's speakers and into the bar's sound system.

When the song ends, the YouTube IFrame Player fires an "ENDED" event. The YouTube Playback Page picks this up and writes it back to Supabase. The queue engine receives this confirmation, marks the song as played in the billing records, and triggers the next song.

Why this architecture and not direct API control: YouTube does not provide an API that lets a backend server (running on Vercel) directly command a browser tab playing on another machine. The only way to control playback in a browser is to have JavaScript running inside that browser. This page is that JavaScript. It sits in the browser, listens to the cloud brain, and controls the player. The cloud brain never touches YouTube directly — it only writes to Supabase, and the Playback Page reads from Supabase and tells YouTube what to do.

### The Ambient Display Page

Another Vercel-hosted web page, designed to fill a TV screen. It subscribes to Supabase real-time updates and displays:
- "NOW PLAYING — [Song Name]" in large text
- "REQUESTED BY TABLE 7" below it
- "NEXT UP" with the next three songs and their table numbers
- A live boost score visualization (which tables are currently competing)

It refreshes its data automatically via WebSocket. No one ever touches this page after setup. It just runs.

---

## 4. The Real-World Walkthrough — Friday Night at Koramangala

It is 9:47pm on a Friday. The bar is at about 70% capacity. Let's follow every step of what happens to Table 7 — Arjun, Priya, Rahul, and Sneha — from the moment they sit down to the moment they pay and leave. Every component mentioned above will appear in this story.

### Chapter 1 — The Table Opens (9:47pm)

The waiter walks to Table 7 after taking the group's order. He opens the **Venue Dashboard** on the laptop behind the bar. He taps "Open New Table" and selects Table 7. The dashboard generates a fresh 6-digit table code: **4-8-2-1-7-6**. This code is stored in **Supabase** as a new session record linked to Table 7 at this venue, valid for the next 90 minutes.

The waiter tells the group: "You can request songs tonight — scan the QR on the table tent and use the code 482176."

**What just happened technically:** A new row was created in Supabase's "sessions" table with the venue ID, table number, table code, creation timestamp, and expiry timestamp (90 minutes from now). The table is now "active" in the system.

### Chapter 2 — Priya Joins (9:49pm)

Priya picks up her phone and opens the camera. She scans the QR code on the small tent card on the table. Her phone opens a URL in Safari — something like `vibequeue.in/venue/koramangala-social`. This URL opens the **Guest Interface PWA** — a clean, full-screen web experience that loads in about 1.5 seconds on her 5G connection.

She sees a screen asking for the table code. She types in 482176 and taps "Join." Her phone sends this code to the **Vercel API**. The API checks Supabase: does the code 482176 exist, is it assigned to an active table at this venue, and has it not yet expired? All three: yes. The API creates a guest session token for Priya's phone and sends her into the main interface.

Now Priya sees:
- "Now Playing: Dynamite — BTS (requested by Table 3)"
- "Next Up: Kesariya — Arijit Singh (Table 2), Calm Down — Rema (Table 5), Brown Munde — AP Dhillon (Table 4)"
- A search bar
- A message: "Free requests and boosts available. Spend up to ₹150 tonight."

**What just happened technically:** Priya's phone authenticated against the sessions table in Supabase. A WebSocket connection was established between her phone and Supabase Realtime. She is now subscribed to live queue updates. Every change to the queue will push to her screen automatically.

**Why mobile data works:** The Vercel API and Supabase are internet services. Priya's phone reaches them over 5G just as it would reach any website. The venue's Wi-Fi is irrelevant for her interaction. The only device using venue Wi-Fi is the laptop, for playing music.

### Chapter 3 — Rahul Makes a Free Request (9:52pm)

Rahul types "Kesariya" in the search bar. The Guest Interface sends a search query to the Vercel API, which looks up the venue's song catalogue in Supabase. Results appear: "Kesariya — Arijit Singh (Brahmāstra)."

He taps "Request." The API:
1. Checks that Kesariya is in this venue's approved song pool (it is)
2. Checks that Table 7 has not made a request in the last 3 minutes (the cooldown — it hasn't)
3. Creates a new entry in the queue table with: song name, video ID, requesting table (7), initial boost score (0), and timestamp

Rahul's screen shows: "Kesariya is in the queue — estimated to play in about 22 minutes."

On the **Ambient Display TV**, the queue updates immediately. A fourth song appears under "Next Up."

Every other guest currently in the VibeQueue interface at this bar also sees the queue update on their screens in real time — their WebSocket connections pushed the change automatically.

**What just happened technically:** A row was inserted into the "queue" table in Supabase. The Supabase Realtime service pushed this insertion to every device subscribed to that venue's queue channel. No polling. No refresh. Just instant broadcast.

### Chapter 4 — Priya Sees the Queue Getting Crowded (10:08pm)

Twenty minutes have passed. The queue has grown. There are now 8 songs ahead of Kesariya in the active queue. Kesariya is in the waiting pool — visible on Priya's phone but not yet on the Ambient Display.

Her phone shows: "Kesariya is in the waiting list — it will enter the queue as songs play."

She tries to tap Boost. The button is greyed out with the text: "Boost available once your song enters the live queue." She can't boost it yet.

**What just happened technically:** The queue table in Supabase has 8 rows with status "active" (in the visible queue) and Kesariya has status "waiting." The frontend logic checks this status before showing the Boost button as active.

### Chapter 5 — Arjun Decides to Boost (10:22pm)

Two songs have played. Kesariya has entered the active queue at position 7. Arjun sees it on his screen. He taps "Boost." Three options appear:

- **Small Boost (+15 score)** — ₹15
- **Medium Boost (+25 score)** — ₹25
- **Priority Boost (+35 score)** — ₹35

He taps ₹25. The boost is recorded as a **pending charge** in Supabase — not yet confirmed, just noted as "Table 7 boosted Kesariya for ₹25, pending song play confirmation."

The queue engine recalculates. Kesariya's score was previously: `time_decay_factor` only (approximately 8, since it was requested 30 minutes ago and the decay formula gives diminishing value over time). Now it's: 25 (boost) + 8 (decay) = 33. The engine looks at all other songs in the queue and re-sorts them by score. Kesariya jumps from position 7 to position 3.

On the **Ambient Display TV**, the queue reorders visually and immediately. The whole bar can see it happen. The table next to Arjun's notices their song just got pushed back a position. One of them opens their phone.

**What just happened technically:** A row was inserted into the "boosts" table with the amount, table, song, and timestamp. The queue engine (running as a Vercel Edge Function triggered by the Supabase webhook) recalculated all scores in the queue table and updated the positions. Supabase pushed the reordered queue to all connected clients.

### Chapter 6 — The Song Plays (Mode A — Automated, 10:31pm)

Kesariya is now at position 1. The current song (Brown Munde) is ending. The **YouTube Playback Page** on the venue laptop is listening to Supabase via WebSocket.

The queue engine detects that the current song is about to end (it sees the ENDED event from the previous song was just written to Supabase). It writes a new instruction to the "playback_commands" table in Supabase: `{video_id: "BVBWugH_aFE", action: "play", song_name: "Kesariya", requesting_table: 7}`.

The YouTube Playback Page, which is always watching this table, receives this instruction in under 500 milliseconds. It calls the YouTube IFrame Player API: "Load video BVBWugH_aFE and play immediately." Kesariya starts playing. The audio goes through the laptop's output cable into the bar's speaker system.

Simultaneously, the Ambient Display updates: "NOW PLAYING — Kesariya · Arijit Singh · Requested by Table 7 🎵"

The venue dashboard also updates for the staff, showing Kesariya as the current song and the next three songs queued.

Table 7 reacts. They cheer quietly. Sneha takes a video for her Instagram story. The table next to them notices the attribution on the screen and laughs.

**What just happened technically:** A single Supabase table write triggered a cascade: the playback page loaded the correct YouTube video, the ambient display updated, and the staff dashboard updated — all via Supabase Realtime WebSockets, all within approximately one second.

### Chapter 7 — Song Ends, Billing Confirmed (10:34pm)

Kesariya ends three minutes later. The YouTube IFrame Player fires its ENDED event. The YouTube Playback Page picks this up and writes `{video_id: "BVBWugH_aFE", event: "ENDED", timestamp: 10:34pm}` to a "playback_events" table in Supabase.

The queue engine sees this ENDED event and does two things:
1. Marks Kesariya's status in the queue table as "played"
2. Marks the ₹25 boost in the boosts table as "confirmed — song played" — this means the charge is now real

Then it loads the next song and the cycle continues.

**What just happened technically:** The ENDED event is the billing trigger. This is the core of the deferred payment model. No charge is ever confirmed without a played event. This makes the "you only pay for songs that actually play" promise technically enforced, not just a policy.

### Chapter 8 — Sneha Tries Something Problematic (10:45pm)

Sneha, who has had a few drinks, thinks it would be funny to request "Macarena." She searches for it. It doesn't appear. The venue has not included it in their approved song pool.

She tries typing a meme song. Same result. The search only returns songs from the venue's pre-approved catalogue.

She can't request anything the venue hasn't approved. The anti-abuse architecture is structural — it's impossible to request something outside the pool, not just discouraged.

**What just happened technically:** The search API queries only the venue's "songs_catalogue" table, filtered by `venue_id = koramangala_social` and `enabled = true`. Songs outside this table simply don't exist in the search results. There's no way around it.

### Chapter 9 — The Spend Cap Activates (11:05pm)

Arjun has been boosting aggressively. He has spent ₹15 + ₹25 + ₹35 = ₹75 so far. He tries to boost again. The Boost button shows: "₹75 spent tonight. ₹75 remaining until your table limit."

At some point, he tries one more ₹35 boost and gets blocked: "You've reached tonight's music spend cap of ₹150. Your song is still in the queue." He can't spend more, but his existing songs remain.

**What just happened technically:** The API, on every boost request, queries the boosts table for all confirmed + pending boosts from Table 7's current session and sums them. If adding the new boost would exceed the venue's configured spend cap (₹150 in this case), the request is rejected before any payment is processed.

### Chapter 10 — Bill Time (11:47pm)

The group decides to leave. The waiter comes over. He taps "Open Table 7 Billing" on the Venue Dashboard.

The dashboard shows:
- Kesariya — ₹25 — PLAYED ✓
- Brown Munde — ₹15 — PLAYED ✓
- (Another song — ₹35 — NOT PLAYED — pending in queue)
- Total confirmed: ₹40 + 18% GST = ₹47.20

Simultaneously, Priya's phone shows a pre-billing review screen:

> **Tonight's VibeQueue charges for Table 7:**
> ✓ Kesariya (Arijit Singh) — Boosted — PLAYED — ₹25
> ✓ Brown Munde (AP Dhillon) — Boosted — PLAYED — ₹15
> ✗ Tumse Milke Dil Ka — Boosted — NOT PLAYED — [Tap to Remove]

She taps Remove on the unplayed song. The ₹35 pending charge disappears from both her view and the venue dashboard.

Final music total: ₹40 + ₹7.20 GST = ₹47.20.

The waiter adds this as a single line item to their food and drink bill: "VibeQueue Music — ₹47.20." The group pays the full bill — food, drinks, music — in one UPI scan. Razorpay processes the payment. The money flows: the venue receives 100% from the guest, and at end of week VibeQueue invoices the venue for its 40% share of music revenue and the venue transfers it.

**What just happened technically:** The pre-billing review screen shows all boosts from the session where status is "confirmed" (PLAYED) or "pending" (in queue but not yet played). The guest can remove pending items, which updates their status to "cancelled" in the boosts table. Only confirmed boosts appear on the final bill. The total is calculated and passed to Razorpay as a payment order.

---

## 5. Every Component Explained

### The Session and Table Code System

Every table gets a unique 6-digit code when the waiter opens it. This code is the gatekeeper. Without it, guests cannot join.

The code serves two purposes:
1. It proves the guest is physically in the venue (the waiter tells them verbally)
2. It links all activity to a specific table for billing

Codes rotate every 90 minutes. After 90 minutes, the existing code expires and a new one is generated. The waiter gives the new code to the table if they're still seated. This prevents someone outside the bar from joining using a screenshot of the QR code that was shared on WhatsApp — even if they have the QR link, they'd need the current code.

The QR code itself never changes. It's a printed sticker on the table tent. The code it contains is just the venue URL. The 6-digit session code is always verbal and always rotates.

### The Song Catalogue System

Before the venue goes live, their song catalogue is configured in Supabase. The VibeQueue team pre-loads genre packs: Bollywood Top 500, Current English Pop, Kannada Regional, EDM/Electronic, and so on. The venue owner selects which packs to activate.

Each song in the catalogue has:
- A display name and artist
- A YouTube video ID (the unique identifier for the specific YouTube video — for example, the official Kesariya video has the ID "BVBWugH_aFE")
- A genre tag
- An enabled/disabled toggle
- A time-of-day availability (optional — "only available after 10pm")

Guests only ever see songs from this catalogue. The catalogue is the entire universe of requestable content for that venue.

### The Queue Engine

The queue engine is a set of rules that run as Vercel Functions (small server-side scripts triggered by API calls). The engine does not run continuously — it runs in response to events: a new request, a new boost, a song ending, a song being skipped.

The scoring formula: `score = sum_of_all_boosts_for_this_song + (10 / minutes_since_request)`

This means:
- A song boosted ₹25 one minute ago has score: 25 + (10/1) = 35
- A song with no boost requested one minute ago has score: 0 + (10/1) = 10
- A song with no boost requested 30 minutes ago has score: 0 + (10/30) = 0.33
- Time naturally promotes older songs — preventing a song from sitting in the queue forever

The queue engine reads all songs with status "active" from Supabase, sorts them by score descending, and assigns positions 1 through 8. Position 1 is next to play.

When a song has a score tie (same boost amounts, same age), the tie-breaker is **the timestamp of the original request** — older request goes first. This is predictable and explainable to guests: "Equal boosts go in the order they were requested."

### The Waiting Pool Logic

Songs in positions 9 and beyond are in the waiting pool. They are stored in Supabase with status "waiting" and are not shown on the Ambient Display. They are visible only on the requesting guest's own phone.

Waiting pool rules:
- Waiting pool songs cannot receive boosts (boosting opens only when the song is in the active queue — positions 1–8)
- When a song leaves the active queue (played, skipped, or expired), the highest-scoring waiting pool song automatically moves to position 8 in the active queue
- Songs expire after 90 minutes if not played. The guest is notified and the song is removed with no charge.
- Guests can cancel waiting pool songs at any time, with no charge

### The Fallback System (Mode A)

The YouTube Playback Page monitors its own health. If the YouTube IFrame Player fires an ERROR event and does not recover within 30 seconds (meaning the video failed to load or play), the following automated sequence occurs:

1. The Ambient Display switches to a "Short break — music continues in a moment" message
2. The Venue Dashboard fires an alert: "YouTube issue detected — switch to your backup playlist now"
3. The queue engine cancels the boost charge for the current failing song (no guest is charged)
4. After 2 minutes of non-recovery, the queue is paused
5. A WhatsApp alert goes to the VibeQueue support contact (the founder's number) for immediate investigation

The staff action at step 2 is: raise the volume on the Spotify playlist that has been quietly running in a separate tab or on their phone. This is documented on the laminated card: "If music stops — open Spotify tab and raise volume." One action. Five seconds. The bar never goes fully silent.

---

## 6. The Queue Engine — How Songs Are Ordered

Let's walk through a specific example of queue ordering to make the logic completely concrete.

At 10:30pm, the active queue has these songs:

| Position | Song | Table | Boost Total | Time Since Request | Calculated Score |
|---|---|---|---|---|---|
| 1 | Brown Munde | Table 4 | ₹35 | 5 min | 35 + 2.0 = 37.0 |
| 2 | Kesariya | Table 7 | ₹25 | 8 min | 25 + 1.25 = 26.25 |
| 3 | Pasoori | Table 2 | ₹25 | 12 min | 25 + 0.83 = 25.83 |
| 4 | Aafat | Table 1 | ₹15 | 3 min | 15 + 3.33 = 18.33 |
| 5 | Calm Down | Table 5 | ₹0 | 2 min | 0 + 5.0 = 5.0 |
| 6 | Shape of You | Table 3 | ₹0 | 4 min | 0 + 2.5 = 2.5 |
| 7 | Butta Bomma | Table 6 | ₹0 | 6 min | 0 + 1.67 = 1.67 |
| 8 | Levitating | Table 8 | ₹0 | 8 min | 0 + 1.25 = 1.25 |

Now Table 5 boosts "Calm Down" with a ₹35 Priority Boost. New score: 35 + 5.0 = 40.0.

Scores recalculated:

| Position | Song | New Score |
|---|---|---|
| 1 | Calm Down | 40.0 ← jumped from 5 to 8 |
| 2 | Brown Munde | 37.0 |
| 3 | Kesariya | 26.25 |
| ... | ... | ... |

The queue instantly reorders. Calm Down is now next to play. The Ambient Display shows this live. Table 5 watches their song jump. Other tables see it happen. Social energy spikes. Two more tables open their phones to boost.

This is the product. The visible competition, the live reordering, the social moment — this all emerges from the queue engine doing a simple mathematical sort every time something changes.

---

## 7. The Billing System — How Money Moves

### The Deferred Model Explained

No money is collected at the time of a boost. When Arjun taps "Boost ₹25," the system creates a pending charge — a record that says "Table 7 intends to pay ₹25 for Kesariya, if and only if it plays."

Money only becomes real when the ENDED event confirms the song completed. At that point, the pending charge becomes a confirmed charge. If the song never plays (queue expires, song is removed, venue switches to fallback mode), the charge is automatically cancelled.

At bill time, the guest reviews all confirmed charges and any remaining pending charges (songs still in queue). They can remove pending ones. They confirm the rest. Razorpay generates a payment order for the confirmed total. The guest pays once, for everything — food, drinks, and music — in a single transaction.

### The Revenue Split

For every ₹25 boost:
- Guest pays ₹25
- 18% GST (₹4.50) goes to the government, collected by the venue as the service provider
- Pre-GST amount: ₹21.19
- Venue receives 60% of pre-GST: ₹12.71
- VibeQueue receives 40% of pre-GST: ₹8.47

In practice, the venue collects the full amount from the guest. At end of week, VibeQueue sends an invoice to the venue for its 40% share (calculated on pre-GST boost revenue). The venue bank transfers this amount. This makes settlement simple — one transfer per venue per week.

### GST Treatment

Music boost fees are classified as "interactive digital service charges." GST rate: 18%. This is consistent with how digital service fees are taxed in India and consistent with the other GST line items already on the bar's bill. The venue's GST registration covers this. VibeQueue issues weekly B2B invoices to venues, which they can claim as input credit.

---

## 8. Edge Cases — What Happens When Things Go Wrong

### Edge Case 1: The Internet Goes Down at the Venue

**What breaks:** The YouTube Playback Page can no longer stream music. The queue engine can no longer receive events.

**What doesn't break:** If internet drops during a song, the song currently buffered in the YouTube player will continue playing for 30–60 seconds (browsers buffer ahead). After that, music stops.

**What happens:** The fallback alert fires on the venue dashboard. Staff switch to Spotify on their phone, played through Bluetooth to the same speaker system. The queue pauses. No charges are confirmed for songs that didn't play.

**The honest reality:** This is the same experience the venue already has if internet drops while playing Spotify. VibeQueue doesn't make this worse — it just changes what the staff's backup action is.

### Edge Case 2: A Guest's Table Code Expires Mid-Evening (90-Minute Rotation)

**What happens:** The guest's session becomes invalid. The next time they try to interact (boost, request), the API returns an "expired session" error. Their phone shows: "Your session has ended. Get the new table code from your waiter to continue."

**What happens to their existing queue entries:** Songs already in the queue continue to be eligible to play. Pending boosts for those songs remain pending. Their in-progress queue activity is preserved. Only new requests require re-authentication.

**The staff action:** Waiter tells them the new 90-minute code. Takes 5 seconds.

### Edge Case 3: Two Tables Simultaneously Boost the Same Song to the Same Score

**What happens:** The tie-breaker is the original request timestamp. The song that was requested first goes first. This is communicated clearly in the UI and is fully deterministic — no randomness, no dispute possible.

### Edge Case 4: A Song's YouTube Video Gets Removed or Becomes Unembeddable

**What happens during the week:** The weekly automated re-validation job (running Monday at 3am as a Vercel Cron Job) checks every video ID in every venue's catalogue. It attempts to confirm each video's embeddable status via the YouTube Data API. Any video that fails is flagged in the venue dashboard and hidden from guest search. The venue owner receives a WhatsApp message: "3 songs in your catalogue may have become unavailable. Tap here to replace them (2 minutes)."

**What happens if it goes wrong on a Saturday night:** The YouTube Playback Page fires an ERROR event when it tries to load the unavailable video. The fallback sequence triggers automatically. The boost for that song is cancelled. The next song in queue plays.

### Edge Case 5: Staff Member Forgets to Open the YouTube Playback Tab

**What happens:** The queue engine sends a playback command to Supabase. Nobody is listening because the tab isn't open. The command sits in the database. Nothing plays.

**How it's caught:** The queue engine has a watchdog: if a playback command has been in the "pending" state for more than 60 seconds without a "playing" confirmation, the Venue Dashboard fires an alert: "Playback issue — check that the music tab is open." The laminated card has a step for this.

**How it's prevented:** The playback tab's URL is set as a bookmarked tab or a pinned tab on the venue's laptop Chrome browser. Opening it is part of the standard "start of evening" checklist: open laptop, log into YouTube Premium, open VibeQueue dashboard, open VibeQueue playback tab. Three tabs, five minutes.

### Edge Case 6: A Guest Tries to Pay But UPI Fails

**What happens:** Razorpay handles UPI failures with a retry flow. The guest sees a "Payment failed — try again" screen and can retry with the same UPI ID, a different UPI app, or a card. The confirmed charges are preserved in Supabase — nothing is lost. The billing session waits for successful payment before closing the table.

**What if it keeps failing:** The waiter can mark the music charge as "collect in cash" directly in the venue dashboard. A ₹47 music charge collected in cash is noted, the table is closed, and VibeQueue's 40% share of that transaction is still invoiced to the venue at end of week. No data is lost.

### Edge Case 7: The Venue Owner Wants to Override the Queue Entirely

**What they do:** Tap the Pause button on the Venue Dashboard. One tap. The queue freezes. All guest interaction is suspended (guests see "Queue paused — back soon"). The venue plays whatever they want. When they're ready to resume, they tap Resume. The queue continues from where it was.

This is the escape valve that makes venue owners comfortable trusting the system in the first place. They always have an exit.

### Edge Case 8: A Drunk Guest is Being Disruptive

**Scenario:** A table has been requesting lots of songs and other tables are complaining.

**The system's automatic response:** The per-table request cooldown (one request per 3 minutes, configurable) naturally limits flooding. The spend cap limits aggressive boosting. The social visibility of table attributions creates social accountability.

**The staff's manual response:** On the Venue Dashboard, the staff can flag a table. This triggers a temporary cooldown on that table's request privileges — they can still see the queue but cannot request or boost for a configured period (default: 15 minutes). This is invisible to the guest — they don't get a notification saying they're flagged, they just find that their requests aren't going through.

---

## 9. The Venue Setup Session — What You Actually Install and Configure

The entire setup is designed to take 20 minutes with one VibeQueue team member present (you, the founder, for the two pilot venues).

### Before You Arrive at the Venue

1. Create the venue's profile in Supabase (venue name, address, spend cap, default mode)
2. Pre-load their approved song catalogue (you select genre packs based on what you know about the venue)
3. Print two laminated cards (Staff side / Owner side)
4. Print the table tent QR codes (one per table)

### At the Venue: The 20-Minute Session

**Minutes 1–5 — Network Test**
Connect four devices (two phones, a laptop, and a tablet) to the venue's Wi-Fi simultaneously. Open the VibeQueue venue dashboard on each. If load time is under 2 seconds on all four, the network passes. If not, a TP-Link access point is installed (₹2,500–3,500, takes 10 minutes).

**Minutes 5–12 — Laptop Setup**
On the venue's existing laptop:
- Open Chrome
- Log into the venue's Google account (which has YouTube Premium active — Premium was purchased before this session)
- Open the VibeQueue Venue Dashboard URL — the staff logs in with their venue credentials
- Open the VibeQueue Playback Tab URL — this is the custom page that embeds the YouTube player
- Open Spotify in a third tab as the backup playlist
- Pin all three tabs in Chrome so they don't get accidentally closed
- Test: add a song to the queue via the dashboard, confirm it plays on the Playback Tab, confirm audio comes through the speakers

**Minutes 12–16 — Song Pool Configuration**
Walk the owner through the pre-loaded catalogue. Which genres are active? Any songs to disable? Enable time-based mode switching if they want it (e.g., jazz pool before 9pm, Bollywood after).

**Minutes 16–19 — Ambient Display Setup**
If the venue has a TV: plug in the Android TV stick, connect to venue Wi-Fi, open Chrome, navigate to the VibeQueue Ambient Display URL, tap full-screen. Done.

**Minute 19–20 — Staff Briefing**
Show the waiter the five elements of the dashboard. Show them the "Open Table" flow. Show them the Pause button. Hand them the laminated card. Ask them to open a table themselves while you watch. Done.

**Leave behind:**
- Laminated card cable-tied to the laptop or taped to the bar counter
- Table tent QR codes on all tables
- The venue's WhatsApp group includes the owner (not just the manager)
- Your number saved in the group for Friday/Saturday peak-hour support

---

## 10. Scalability Confidence — Why This Architecture Grows

You said you don't want to focus much on scale — just enough confidence that it's possible. Here is that confidence, stated simply.

**The architecture is already cloud-native.** Vercel and Supabase are not local systems — they are cloud services that scale horizontally. Adding venue 3 is identical to adding venue 1: create a Supabase record, configure a catalogue, give the owner their dashboard URL. No new servers. No new deployments.

**The database is designed for multi-tenancy from day one.** Every table in Supabase has a `venue_id` column. Every query is filtered by venue. Venue 1's queue never touches Venue 2's data. Adding 50 venues means 50 independent data channels running through the same infrastructure.

**Vercel's Edge Functions autoscale.** If 500 guests all send requests simultaneously across 20 venues on a Friday night, Vercel spins up more compute automatically. You never touch a server.

**Supabase Realtime scales to thousands of concurrent connections** on the Pro plan. At 50 venues with 30 concurrent guests each, that's 1,500 WebSocket connections — well within limits.

**The cost curve is predictable.** Infrastructure cost grows linearly with venue count (roughly ₹400–600 per venue per month in compute). Revenue grows faster than cost as long as boost conversion is above 5%.

The migration path from YouTube to JioSaavn or a licensed music API in Phase 3 is a change to the Playback Tab only — the queue engine, billing system, guest interface, and venue dashboard are entirely platform-agnostic. Swapping the music playback layer does not require rebuilding anything else.

---

## 11. The Pilot Success Checklist

Before the first venue goes live, every item on this list must be checked off.

### Technical Readiness
- [ ] Supabase project created, all tables defined, Row Level Security configured
- [ ] Vercel project deployed, all pages accessible from a public URL
- [ ] YouTube Playback Page tested end-to-end: queue update → Supabase → page receives it → YouTube player loads video → ENDED event captured → Supabase updated
- [ ] Pre-billing review tested: boost created → song played → charge confirmed → song not played → charge removable
- [ ] Razorpay test payments processed successfully
- [ ] Weekly catalogue re-validation cron job scheduled and tested
- [ ] Fallback sequence tested: ERROR event fires → dashboard alert → charge cancelled → next song loads

### Venue Readiness
- [ ] Venue's Google account created with YouTube Premium active
- [ ] Network test passed (under 2 seconds load time, 4 devices simultaneous)
- [ ] Three Chrome tabs pinned on venue laptop (Dashboard, Playback, Spotify backup)
- [ ] Ambient display TV set up and showing correct venue queue
- [ ] Table tent QR codes placed on all tables
- [ ] Laminated reference cards in place
- [ ] WhatsApp group created with owner included
- [ ] Staff walkthrough completed — waiter can open a table independently

### Legal Readiness
- [ ] Venue agreement signed, including liability clause for music licensing and YouTube TOS compliance
- [ ] GST treatment confirmed (18% on music charges, shown as separate line item)
- [ ] IP lawyer reviewed the agreement (can be done in the first week if not before)

### Operational Readiness
- [ ] Founder available on WhatsApp for Friday and Saturday peak hours (8pm–1am) for weeks 1 and 2
- [ ] Pilot success metrics dashboard configured (boost conversion rate, participation rate, error rate, etc.)
- [ ] End-of-week revenue report template prepared for venue owner WhatsApp

---

*VibeQueue Pilot Blueprint · June 2026 · Confidential*
*This document describes the two-venue Bengaluru pilot architecture. Scale considerations are addressed in the Scale Path section of the Master Plan.*