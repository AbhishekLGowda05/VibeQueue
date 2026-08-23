# VibeQueue — Interfaces, Architecture & YouTube IFrame: Complete Technical Reference

**Version: Pilot-Ready · June 2026 · Confidential**

> This document answers two questions that the Pilot Blueprint deliberately left underexplained:
> 1. How does the YouTube IFrame Player actually work, and why is it the right tool for this job?
> 2. What do each of the four interfaces look like, who uses them, what do they contain, and how does the backend serve each one?
>
> Everything here is written for a builder who needs to understand the system well enough to direct it, not just read about it.

---

## TABLE OF CONTENTS

1. [The Four Interfaces — Quick Map](#1-the-four-interfaces--quick-map)
2. [The YouTube IFrame Player — What It Is and Why It Matters](#2-the-youtube-iframe-player--what-it-is-and-why-it-matters)
3. [Interface 1 — The Guest Interface (Phone)](#3-interface-1--the-guest-interface-phone)
4. [Interface 2 — The YouTube Playback Page (Laptop Tab 2)](#4-interface-2--the-youtube-playback-page-laptop-tab-2)
5. [Interface 3 — The Venue Dashboard (Laptop Tab 1)](#5-interface-3--the-venue-dashboard-laptop-tab-1)
6. [Interface 4 — The Ambient Display (TV)](#6-interface-4--the-ambient-display-tv)
7. [How All Four Interfaces Talk To Each Other](#7-how-all-four-interfaces-talk-to-each-other)
8. [The Complete Data Flow — One Boost, All Four Screens](#8-the-complete-data-flow--one-boost-all-four-screens)
9. [Critical Analysis — What Can Go Wrong With This Architecture](#9-critical-analysis--what-can-go-wrong-with-this-architecture)
10. [Backend Responsibilities Per Interface](#10-backend-responsibilities-per-interface)

---

## 1. The Four Interfaces — Quick Map

Before going deep, here is the complete map of every screen in VibeQueue, who sees it, and what device it runs on.

```
DEVICE                  INTERFACE               WHO USES IT         PURPOSE
─────────────────────────────────────────────────────────────────────────────────
Guest's phone           Guest Interface         Customers           Request + boost songs
Venue laptop (Tab 1)    Venue Dashboard         Staff               Monitor + control queue
Venue laptop (Tab 2)    YouTube Playback Page   Nobody (automated)  Actually play music
Venue TV                Ambient Display         Everyone in room    Social scoreboard
```

These four interfaces are running simultaneously at all times during service. They are all web pages. None of them are native apps. None of them require installation. They all talk to the same backend (your FastAPI server) and the same database (Supabase).

**The most important thing to understand:** These four pages are not four separate products. They are four different views into the same shared data. When the queue changes in the database, all four update simultaneously. They are like four windows into the same room.

---

## 2. The YouTube IFrame Player — What It Is and Why It Matters

This is the piece of the architecture that most people find confusing, so let's spend real time here before talking about the interfaces.

### What is an IFrame?

An IFrame (Inline Frame) is an HTML element that embeds one website inside another website. Think of it like a picture frame on a wall — the frame is your web page, and inside the frame is a completely separate website (in this case, YouTube). The two are visually merged but technically independent.

When you go to any website that shows a YouTube video without sending you to YouTube.com, that is an IFrame. The video is playing on YouTube's servers. The web page is just displaying a window into YouTube.

**Analogy:** An IFrame is like a TV within a TV. Your living room TV shows a cooking show. On the cooking show, there is a smaller TV in the kitchen that is showing a football match. The kitchen TV is running independently — changing the cooking show's channel does not change what is on the kitchen TV. But the cooking show can point a camera at the kitchen TV and show it to you.

### What is the YouTube IFrame Player API?

YouTube provides a JavaScript library called the IFrame Player API. This library lets the web page surrounding the IFrame **control** the YouTube player programmatically using JavaScript. Without this API, you can only embed a video and the user can control it manually (play, pause, skip). With the IFrame Player API, your code can:

- Tell the player to load a specific video by its video ID
- Tell the player to play, pause, or stop
- Tell the player to start from a specific timestamp
- Read the player's current state (is it playing? paused? buffering?)
- Listen to events (when does the video end? when does an error occur?)

**Analogy:** Without the API, the IFrame is a TV that only has physical buttons. You have to walk up to it and press play. With the IFrame Player API, you have installed a remote control. Your JavaScript code is the remote. It can press play, press stop, change the channel, and it can also receive signals back from the TV (the TV sends you a notification when the current show ends).

### The Specific Events VibeQueue Uses

The IFrame Player API fires events automatically. You write JavaScript functions that listen to these events. When the event fires, your function runs. The three events VibeQueue uses are:

**onStateChange** — fires every time the player's state changes. The states are:
- -1 (unstarted, video is loaded but not yet played)
- 0 (ENDED — the video finished playing naturally)
- 1 (PLAYING — the video is actively playing)
- 2 (PAUSED — the user or code paused it)
- 3 (BUFFERING — loading the video)
- 5 (VIDEO_CUED — a new video has been cued but not started)

**onError** — fires when a video fails to load or play. The error codes are:
- 2 (invalid video ID)
- 5 (HTML5 player error)
- 100 (video not found or private)
- 101 or 150 (video cannot be embedded — the uploader has disabled embedding)

These error codes are the reason the weekly catalogue re-validation exists. A music video might be embeddable today and have embedding disabled next week when the label asks YouTube to restrict it.

**onReady** — fires once when the player has loaded and is ready to accept commands. Before this event fires, calling player.loadVideoById() does nothing.

### Why Can't the Backend Play Music Directly?

This is the most important architectural question, and the answer is fundamental.

Your backend server (FastAPI on Railway/Render) is a computer running in a data centre. It has no speakers. It cannot play audio. It can process data, store records, and respond to API calls, but it has no audio output and no browser.

YouTube's IFrame Player API only works inside a browser. The API is JavaScript that runs in Chrome or Safari. There is no server-side version. There is no way to call YouTube from Python and say "play this video on that laptop in Koramangala."

What you CAN do from the backend: write data to the database.

What the browser tab CAN do: read data from the database in real time and react to it.

This is the architecture. Your backend writes "play video BVBWugH_aFE" to a Supabase table. The YouTube Playback Page (running in the browser on the venue laptop) is always watching that table. The moment the backend writes the command, the browser tab reads it and tells the IFrame Player to load and play that video.

**Analogy:** Imagine a restaurant kitchen. The backend is the head chef who writes orders on tickets. The IFrame Player is the line cook who is watching the ticket rail. The head chef cannot cook the food himself — he is in the office. But he can write a ticket, and the moment it appears on the rail, the line cook picks it up and cooks the dish.

### The YouTube Premium Requirement

YouTube Premium is required for one specific reason: ads.

Without YouTube Premium, YouTube videos show advertisements before and during playback. An ad playing through the bar's speaker system for 30 seconds before every song is a catastrophic UX failure. The venue paid for YouTube Premium to eliminate ads. The IFrame Player respects the Premium account status — if the account watching the video has Premium, ads are suppressed.

This is why the YouTube Playback Page must be open in a Chrome tab that is logged into the venue's YouTube Premium Google account. The Premium status is tied to the Google account, not to the device or the URL.

### What "Video ID" Means

Every YouTube video has a unique identifier in its URL. When you go to `youtube.com/watch?v=BVBWugH_aFE`, the value after `?v=` is the video ID: `BVBWugH_aFE`. This is what you store in your song catalogue. When you call `player.loadVideoById("BVBWugH_aFE")`, YouTube loads that exact video regardless of what the URL looks like.

This ID is stable — it does not change unless the video is deleted and re-uploaded. A video can change its title, thumbnail, or description and the ID stays the same. This is why you store the ID in the database, not the full URL.

---

## 3. Interface 1 — The Guest Interface (Phone)

### Who Uses This

Every customer who walks into the venue. They are 20–30 years old, on 4G or 5G, using their personal phone. They did not download anything. They arrived at this page by scanning a QR code on the table tent. They may be sober or four drinks in.

**Critical design constraint:** This interface must be understandable by a drunk 23-year-old in 10 seconds. If it requires explanation, it has failed.

### How They Get Here

The QR code on the table tent encodes a URL like `vibequeue.in/join/koramangala-social`. When scanned, their phone opens this URL in the default browser (Safari on iPhone, Chrome on Android). No app download. No sign-up form. The page loads and shows one thing: a text field asking for the table code.

The table code is the 6-digit number the waiter told them verbally when they sat down. They type it and tap Join. That is the entire onboarding.

**Why a verbal code and not automatic join?** Because the QR code is printed on the table tent. Someone could photograph the QR code and join from outside the venue. The verbal code proves physical presence — the waiter only gives it to people who are actually sitting at that table right now. This is also the link between the guest's digital activity and their physical bill.

### The Screens They See (in order)

**Screen 0 — Join Screen (30 seconds)**

A minimal screen. Your logo, a text field saying "Enter table code," and a Join button. Below the text field, optional text explaining that the waiter gives them the code. That is it. No signup, no account creation, no terms of service wall. The faster this screen disappears, the better.

Backend connection: The Join button sends a POST request to `/api/v1/auth/join` with the table code and venue slug. The backend validates the code against the sessions table in Supabase. If valid, it returns a JWT token and the guest is in. The phone stores this JWT in memory (not local storage — local storage is disabled in Claude artifacts and unreliable in private browsing). The JWT is included in every subsequent API call.

**Screen 1 — Main Queue View (The Home Screen, seen all evening)**

This is the screen they spend 80% of their time on. It has four sections:

*Section A — Now Playing Banner (top of screen)*

Shows the song currently playing, the artist name, and which table requested it. Example: "NOW PLAYING: Kesariya · Arijit Singh · Requested by Table 3."

This banner is live — it updates the moment the song changes. It does not need to be refreshed. The guest's phone has an open WebSocket connection to Supabase. When the backend writes a new "currently playing" event, Supabase pushes it to every connected phone instantly.

*Section B — Live Queue (middle of screen)*

A scrollable list of up to 8 songs in the active queue. Each entry shows:
- Position number (1, 2, 3...)
- Song name and artist
- Which table requested it
- The current boost score (shown as a simple number or a visual bar)
- A Boost button

The list reorders in real time. When Table 5 boosts Calm Down and it jumps from position 5 to position 1, the guest watching their phone sees the cards animate upward. This live reordering is the social spectacle that makes people want to participate.

**Scenario:** Arjun is sitting at Table 7. He can see on the queue that Kesariya is at position 5. His table requested it. He can see that position 2 (Pasoori, requested by Table 2) has a boost score of 25. He taps the Boost button on Kesariya, picks ₹25, and watches his song jump from position 5 to position 3 in real time. The animation happens on every phone in the room simultaneously.

*Section C — Search Bar (below the queue)*

A simple text search field. The guest types a song name. The result set comes from the venue's approved catalogue only. If they search "Macarena" and it is not in the catalogue, it does not appear. There is no "request a song not in the list" option. The catalogue is the universe.

Backend connection: Every keystroke after 2 characters sends a GET request to `/api/v1/songs/search?venue_id=...&q=Kesariya`. The backend queries only rows in the songs_catalogue table where `venue_id` matches and `enabled = true`. The results come back in under 200ms. No search engine, no AI — just a SQL ILIKE query on the title and artist columns.

*Section D — My Songs (bottom section, collapsible)*

Shows only the songs this specific table has requested and their status:
- "In queue at position 4 — boost to move up?"
- "In waiting list — enters queue when a slot opens"
- "PLAYED ✓ — ₹25 confirmed"

This is the only personalised section of the screen. Everything else is venue-wide. This section is pulled from the queue table filtered by the session_id from their JWT — only their table's songs appear here.

**Screen 2 — Boost Selection Sheet (appears when they tap Boost)**

A bottom sheet (slides up from the bottom of the screen, covering about half the screen). Shows three options:

```
BOOST KESARIYA
─────────────────────────────
🔺 Small Boost    +15 score    ₹15
🔺 Medium Boost   +25 score    ₹25
🔺 Priority       +35 score    ₹35
─────────────────────────────
Current position: #5
With Medium Boost: moves to approx. #3
─────────────────────────────
[CONFIRM ₹25]          [Cancel]
```

The estimated new position is calculated client-side in real time based on the current scores visible in the queue. It is an approximation — between the time they see this sheet and the time they tap Confirm, someone else may have boosted. The backend re-calculates the actual final position on submission, so the displayed estimate may differ slightly from the result.

**Why no free boost? Why no Boost button for songs in the waiting pool?**

Boosting is only available for songs in the active queue (positions 1–8). Songs in the waiting pool (positions 9+) cannot be boosted. This prevents guests from paying money to boost a song that may never play. The boost converts to a confirmed charge only when the song actually plays — so you cannot confirm a charge for a song that is not yet competing for a real position. Once the song enters the active queue, the Boost button activates.

**Screen 3 — Pre-Billing Review (appears when waiter closes the table)**

The waiter taps "Open Billing for Table 7" on the Venue Dashboard. This triggers a state change in the database. The guest's phone detects this state change via WebSocket and automatically shows the billing screen — the guest does not navigate here themselves.

The billing screen shows:

```
TONIGHT'S MUSIC TAB
Table 7 · 4 guests
─────────────────────────────
✓ PLAYED  Kesariya          ₹25
✓ PLAYED  Brown Munde       ₹15
✗ PENDING Tumse Milke...    ₹35  [Remove]
─────────────────────────────
CONFIRMED TOTAL:             ₹40
GST (18%):                   ₹7.20
─────────────────────────────
MUSIC TOTAL:                 ₹47.20
─────────────────────────────
[This will be added to your food bill]
[CONFIRM →]
```

The pending song (Tumse Milke...) has a Remove button. Tapping Remove sends a DELETE request to `/api/v1/boosts/{boost_id}` which sets that boost to "cancelled" in the database. The total updates immediately. The waiter's dashboard also shows the updated total instantly.

After the guest taps Confirm, the phone shows a simple success screen: "Music tab added to your bill. ₹47.20." They pay the whole thing — food + music — when the waiter brings the bill. One payment covers everything.

### What the Backend Does For This Interface

Every action on the guest phone is a REST API call or a WebSocket subscription:

| Guest Action | Backend Endpoint | What Happens |
|---|---|---|
| Tap Join with table code | POST /auth/join | Validate code, create JWT, return token |
| Page loads (queue) | GET /queue/{venue_id} | Return full active queue state |
| WebSocket subscribe | WS /venue/{venue_id}/queue | Push live updates as queue changes |
| Search for a song | GET /songs/search?q=Kesariya | Query catalogue, return matching songs |
| Tap Request | POST /queue/request | Validate cooldown, add to queue |
| Tap Boost | POST /boosts/ | Check spend cap, create pending boost, recalculate queue |
| Remove pending boost | DELETE /boosts/{id} | Cancel pending charge |
| Billing screen appears | (pushed via WebSocket) | Backend writes billing_open event, phone receives it |
| Tap Confirm | POST /billing/confirm | Freeze confirmed boosts, mark session as billing |

---

## 4. Interface 2 — The YouTube Playback Page (Laptop Tab 2)

### Who Uses This

Nobody. This page is not for humans. It is a machine-operated interface.

This is the single most misunderstood piece of the architecture. Staff never look at it. Guests never see it. It sits in a pinned browser tab on the venue's laptop, hidden behind Tab 1 (the Venue Dashboard), and it does one thing: it listens for instructions from the database and tells YouTube what to play.

**Analogy:** Think of this page as a robotic DJ's hands. The robotic DJ's brain (your backend) decides what song to play. But it cannot physically press play on YouTube — it does not have hands. The YouTube Playback Page is the hands. The brain writes an instruction, the hands read it and press play.

### What It Looks Like

During normal operation, this page should be nearly invisible. The staff should barely notice it exists. Visually it shows:

- A YouTube IFrame Player (likely minimized or showing a still frame)
- A status indicator: "PLAYING: Kesariya · Arijit Singh" in small text
- A connection indicator: a green dot confirming the Supabase WebSocket is active
- No other controls — no buttons for humans to press

The YouTube IFrame Player on this page is the video player. Audio from this player goes through the laptop's audio output → audio cable/Bluetooth → venue speaker system. This is where the actual music comes from.

**Why is the YouTube video visible at all?** YouTube's embed terms require the player to be visible and not hidden by CSS. You cannot embed a YouTube player with `display: none` and have it play audio only. YouTube's terms prohibit this. So the player must be visible. But it can be very small — a 320×180 pixel window in the corner of the page is fine. The page background can be dark with minimal UI so it does not distract.

### The Exact Technical Mechanism

Here is step by step what happens inside this page from the moment it opens:

**Step 1 — Page Loads, IFrame API Initialises**

The page loads the YouTube IFrame Player API script from YouTube's servers. Once loaded, it creates a new YT.Player object in a `<div>` on the page. The YT.Player initialisation accepts:
- The element to replace with the player
- Initial dimensions (width and height in pixels)
- Player variables (autoplay, controls hidden, modestbranding)
- Event listener functions (onReady, onStateChange, onError)

At this point, the player is an empty grey box. No video is loaded yet.

**Step 2 — onReady Event Fires**

When the YouTube player has finished loading and is ready, it fires the onReady event. Your JavaScript function for onReady runs. It does one thing: opens a Supabase real-time subscription to the `playback_commands` table filtered by `venue_id = koramangala-social` and `status = pending`.

This subscription is now open and listening. Nothing has played yet.

**Step 3 — Waiting for Instructions**

The page sits idle. The Supabase WebSocket connection is open. The JavaScript is running. The YouTube player is ready. The speaker cable is connected. Everything is ready. But nothing is happening because no instruction has arrived yet.

**Step 4 — Instruction Arrives**

The queue engine (your backend) decides it is time to play the next song. It writes a row to the `playback_commands` table in Supabase:

```
{
  venue_id: "koramangala-social",
  queue_id: "uuid-of-kesariya-entry",
  youtube_video_id: "BVBWugH_aFE",
  status: "pending",
  issued_at: "2026-06-27T22:31:00"
}
```

Supabase detects this INSERT and pushes it via WebSocket to all clients subscribed to the `playback_commands` table for `koramangala-social`. The YouTube Playback Page is subscribed. It receives the payload in under 500 milliseconds.

**Step 5 — Page Calls the IFrame API**

The JavaScript function that handles the Supabase payload runs:

```
player.loadVideoById({
  videoId: "BVBWugH_aFE",
  startSeconds: 0
});
```

This tells the YouTube IFrame Player: load the video with ID BVBWugH_aFE and start playing from the beginning.

The IFrame Player contacts YouTube's servers, buffers the video, and begins playing. Within 1–2 seconds (on a decent internet connection), Kesariya starts playing through the speakers.

Simultaneously, the page writes back to Supabase:
```
UPDATE playback_commands SET status = "playing", acknowledged_at = NOW()
WHERE id = "this-command-id"
```

This acknowledgement is how your backend knows the page received and acted on the command. If 60 seconds pass and the command is still "pending" (not "playing"), the watchdog task fires an alert on the Venue Dashboard: "Playback tab may not be open."

**Step 6 — onStateChange Fires**

As the video plays, the IFrame Player fires onStateChange events. Your JavaScript logs these. The most important one: when the state changes to 0 (ENDED), meaning the song finished playing naturally.

When onStateChange fires with state = 0, your JavaScript writes to the `playback_events` table in Supabase:

```
{
  venue_id: "koramangala-social",
  queue_id: "uuid-of-kesariya-entry",
  youtube_video_id: "BVBWugH_aFE",
  event_type: "ENDED",
  occurred_at: "2026-06-27T22:34:12"
}
```

Your backend is subscribed to this table (or a Supabase webhook calls your API). When it detects the ENDED event, it:
1. Confirms the ₹25 boost on Kesariya (pending → confirmed, this is now real money)
2. Marks Kesariya as "played" in the queue
3. Promotes the next waiting pool song into the active queue
4. Writes the next `playback_command` for the next song in queue

The cycle repeats.

**Step 7 — onError Fires (failure scenario)**

If YouTube returns an error (video removed, embedding disabled, network issue), onStateChange fires with a specific error code, or onError fires directly. Your JavaScript:
1. Writes a "ERROR" event to `playback_events` with the error code
2. Does NOT try to retry automatically (retrying a broken video in a loop is worse than stopping)
3. Your backend receives the error event and runs the fallback sequence

### Scenario: The Staff Forget to Open This Tab

The queue engine issues a playback command at 10:31pm. It writes the row to `playback_commands`. The Supabase WebSocket push fires. But Tab 2 is not open — the staff forgot to open it during setup, or they accidentally closed it.

No listener receives the command. The command sits in the database with status "pending."

60 seconds later, your backend's watchdog task runs (a Celery task that runs every 60 seconds). It queries: "Are there any playback_commands for active venues that are still pending after more than 60 seconds?" It finds this one. It writes an alert to the `alerts` table. The Venue Dashboard (Tab 1) is subscribed to alerts via WebSocket. It immediately shows a banner:

**"⚠ MUSIC ISSUE: Playback tab may not be open. Check Tab 2."**

The laminated card tells the staff: "If you see this alert, click the pinned 'VQ Playback' tab."

### What the Backend Does For This Interface

The backend does not serve this interface as much as it communicates with it:

| Backend Action | Mechanism | Effect on Playback Page |
|---|---|---|
| Queue engine picks next song | Writes to playback_commands table | Page receives via WebSocket, calls player.loadVideoById() |
| Staff presses Pause | Writes pause event to playback_commands | Page calls player.pauseVideo() |
| Staff presses Resume | Writes resume event | Page calls player.playVideo() |
| Watchdog detects stale command | Writes to alerts table | Dashboard shows alert (Page itself does not act) |
| Error received from page | Page writes to playback_events | Backend cancels boost, advances queue, shows dashboard alert |

---

## 5. Interface 3 — The Venue Dashboard (Laptop Tab 1)

### Who Uses This

One specific person: the staff member responsible for music that evening. In a small bar this might be the bartender. In a larger venue it might be a dedicated floor manager. This person has approximately 30 seconds of attention to give VibeQueue at any given moment. They are serving drinks, managing tables, and dealing with customers. The dashboard must be glanceable.

**Critical design constraint:** Every important action must be completable in one tap. Any control that requires more than two taps is too complex for this context.

### The Physical Setup

Tab 1 (Venue Dashboard) sits on the venue's existing laptop, which is behind the bar or at the host stand. It is open at all times during service. The staff member glances at it between serving drinks. They do not sit in front of it.

### What It Shows

The Venue Dashboard is a single-page application with everything visible at once. No navigation. No menus. No tabs within the dashboard. Everything is on one screen. Think of it like a cockpit instrument panel — the pilot sees everything at once and can reach any control without navigating.

**Zone A — Now Playing (top centre, largest element)**

The biggest text on the screen:

```
NOW PLAYING
────────────────────────────────────────────
Kesariya · Arijit Singh
Requested by TABLE 7
Duration: 3:45 · Playing for: 0:47
────────────────────────────────────────────
[SKIP →]     [⏸ PAUSE ALL]
```

The Skip button removes the current song from the queue (marks it as skipped, cancels any pending boost for it, advances to the next song immediately). The Pause All button freezes the entire system — the queue pauses, guests see a "queue paused" message, no new requests are processed.

**Zone B — Queue Preview (left side, below Now Playing)**

Shows the next 5 songs in queue with their table attributions:

```
NEXT UP
─────────────────────────────────────────
#1  Pasoori · Ali Sethi         Table 2  ▲score 25
#2  Calm Down · Rema            Table 5  ▲score 22
#3  Brown Munde · AP Dhillon    Table 4  ▲score 18
#4  Levitating · Dua Lipa       Table 1  ▲score 0
#5  Butta Bomma                 Table 6  ▲score 0
─────────────────────────────────────────
12 more songs in waiting pool
```

Staff cannot rearrange the queue from here (the algorithm handles ordering). But they can tap on any song to see a context menu with one option: Remove. If a song is inappropriate (staff knows the crowd) they can remove it in one tap.

**Zone C — Active Tables (right side)**

Shows every currently open table:

```
ACTIVE TABLES
────────────────────────────────
TABLE 7    4 guests   ₹40 pending   [Close]  [Flag]
TABLE 2    2 guests   ₹25 pending   [Close]  [Flag]
TABLE 5    6 guests   ₹75 pending   [Close]  [Flag]
────────────────────────────────
[+ OPEN NEW TABLE]
```

"Open New Table" is how the evening starts for each table. Staff tap this, select a table number, the system generates a 6-digit code, and the staff tell the table the code. "Close" opens the billing flow for that table. "Flag" blocks that table's request and boost privileges for 15 minutes.

**Zone D — Tonight's Numbers (bottom, small)**

```
TONIGHT: 8 tables served · ₹2,840 music revenue · 34 songs played · 68% conversion
```

This is the vanity metric strip. It does not require attention — it is there so the venue owner can glance at it and know the evening is working.

**Zone E — Alert Banner (appears only when needed, covers top of screen)**

Red background, large text, one action:

```
⚠ MUSIC ISSUE — Playback tab may not be open
   → Click the pinned "VQ Playback" tab
[DISMISS]
```

Alerts are:
- Playback tab not responding (watchdog triggered)
- YouTube error on a specific video (one song, handled automatically — just informs staff)
- Spend cap reached for a table (purely informational)
- Queue is empty (staff should add a venue playlist or the queue will go silent)

**Zone F — Mode Toggle (small, top right)**

```
MODE: [A: AUTOMATED] / [B: MANUAL]
```

Mode A: everything is automated. Songs play automatically in queue order. The staff just watch.
Mode B: staff confirm each song before it plays. The "Mark as Played" button appears after each song. Staff use this if they want to manually control transitions or if the YouTube IFrame is not working and they are playing songs manually.

### The Mode B Flow (Manual Confirmation)

In Mode B, the backend does not automatically issue playback commands. Instead, it waits. When the queue engine would normally issue a command, it instead writes a "waiting for confirmation" state. Zone A on the dashboard shows:

```
NEXT SONG READY
────────────────────────────────────────────
Kesariya · Arijit Singh  (Table 7, boost ₹25)
────────────────────────────────────────────
[▶ MARK AS PLAYED — START THIS SONG]
```

Staff tap "Mark as Played." This does two things simultaneously:
1. Triggers the backend to confirm the previous song's boosts (as though an ENDED event arrived)
2. Issues the playback command for Kesariya

Mode B is the fallback for the pilot. If the IFrame automation has any issues, Mode B gives the staff manual control without any software dependency breaking. They can run Mode B indefinitely if needed — it just requires one tap per song transition, roughly every 3–4 minutes.

### What the Backend Does For This Interface

| Dashboard Action | Backend Endpoint | What Happens |
|---|---|---|
| Page loads | GET /venues/{id}/dashboard | Returns full state: queue, tables, alerts, tonight's revenue |
| WebSocket connect | WS /venue/{id}/dashboard | Subscribe to live queue updates, alerts, table state changes |
| Open New Table | POST /sessions/open | Create session, generate code, return code to display |
| Close Table / Billing | POST /sessions/{id}/billing | Set session state to "billing", push billing screen to guest phone |
| Skip Song | POST /queue/{id}/skip | Mark skipped, cancel boost, advance queue, issue next command |
| Pause All | POST /playback/pause | Freeze queue, broadcast pause state to all guest phones |
| Resume | POST /playback/resume | Unfreeze queue, issue next playback command |
| Flag Table | POST /sessions/{id}/flag | Block request/boost for 15 minutes |
| Remove Song | DELETE /queue/{id} | Cancel song and its pending boosts, recalculate queue |
| Mode B: Mark as Played | POST /playback/confirm-manual | Confirm previous boosts, issue next command |
| Alerts arrive | (pushed via WebSocket) | Dashboard shows alert banner without refresh |

---

## 6. Interface 4 — The Ambient Display (TV)

### Who Uses This

Technically nobody "uses" it — there are no controls and no interaction. But every customer in the room is the audience. The Ambient Display is the social performance layer of VibeQueue. It is what makes the system feel alive for people who have not even opened their phones yet.

**Analogy:** Think of the Ambient Display as the scoreboard at a cricket match. Nobody "uses" the scoreboard. But everyone in the stadium glances at it. It provides shared context. It creates conversation. It generates excitement. The scoreboard is not the cricket match. It is the shared information layer that makes watching the match together more exciting.

### The Physical Setup

A TV or monitor near the bar, connected to an Android TV Stick (Mi TV Stick or similar). The TV stick runs Chrome browser in full-screen mode showing the Ambient Display URL. Nobody needs to touch this after setup. It connects to the venue's Wi-Fi, loads the page, and runs all evening.

### What It Shows

The Ambient Display is a dark-background, large-text screen designed to be readable from 10 metres away. No small text. No detailed information. Only the things that create conversation:

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  NOW PLAYING                                            │
│  ██████████████████████████████████████                 │
│  KESARIYA                                               │
│  Arijit Singh · Brahmāstra                              │
│  ─────────────────────────────────                      │
│  Requested by  TABLE 7  🎵                              │
│                                                         │
│  ─────────────────────────────────                      │
│  NEXT UP                                                │
│  #1  Pasoori              TABLE 2  ▲25                  │
│  #2  Calm Down            TABLE 5  ▲22                  │
│  #3  Brown Munde          TABLE 4  ▲18                  │
│                                                         │
│  WANT YOUR SONG NEXT? SCAN THE QR ON YOUR TABLE         │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

Every element here serves a social function:

**"Requested by TABLE 7"** — Table 7 gets credit. The group at Table 7 may look up at the screen and notice. Their friends at other tables may congratulate them. Attribution creates ownership. Ownership creates engagement.

**The Next Up section** — Other tables can see that Table 2 is currently winning the queue with a boost score of 25. A table that wants to beat Table 2 and get their song higher will open their phone and boost. The Ambient Display is the motivation engine.

**"Scan the QR on your table"** — The CTA for people who have not joined yet. A customer who has been watching the TV for 5 minutes knows exactly what VibeQueue does. They see songs moving, they see table attributions, they want to participate. This line tells them exactly how.

**The progress bar under the song title** — A visual indicator of how far through the current song the venue is. This is purely aesthetic but creates a sense of "something is always happening."

### What Changes and When

This is the most real-time interface in the system. Every change in the queue is visible here immediately. Specific events that update the display:

- **Song starts playing** — The Now Playing section updates with the new song. The old song leaves. The new song slides in with its artist and table attribution.
- **Queue reorders** — The Next Up section reorders instantly. If Table 5 boosts Calm Down and it jumps from #3 to #1, the display re-orders within half a second. Everyone in the room who is looking at the TV sees it happen.
- **New song enters the queue** — The Next Up list gains a new entry at the bottom.
- **Song removed or skipped** — It disappears from the Next Up list.
- **Queue paused** — The entire display dims slightly and shows "Queue Paused — back soon." The Now Playing info remains.

### What the Backend Does For This Interface

The Ambient Display is entirely read-only. It never sends data to the backend. It only receives.

| Display Need | Mechanism | Update Frequency |
|---|---|---|
| Initial state on page load | GET /playback/status/{venue_id} | Once on load |
| Now Playing updates | Supabase WebSocket on playback_events | Within 500ms of song change |
| Queue order updates | Supabase WebSocket on queue table | Within 500ms of any queue change |
| New song added to queue | Supabase WebSocket on queue table INSERT | Immediate |
| Pause/Resume state | Supabase WebSocket on venue_state table | Immediate |

### The Passive Acquisition Loop

The Ambient Display creates a passive customer acquisition loop. Consider a customer who arrives late and did not see the waiter give out table codes. They sit down, see the TV, and within 60 seconds understand: "That TV shows songs playing and which table requested them. I can apparently do that." They look at the table tent, scan the QR, get the code from the waiter, and join. This entire journey can happen without any staff involvement.

This is the most underrated feature of the Ambient Display. It is not just informational — it is self-service marketing for the product, happening continuously all evening.

---

## 7. How All Four Interfaces Talk To Each Other

Here is a complete map of the communication paths between all four interfaces:

```
                        ┌─────────────────────┐
                        │   SUPABASE (DB)      │
                        │   + Realtime         │
                        └──────────┬──────────┘
                                   │
                    ┌──────────────┼──────────────┐
                    │              │              │
                    ▼              ▼              ▼
            ┌──────────────┐  ┌──────────┐  ┌──────────────┐
            │ Guest Phone  │  │  Venue   │  │  Ambient     │
            │ (Interface 1)│  │ Dashboard│  │  Display TV  │
            │              │  │ (Tab 1)  │  │ (Interface 4)│
            │ READS queue  │  │          │  │              │
            │ WRITES boosts│  │READS queue│  │ READS queue  │
            │ WRITES req.  │  │READS alerts│ │ READS now    │
            └──────────────┘  │WRITES cmds│  │ playing      │
                              └────┬─────┘  └──────────────┘
                                   │
                              reads/writes
                                   │
                              ┌────▼─────────────┐
                              │  YouTube Playback  │
                              │  Page (Tab 2)      │
                              │                    │
                              │  READS playback    │
                              │  commands          │
                              │  WRITES playback   │
                              │  events (ENDED,    │
                              │  ERROR, PLAYING)   │
                              │                    │
                              │  CONTROLS YouTube  │
                              │  IFrame Player     │
                              └────────────────────┘
                                        │
                                controls audio
                                        │
                                ┌───────▼───────┐
                                │   Speakers     │
                                │   (physical)   │
                                └───────────────┘
```

**The key architectural insight:** Nothing talks to anything else directly. Everything communicates through Supabase. The guest phone never talks to the YouTube Playback Page. The Venue Dashboard never talks to the Ambient Display directly. Everything is mediated through the database. When something changes in Supabase, Supabase broadcasts the change to all subscribers.

This is the publish-subscribe pattern. Supabase is the publisher and broker. Every interface is a subscriber that reacts to changes.

**Why this matters for reliability:** If any one interface goes down, the others continue working. If the Ambient Display TV loses power, guests can still request songs. If a guest phone's browser crashes, the queue keeps running. If the Venue Dashboard is accidentally closed, the YouTube Playback Page keeps playing (though staff have no visibility). The system has no single point of failure at the interface layer.

---

## 8. The Complete Data Flow — One Boost, All Four Screens

Let's trace exactly what happens across all four interfaces when Arjun (Table 7) taps "Boost Kesariya ₹25" at 10:22pm.

**T+0ms — Arjun taps Confirm on his phone**

The Guest Interface sends:
```
POST /api/v1/boosts/
Authorization: Bearer eyJ...arjun-table7-token...
{
  "song_id": "uuid-kesariya",
  "amount": 25,
  "queue_id": "uuid-kesariya-queue-entry"
}
```

**T+50ms — Backend receives the request**

FastAPI receives the POST. The auth dependency validates Arjun's JWT. The session dependency confirms Table 7's session is active and not flagged. The rate_limit dependency checks Redis: no recent boosts from Table 7. All checks pass.

**T+80ms — Business logic runs**

boost_service.create_boost() runs:
1. Queries boost_repo.get_session_spend_total("table7-session-uuid") — returns ₹0
2. ₹0 + ₹25 = ₹25, which is less than the ₹150 cap — proceed
3. Inserts a new row into the boosts table: `{session_id, queue_id, amount: 25, status: "pending"}`
4. Calls queue_service.recalculate_queue("koramangala-social")

**T+120ms — Queue recalculates**

queue_service.recalculate_queue() fetches all 8 active queue songs. Applies the scoring formula. Kesariya's new score is 25 (boost) + 1.25 (time decay for 8 minutes) = 26.25. This puts Kesariya at position 3, up from position 7. Bulk-updates position and boost_score columns in Supabase for all 8 rows.

**T+130ms — Supabase detects the database write**

Supabase's Realtime engine detects that rows in the queue table changed for venue `koramangala-social`. It prepares to push the change to all WebSocket subscribers.

**T+140ms — The API returns to Arjun's phone**

FastAPI returns:
```
HTTP 201 Created
{
  "boost_id": "uuid-new-boost",
  "status": "pending",
  "new_queue_position": 3,
  "song_name": "Kesariya",
  "spend_remaining": 125
}
```

**T+140ms — Guest Interface updates (Arjun's phone)**

The Guest Interface receives the 201 response. It updates:
- The "My Songs" section: Kesariya shows "Queue position: 3"
- The "Spend Remaining" indicator: ₹125 remaining
- A brief success toast: "Kesariya boosted to #3!"

**T+150ms — Supabase pushes real-time update**

Supabase Realtime broadcasts the updated queue to all WebSocket subscribers for `koramangala-social`:

*Guest Interface (all phones in the venue):* The queue list animates. Kesariya's card moves from position 7 upward to position 3. The boost score on Kesariya updates to 26.25. This happens on Priya's phone, Rahul's phone, Sneha's phone, and every other guest phone in the room that is currently showing the queue.

*Venue Dashboard (laptop Tab 1):* The Queue Preview section reorders. Position 3 now shows Kesariya with score 26.25 and "TABLE 7" attribution.

*Ambient Display TV:* The Next Up section reorders. Kesariya appears at position 3. Everyone in the bar can see this happen simultaneously.

*YouTube Playback Page (laptop Tab 2):* This interface does not subscribe to queue changes. It only listens for `playback_commands`. So it does not update at this moment. It is still playing whatever the current song is.

**T+160ms — Total elapsed time: 160ms**

All four interfaces reflect the new state. Arjun's boost is visible to everyone. The social moment is complete.

**9 minutes later — T+9:00 — The ENDED Event**

The current song (Brown Munde) finishes. The YouTube IFrame Player fires state = 0 (ENDED). The YouTube Playback Page writes to `playback_events`.

The backend receives the event. It:
1. Confirms all pending boosts for Brown Munde (if any) — marks as "confirmed"
2. Advances the queue: Kesariya is now at position 1, ready to play
3. Writes a new `playback_command` for Kesariya with video ID BVBWugH_aFE

The YouTube Playback Page receives the playback command via WebSocket and calls:
```
player.loadVideoById({ videoId: "BVBWugH_aFE", startSeconds: 0 })
```

Kesariya starts playing. Arjun's ₹25 boost has not yet been confirmed — it gets confirmed when Kesariya's ENDED event fires approximately 3–4 minutes from now.

---

## 9. Critical Analysis — What Can Go Wrong With This Architecture

In keeping with the system prompt's directive to be brutally honest about failure modes, here are the real risks with the YouTube IFrame approach.

### Risk 1: YouTube Changes Its Embed Terms

**Severity: HIGH. Probability: MEDIUM.**

YouTube is a Google product and has changed its API terms multiple times. In 2021 they restricted the ability to use the IFrame API on domains not explicitly registered in Google Cloud Console. In 2023 they changed autoplay behaviour. There is a non-zero probability that YouTube restricts commercial venue usage of the IFrame Player.

**Mitigation for the pilot:** You are using the IFrame Player with a human-controlled account (the venue's YouTube Premium account) in a browser, which is indistinguishable from a person watching YouTube. You are not scraping, not using an automated headless browser, and not violating any current written term. The risk is manageable during a 4-week pilot.

**Long-term mitigation:** The Playback Page architecture is designed to be platform-agnostic. When you switch to JioSaavn or a licensed music API in Phase 3, only the Playback Page changes. The queue engine, billing, and all other interfaces are unchanged.

### Risk 2: The Playback Page Browser Tab Goes to Sleep

**Severity: HIGH. Probability: MEDIUM during pilot.**

Modern browsers aggressively throttle or suspend tabs that are not in focus, especially on laptops running on battery. Chrome's tab sleeping feature can suspend background tabs after a few minutes. If the YouTube Playback Page goes to sleep, it stops receiving Supabase WebSocket messages and stops playing music.

**Mitigation:**
- The venue laptop should be plugged into power (not battery) at all times during service
- Chrome has a tab sleep opt-out: you can mark specific tabs as "always active" in Chrome flags
- The page itself uses the Web Audio API to play a silent audio loop every 30 seconds — this keeps the tab "awake" by making the browser think it is actively playing audio (it is playing 0-volume audio continuously)
- The watchdog (60-second stale command detection) catches this scenario and alerts staff

### Risk 3: Song Ends Abruptly Mid-Room

**Severity: MEDIUM. Probability: LOW.**

If a YouTube video gets an embed restriction applied while it is currently playing, the IFrame Player may stop mid-song. Alternatively, if the venue's internet drops for a few seconds while a video is buffering, the music may stutter or stop.

**Mitigation:** The fallback is always Spotify running silently in Tab 3. The laminated card says "If music stops: click the Spotify tab and unmute." Five seconds of silence followed by five seconds of action. The bar does not go silent for more than 10 seconds in any failure scenario.

### Risk 4: The Guest Interface and the Billing Flow Desync

**Severity: MEDIUM. Probability: LOW with proper implementation.**

The billing flow is triggered when the waiter closes a table. The backend writes a "billing_open" event. The guest phone receives this via WebSocket and shows the billing screen. But what if the guest's phone has a dead WebSocket connection (their phone was locked, they walked outside, bad signal)? They do not see the billing screen. The waiter is waiting at the table.

**Mitigation:** The billing screen is also accessible by the guest at any time through a button on their main interface ("View my tab"). The waiter can read them their total from the Venue Dashboard even if the guest's phone does not show the billing screen. Payment can be processed entirely from the venue side if the guest's phone is unresponsive.

### Risk 5: The Table Code System Creates Friction at Busy Moments

**Severity: MEDIUM. Probability: MEDIUM.**

Imagine a Friday night. The venue is packed. The waiter is juggling 12 tables. Table 7 sits down and nobody gives them the table code because the waiter forgot in the chaos. The table never joins VibeQueue. The boost conversion for that table is zero.

**Mitigation for pilot:** This is an operational problem, not a technical one. The fix is training, not code. The laminated card should list "Opening a new table" as step 1 of the evening shift procedure. The table tent should have a visual reminder: "Ask your waiter for the 6-digit code to request songs."

**Longer term:** Consider whether the 6-digit verbal code step can be replaced entirely in Phase 2. Options: NFC tap on the table tent (no code needed, phone reads the table identity from the tag), or a physical printed code on the table tent that rotates weekly instead of every 90 minutes (lower security, higher adoption). This is a tradeoff between adoption friction and abuse prevention that should be validated with real data from the pilot.

### Risk 6: Negative Reactions / Downvotes Create Social Conflict

**The current model does not include negative reactions/downvotes.** This is the right call. Here is why:

If someone at Table 5 can see that Table 2's song is being downvoted by other tables, two problems emerge:
1. Table 2 is publicly humiliated. The person who requested the song feels attacked. Social conflict at the venue level.
2. Organized downvoting becomes a troll vector. A group at Table 3 can systematically kill every song from Table 2.

Downvoting is the most dangerous feature in any social music system. Every venue that has implemented it (TouchTunes had it early, most jukebox systems tried it) has found that it creates more conflict than it resolves. The correct mechanism is spend-based priority, not negative scoring. If you do not want a song to play, boost a different song above it. This creates positive pressure rather than negative conflict.

**Do not add downvotes. The current model is correct.**

---

## 10. Backend Responsibilities Per Interface

This section is a clean summary of exactly what your FastAPI backend is responsible for serving to each interface. Use this as a reference when building.

### For the Guest Interface

**Authentication:**
- Validate table codes against active sessions
- Issue JWTs for authenticated sessions
- Validate JWTs on every protected endpoint

**Queue Operations:**
- Return full queue state on page load
- Accept new song requests with cooldown enforcement
- Accept boost submissions with spend cap enforcement
- Recalculate queue order after every boost
- Return personalised "my songs" data per session

**Real-time:**
- Supabase handles the push — backend triggers this by writing to the database
- Backend does not need to maintain WebSocket connections itself for guests

**Billing:**
- Return bill preview (confirmed + pending boosts with GST)
- Trigger Razorpay payment order
- Receive and verify Razorpay webhook
- Confirm session as paid

### For the YouTube Playback Page

**Playback Commands:**
- Write playback commands to Supabase when queue advances
- Write pause/resume commands on staff action

**Event Reception:**
- Receive ENDED events and trigger boost confirmation + queue advance
- Receive ERROR events and trigger fallback sequence
- Receive PLAYING confirmations and update watchdog timer

**Watchdog:**
- Celery task every 60 seconds checks stale commands
- Write alert to database if command is stale

### For the Venue Dashboard

**Initial State:**
- Return full venue state: queue, active sessions, tonight's revenue, active alerts

**Table Management:**
- Create new table sessions and generate codes
- Flag/unflag tables
- Open billing for a table

**Queue Control:**
- Skip songs
- Remove songs
- Pause/resume the entire queue

**Alerts:**
- Write to alerts table when watchdog fires, YouTube error occurs, or queue goes empty
- Alerts are pushed to dashboard via Supabase Realtime

**Mode B Confirmation:**
- Accept "mark as played" from staff and trigger the same flow as an ENDED event

### For the Ambient Display

**Nothing.** The Ambient Display sends zero data to the backend. It is entirely read-only. It subscribes to Supabase Realtime channels for the queue and playback events. The backend does not need to write anything special for the Ambient Display — it reads the same data that the dashboard and guest interface read.

This is intentional. The Ambient Display should never require backend support. If the backend goes down temporarily, the Ambient Display shows stale data (the last known state) but does not error. It is the most resilient interface in the system.

---

## Summary: The Mental Model

To summarise the entire system in a paragraph you can hold in your head:

**The backend is the brain.** It applies rules, enforces limits, calculates scores, and writes instructions.

**Supabase is the nervous system.** It stores the brain's decisions and broadcasts them instantly to all extremities.

**The Guest Interface is how customers speak to the brain.** They request, boost, and review their tab.

**The YouTube Playback Page is how the brain controls sound.** The brain writes "play this," the page reads it and presses play on YouTube.

**The Venue Dashboard is how the staff intervene.** They override, pause, skip, and close tables.

**The Ambient Display is how the room knows what is happening.** It shows everyone the result of the brain's decisions in real time.

None of these need each other directly. They all need the brain (backend) and the nervous system (Supabase). Take away any one interface and the others continue. That is the architecture. That is why it is resilient.

---

*VibeQueue Interface Reference · June 2026 · Confidential*
*Written for builders who need to direct the system, not just understand it.*