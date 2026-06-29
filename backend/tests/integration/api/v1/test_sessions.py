"""tests/integration/api/v1/test_sessions.py"""
import pytest
from httpx import AsyncClient


class TestGuestJoin:
    async def test_join_with_valid_code_returns_token(self, client: AsyncClient):
        """Happy path: guest enters valid table code and receives access token."""
        # Seed: create venue + open table session in DB
        # Then: POST /sessions/join with correct table code
        # Assert: 200, access_token present, expires_at present
        pass   # Implement after seed fixtures are built

    async def test_join_with_invalid_code_returns_401(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/sessions/join?venue_slug=test-venue",
            json={"table_code": "000000"},
        )
        assert response.status_code == 401
        assert response.json()["detail"]["code"] == "INVALID_TABLE_CODE"

    async def test_join_with_expired_session_returns_401(self, client: AsyncClient):
        """Expired table codes must be rejected even if the code itself is valid."""
        pass
