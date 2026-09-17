from datetime import datetime
from math import ceil

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.auth import get_current_user
from app.db import get_db
from app.fees import calculate_fee
from app.models import ParkingSession, ParkingSpot, User
from app.rate_card import get_active_rate_card
from app.schemas import (
    CheckInRequest,
    CheckoutResponse,
    ParkingSessionListResponse,
    ParkingSessionResponse,
    TransferRequest,
)

router = APIRouter(tags=["sessions"])
VALID_VEHICLE_TYPES = {"regular", "ev"}
SORTABLE_FIELDS = {
    "id": ParkingSession.id,
    "plate_number": ParkingSession.plate_number,
    "vehicle_type": ParkingSession.vehicle_type,
    "checked_in_at": ParkingSession.checked_in_at,
    "checked_out_at": ParkingSession.checked_out_at,
    "fee_charged": ParkingSession.fee_charged,
}


@router.post(
    "/checkin",
    response_model=ParkingSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
def check_in(
    check_in_data: CheckInRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ParkingSession:
    if check_in_data.vehicle_type not in VALID_VEHICLE_TYPES:
        raise HTTPException(status_code=400, detail="Invalid vehicle type")

    spot = db.get(ParkingSpot, check_in_data.spot_id)
    if spot is None:
        raise HTTPException(status_code=404, detail="Parking spot not found")
    if check_in_data.vehicle_type == "ev" and spot.spot_type != "ev":
        raise HTTPException(status_code=400, detail="EV vehicle must use an EV spot")
    if spot.is_occupied:
        raise HTTPException(status_code=400, detail="Spot is already occupied")

    active_session = db.scalar(
        select(ParkingSession).where(
            ParkingSession.plate_number == check_in_data.plate_number,
            ParkingSession.checked_out_at.is_(None),
        )
    )
    if active_session is not None:
        raise HTTPException(status_code=400, detail="Vehicle is already checked in")

    parking_session = ParkingSession(
        spot_id=spot.id,
        plate_number=check_in_data.plate_number,
        vehicle_type=check_in_data.vehicle_type,
        checked_in_by=user.id,
    )
    spot.is_occupied = True
    db.add(parking_session)
    db.commit()
    db.refresh(parking_session)
    return parking_session


@router.post("/checkout/{session_id}", response_model=CheckoutResponse)
def check_out(
    session_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> dict[str, object]:
    parking_session = db.scalar(
        select(ParkingSession)
        .options(joinedload(ParkingSession.spot))
        .where(ParkingSession.id == session_id)
    )
    if parking_session is None:
        raise HTTPException(status_code=404, detail="Parking session not found")
    if parking_session.checked_out_at is not None:
        raise HTTPException(status_code=400, detail="Session is already checked out")

    checked_out_at = datetime.utcnow()
    duration_hours = max(
        1,
        ceil(
            (checked_out_at - parking_session.checked_in_at).total_seconds() / 3600
        ),
    )
    fee_charged = calculate_fee(
        parking_session.checked_in_at,
        checked_out_at,
        parking_session.spot.spot_type,
        parking_session.vehicle_type,
        get_active_rate_card(),
    )
    parking_session.checked_out_at = checked_out_at
    parking_session.fee_charged = fee_charged
    parking_session.spot.is_occupied = False
    db.commit()

    return {
        "session_id": parking_session.id,
        "plate_number": parking_session.plate_number,
        "fee_charged": fee_charged,
        "checked_in_at": parking_session.checked_in_at,
        "checked_out_at": checked_out_at,
        "duration_hours": duration_hours,
    }


@router.post("/sessions/{session_id}/transfer", response_model=ParkingSessionResponse)
def transfer_session(
    session_id: int,
    transfer_data: TransferRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> ParkingSession:
    parking_session = db.get(ParkingSession, session_id)
    if parking_session is None:
        raise HTTPException(status_code=404, detail="Parking session not found")
    if parking_session.checked_out_at is not None:
        raise HTTPException(status_code=400, detail="Session is already checked out")
    if parking_session.plate_number == transfer_data.plate_number:
        raise HTTPException(status_code=400, detail="New plate must be different")

    active_session = db.scalar(
        select(ParkingSession).where(
            ParkingSession.plate_number == transfer_data.plate_number,
            ParkingSession.checked_out_at.is_(None),
            ParkingSession.id != session_id,
        )
    )
    if active_session is not None:
        raise HTTPException(
            status_code=400,
            detail="New plate already has an active session",
        )

    parking_session.plate_number = transfer_data.plate_number
    db.commit()
    db.refresh(parking_session)
    return parking_session


@router.get("/sessions", response_model=ParkingSessionListResponse)
def list_active_sessions(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1),
    sort_by: str = "checked_in_at",
    order: str = "desc",
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> dict[str, object]:
    sort_column = SORTABLE_FIELDS.get(sort_by)
    if sort_column is None:
        raise HTTPException(status_code=400, detail="Invalid sort field")
    if order not in {"asc", "desc"}:
        raise HTTPException(status_code=400, detail="Order must be asc or desc")

    active_filter = ParkingSession.checked_out_at.is_(None)
    total = db.scalar(
        select(func.count(ParkingSession.id)).where(active_filter)
    ) or 0
    ordered_column = sort_column.asc() if order == "asc" else sort_column.desc()
    sessions = db.scalars(
        select(ParkingSession)
        .where(active_filter)
        .order_by(ordered_column)
        .offset(skip)
        .limit(limit)
    ).all()
    return {
        "data": list(sessions),
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/search")
def search_sessions(
    plate: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[dict[str, object]]:
    sessions = db.scalars(
        select(ParkingSession)
        .options(joinedload(ParkingSession.spot))
        .where(ParkingSession.plate_number.ilike(f"%{plate}%"))
        .order_by(ParkingSession.checked_in_at.desc())
    ).all()
    return [
        {
            "session_id": parking_session.id,
            "plate_number": parking_session.plate_number,
            "vehicle_type": parking_session.vehicle_type,
            "checked_in_at": parking_session.checked_in_at,
            "checked_out_at": parking_session.checked_out_at,
            "fee_charged": parking_session.fee_charged,
            "spot": {
                "id": parking_session.spot.id,
                "spot_number": parking_session.spot.spot_number,
                "spot_type": parking_session.spot.spot_type,
                "floor_level": parking_session.spot.floor_level,
            },
        }
        for parking_session in sessions
    ]
