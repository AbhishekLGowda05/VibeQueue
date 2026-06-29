"""
tests/load/locustfile.py

Load test simulating peak Friday night traffic.
Run with: locust -f tests/load/locustfile.py --host=http://localhost:8000

Target before pilot go-live:
  - 200 concurrent guests across 50 tables across 2 venues
  - 1000 WebSocket connections sustained
  - p99 response time < 200ms for queue reads
  - p99 response time < 500ms for boost writes

To run a quick smoke test:
  locust -f tests/load/locustfile.py --host=http://localhost:8000
         --users 50 --spawn-rate 5 --run-time 60s --headless
"""
from locust import HttpUser, between, task


class GuestUser(HttpUser):
    """Simulates a guest scanning QR, joining, searching, requesting, boosting."""
    wait_time = between(2, 8)   # Realistic think time between actions

    def on_start(self):
        """Called once per simulated user on startup."""
        self.venue_slug = "koramangala-social"
        self.session_token = None
        self.queue_entry_id = None
        self._join_session()

    def _join_session(self):
        """Simulate guest entering table code."""
        response = self.client.post(
            f"/api/v1/sessions/join?venue_slug={self.venue_slug}",
            json={"table_code": "482176"},
            name="/sessions/join",
        )
        if response.status_code == 200:
            self.session_token = response.json().get("access_token")

    @task(5)
    def search_songs(self):
        """Most common action — browsing/searching songs."""
        if not self.session_token:
            return
        self.client.get(
            "/api/v1/songs/search?q=bollywood",
            headers={"Authorization": f"Bearer {self.session_token}"},
            name="/songs/search",
        )

    @task(3)
    def get_queue(self):
        """Read current queue state (before WebSocket, or on reconnect)."""
        import uuid
        venue_id = "00000000-0000-0000-0000-000000000001"  # Replace with real ID
        self.client.get(
            f"/api/v1/queue/{venue_id}",
            name="/queue/{venue_id}",
        )

    @task(1)
    def apply_boost(self):
        """Least frequent but highest value action."""
        if not self.session_token or not self.queue_entry_id:
            return
        self.client.post(
            "/api/v1/boosts/",
            json={"queue_entry_id": self.queue_entry_id, "amount_paise": 2500},
            headers={"Authorization": f"Bearer {self.session_token}"},
            name="/boosts/",
        )

    @task(2)
    def check_boost_tiers(self):
        self.client.get("/api/v1/boosts/tiers", name="/boosts/tiers")
