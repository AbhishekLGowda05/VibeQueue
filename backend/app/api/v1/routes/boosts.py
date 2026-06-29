"""
app/api/v1/routes/boosts.py

Boost endpoints — guests pay to increase a song's priority score.

POST /boosts       — apply a boost to a queue entry
GET  /boosts/tiers — returns the three fixed boost tiers shown in the UI
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies.session import get_guest_session
from app.core.database import get_db
from app.models.session import TableSession
from app.repositories.boost_repo import BoostRepository
from app.repositories.queue_repo import QueueRepository
from app.repositories.session_repo import SessionRepository
from app.schemas.boost import BoostCreate, BoostResponse, BoostTier
from app.services.queue_engine import QueueEngine

router = APIRouter()

# The three fixed boost tiers. These are the only valid amounts.
BOOST_TIERS = [
    BoostTier(label="Small Boost", score_increase=15, amount_paise=1500, amount_display="₹15"),
    BoostTier(label="Medium Boost", score_increase=25, amount_paise=2500, amount_display="₹25"),
    BoostTier(label="Priority Boost", score_increase=35, amount_paise=3500, amount_display="₹35"),
]
VALID_AMOUNTS = {tier.amount_paise for tier in BOOST_TIERS}


@router.get("/tiers", response_model=list[BoostTier])
async def get_boost_tiers():
    """
    Returns the three fixed boost options.
    Frontend renders these as the three buttons the guest taps.
    """
    return BOOST_TIERS


@router.post("/", response_model=BoostResponse, status_code=201)
async def apply_boost(
    payload: BoostCreate,
    guest_session: TableSession = Depends(get_guest_session),
    db: AsyncSession = Depends(get_db),
):
    """
    Guest applies a paid boost to a song in the active queue.

    Validations:
      - Amount must be one of the three fixed tiers
      - Song must be in active queue (not waiting pool)
      - Table spend cap must not be exceeded

    The boost is created as PENDING — it becomes confirmed (billable)
    only when the ENDED playback event fires for this song.
    """
    if payload.amount_paise not in VALID_AMOUNTS:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_BOOST_AMOUNT",
                "message": f"Boost amount must be one of: {sorted(VALID_AMOUNTS)} paise",
            },
        )

    engine = QueueEngine(
        queue_repo=QueueRepository(db),
        boost_repo=BoostRepository(db),
        session_repo=SessionRepository(db),
    )

    boost = await engine.apply_boost(
        venue_id=guest_session.venue_id,
        session_id=guest_session.id,
        queue_entry_id=payload.queue_entry_id,
        amount_paise=payload.amount_paise,
    )

    return BoostResponse(
        id=boost.id,
        queue_entry_id=boost.queue_entry_id,
        amount_paise=boost.amount_paise,
        status=boost.status,
        created_at=boost.created_at,
    )
