"""RLS policies, Realtime publication, payment idempotency index

Revision ID: a1b2c3d4e5f6
Revises: 543212affe53
Create Date: 2026-08-24 16:00:00.000000

Security migration for pilot launch:
- Enables RLS on all 10 data tables
- Grants anon SELECT-only on 5 Realtime tables
- Adds Realtime publication for live-update tables
- Adds unique partial index on payments.razorpay_payment_id for webhook idempotency
"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "543212affe53"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Enable Row-Level Security on all data tables ─────────────────
    # With RLS enabled and no policy, access is denied by default.
    # The backend connects as the postgres user which bypasses RLS.
    # The frontend uses the anon key — only SELECT policies below apply.
    op.execute("ALTER TABLE venues ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE users ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE songs ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE table_sessions ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE queue_entries ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE boosts ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE payments ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE playback_commands ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE playback_events ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY")

    # ── Anon role: SELECT-only on Realtime tables ────────────────────
    # These are the 5 tables the frontend subscribes to via Supabase
    # Realtime (anon key). No INSERT/UPDATE/DELETE — all writes go
    # through the FastAPI backend (postgres user, bypasses RLS).
    op.execute("""
        CREATE POLICY "anon_select_queue_entries" ON queue_entries
        FOR SELECT TO anon USING (true)
    """)
    op.execute("""
        CREATE POLICY "anon_select_table_sessions" ON table_sessions
        FOR SELECT TO anon USING (true)
    """)
    op.execute("""
        CREATE POLICY "anon_select_boosts" ON boosts
        FOR SELECT TO anon USING (true)
    """)
    op.execute("""
        CREATE POLICY "anon_select_playback_commands" ON playback_commands
        FOR SELECT TO anon USING (true)
    """)
    op.execute("""
        CREATE POLICY "anon_select_playback_events" ON playback_events
        FOR SELECT TO anon USING (true)
    """)

    # No policies on: venues, users, songs, payments, audit_logs
    # = anon has ZERO access to those tables (RLS enabled + no policy = deny all)

    # ── Enable Realtime on specific tables only ──────────────────────
    # Only the 5 tables that need client-side live updates.
    # NOT enabled on: users, venues, songs, payments, audit_logs.
    op.execute("ALTER PUBLICATION supabase_realtime ADD TABLE queue_entries")
    op.execute("ALTER PUBLICATION supabase_realtime ADD TABLE table_sessions")
    op.execute("ALTER PUBLICATION supabase_realtime ADD TABLE boosts")
    op.execute("ALTER PUBLICATION supabase_realtime ADD TABLE playback_commands")
    op.execute("ALTER PUBLICATION supabase_realtime ADD TABLE playback_events")

    # ── Payment idempotency index ────────────────────────────────────
    # Prevents duplicate webhook processing for the same Razorpay payment.
    # Partial index: only non-NULL values (payments start with NULL payment_id).
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS ix_payments_razorpay_payment_id
        ON payments(razorpay_payment_id)
        WHERE razorpay_payment_id IS NOT NULL
    """)


def downgrade() -> None:
    # ── Remove payment idempotency index ─────────────────────────────
    op.execute("DROP INDEX IF EXISTS ix_payments_razorpay_payment_id")

    # ── Remove Realtime publication ──────────────────────────────────
    op.execute("ALTER PUBLICATION supabase_realtime DROP TABLE IF EXISTS queue_entries")
    op.execute("ALTER PUBLICATION supabase_realtime DROP TABLE IF EXISTS table_sessions")
    op.execute("ALTER PUBLICATION supabase_realtime DROP TABLE IF EXISTS boosts")
    op.execute("ALTER PUBLICATION supabase_realtime DROP TABLE IF EXISTS playback_commands")
    op.execute("ALTER PUBLICATION supabase_realtime DROP TABLE IF EXISTS playback_events")

    # ── Drop RLS policies ────────────────────────────────────────────
    op.execute("DROP POLICY IF EXISTS anon_select_queue_entries ON queue_entries")
    op.execute("DROP POLICY IF EXISTS anon_select_table_sessions ON table_sessions")
    op.execute("DROP POLICY IF EXISTS anon_select_boosts ON boosts")
    op.execute("DROP POLICY IF EXISTS anon_select_playback_commands ON playback_commands")
    op.execute("DROP POLICY IF EXISTS anon_select_playback_events ON playback_events")

    # ── Disable RLS ──────────────────────────────────────────────────
    op.execute("ALTER TABLE venues DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE users DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE songs DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE table_sessions DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE queue_entries DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE boosts DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE payments DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE playback_commands DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE playback_events DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE audit_logs DISABLE ROW LEVEL SECURITY")
