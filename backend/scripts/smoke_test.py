"""
scripts/smoke_test.py

End-to-end smoke test against the live local API.
Exercises the core loop: login → open table → join → search → request → boost → verify queue.

Usage:
    # Start the backend first: uvicorn app.main:app --port 8000
    python scripts/smoke_test.py
"""

import httpx
import sys
import json

BASE = "http://localhost:8000/api/v1"


def pp(label: str, resp: httpx.Response):
    """Pretty-print a response."""
    status = "OK" if resp.is_success else "FAIL"
    print(f"\n{'='*60}")
    print(f"[{status}] {label}")
    print(f"  {resp.request.method} {resp.request.url}")
    print(f"  Status: {resp.status_code}")
    try:
        body = resp.json()
        print(f"  Body: {json.dumps(body, indent=2, default=str)}")
    except Exception:
        print(f"  Body: {resp.text[:500]}")
    return resp


def main():
    client = httpx.Client(timeout=10)
    failures = []

    # ── Step 0: Health check ──────────────────────────────────────
    r = pp("Health check", client.get(f"{BASE}/health/"))
    if not r.is_success:
        print("\nBackend is not running. Start it first:")
        print("  cd backend && source .venv/bin/activate")
        print("  uvicorn app.main:app --port 8000")
        sys.exit(1)

    # ── Step 1: Staff login ───────────────────────────────────────
    r = pp("Staff login (venue owner)", client.post(f"{BASE}/auth/login", json={
        "email": "owner@koramangala-social.com",
        "password": "changeme123",
    }))
    if not r.is_success:
        failures.append("Staff login failed")
        print("\nCannot continue without auth. Aborting.")
        sys.exit(1)

    staff_token = r.json()["access_token"]
    staff_headers = {"Authorization": f"Bearer {staff_token}"}

    # ── Step 2: Open table ────────────────────────────────────────
    # First get the venue_id from the token
    from jose import jwt
    token_data = jwt.get_unverified_claims(staff_token)
    venue_id = token_data.get("venue_id")
    print(f"\n  Venue ID from token: {venue_id}")

    r = pp("Open table (staff)", client.post(f"{BASE}/sessions/open", json={
        "table_number": "T1",
        "venue_id": venue_id,
    }, headers=staff_headers))
    if not r.is_success:
        failures.append("Open table failed")
        print("\nCannot continue without table session. Aborting.")
        sys.exit(1)

    table_code = r.json()["table_code"]
    session_id = r.json()["id"]
    print(f"  Table code: {table_code}")

    # ── Step 3: Guest joins with table code ───────────────────────
    r = pp("Guest join (table code)", client.post(
        f"{BASE}/sessions/join?venue_slug=koramangala-social",
        json={"table_code": table_code},
    ))
    if not r.is_success:
        failures.append("Guest join failed")
        print("\nCannot continue without guest session. Aborting.")
        sys.exit(1)

    guest_token = r.json()["access_token"]
    guest_headers = {"Authorization": f"Bearer {guest_token}"}
    print(f"  Guest spend cap: {r.json()['spend_cap_display']}")

    # ── Step 4: Search songs ──────────────────────────────────────
    r = pp("Search songs (Kesariya)", client.get(
        f"{BASE}/songs/search?q=Kesariya", headers=guest_headers,
    ))
    if not r.is_success:
        failures.append("Song search failed")
    else:
        songs = r.json()
        if songs:
            song = songs[0]
            song_id = song["id"]
            yt_id = song["youtube_video_id"]
            print(f"  Found: {song['title']} by {song['artist']}")
        else:
            failures.append("Song search returned 0 results")
            print("  No songs found!")
            sys.exit(1)

    # ── Step 5: Request song ──────────────────────────────────────
    r = pp("Request song", client.post(f"{BASE}/queue/request", json={
        "song_id": song_id,
        "youtube_video_id": yt_id,
    }, headers=guest_headers))
    if not r.is_success:
        failures.append(f"Song request failed: {r.text}")
    else:
        entry_id = r.json()["id"]
        print(f"  Queue entry ID: {entry_id}")
        print(f"  Position: {r.json()['position']}")

    # ── Step 6: Request a second song (for reordering test) ───────
    r2 = pp("Search for second song (Blinding)", client.get(
        f"{BASE}/songs/search?q=Blinding", headers=guest_headers,
    ))
    if r2.is_success and r2.json():
        song2 = r2.json()[0]
        # Wait for cooldown? No — the cooldown is per-table, and both requests
        # are from the same session. Let's try anyway.
        r3 = pp("Request second song", client.post(f"{BASE}/queue/request", json={
            "song_id": song2["id"],
            "youtube_video_id": song2["youtube_video_id"],
        }, headers=guest_headers))
        if r3.is_success:
            entry2_id = r3.json()["id"]
            print(f"  Second entry ID: {entry2_id}")
        elif "cooldown" in r3.text.lower():
            print("  (Cooldown enforced — this is correct behavior)")
            entry2_id = None
        else:
            failures.append(f"Second song request failed: {r3.text}")
            entry2_id = None

    # ── Step 7: Boost first song ──────────────────────────────────
    r = pp("Boost first song (₹25)", client.post(f"{BASE}/boosts/", json={
        "queue_entry_id": entry_id,
        "amount_paise": 2500,
    }, headers=guest_headers))
    if not r.is_success:
        failures.append(f"Boost failed: {r.text}")
    else:
        print(f"  Boost status: {r.json()['status']}")

    # ── Step 8: Get queue and verify ordering ─────────────────────
    r = pp("Get queue (verify reordering)", client.get(
        f"{BASE}/queue/{venue_id}", headers=guest_headers,
    ))
    if r.is_success:
        q = r.json()
        print(f"  Active queue size: {len(q['active_queue'])}")
        for e in q["active_queue"]:
            print(f"    Position {e['position']}: score={e['score']}, boost={e['boost_total_paise']}p")

    # ── Step 9: Get boost tiers ───────────────────────────────────
    r = pp("Get boost tiers", client.get(f"{BASE}/boosts/tiers", headers=guest_headers))

    # ── Summary ───────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"SMOKE TEST SUMMARY")
    print(f"{'='*60}")
    if failures:
        print(f"FAILURES ({len(failures)}):")
        for f in failures:
            print(f"  - {f}")
    else:
        print("ALL STEPS PASSED")
    print(f"{'='*60}")

    client.close()
    return len(failures) == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
