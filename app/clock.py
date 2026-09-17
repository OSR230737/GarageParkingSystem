from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.fees import calculate_fee
from app.models import ParkingSession
from app.rate_card import get_active_rate_card


OVERDUE_AFTER = timedelta(hours=24)


def checkout_overdue_sessions(
    db: Session,
    now: datetime | None = None,
) -> list[dict[str, object]]:
    checked_out_at = now or datetime.utcnow()
    cutoff = checked_out_at - OVERDUE_AFTER
    sessions = db.scalars(
        select(ParkingSession)
        .options(joinedload(ParkingSession.spot))
        .where(
            ParkingSession.checked_out_at.is_(None),
            ParkingSession.checked_in_at <= cutoff,
        )
    ).all()

    checked_out = []
    rate_card = get_active_rate_card()
    for parking_session in sessions:
        fee_charged = calculate_fee(
            parking_session.checked_in_at,
            checked_out_at,
            parking_session.spot.spot_type,
            parking_session.vehicle_type,
            rate_card,
        )
        parking_session.checked_out_at = checked_out_at
        parking_session.fee_charged = fee_charged
        parking_session.spot.is_occupied = False
        checked_out.append(
            {
                "session_id": parking_session.id,
                "plate_number": parking_session.plate_number,
                "fee_charged": fee_charged,
                "checked_out_at": checked_out_at,
            }
        )

    if sessions:
        db.commit()

    return checked_out
