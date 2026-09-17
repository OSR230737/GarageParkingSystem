from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import get_db
from app.models import ParkingSpot, User
from app.schemas import SpotCreate, SpotListResponse, SpotResponse

router = APIRouter(tags=["spots"])
VALID_SPOT_TYPES = {"compact", "standard", "ev"}
SORTABLE_FIELDS = {
    "id": ParkingSpot.id,
    "spot_number": ParkingSpot.spot_number,
    "spot_type": ParkingSpot.spot_type,
    "floor_level": ParkingSpot.floor_level,
    "is_occupied": ParkingSpot.is_occupied,
}


@router.post("/spots", response_model=SpotResponse, status_code=status.HTTP_201_CREATED)
def create_spot(
    spot_data: SpotCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> ParkingSpot:
    if spot_data.spot_type not in VALID_SPOT_TYPES:
        raise HTTPException(status_code=400, detail="Invalid spot type")

    spot = ParkingSpot(**spot_data.model_dump())
    db.add(spot)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Spot number already exists")
    db.refresh(spot)
    return spot


@router.get("/spots", response_model=SpotListResponse)
def list_spots(
    spot_type: str | None = None,
    is_occupied: bool | None = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1),
    sort_by: str = "spot_number",
    db: Session = Depends(get_db),
) -> dict[str, object]:
    if spot_type is not None and spot_type not in VALID_SPOT_TYPES:
        raise HTTPException(status_code=400, detail="Invalid spot type")
    sort_column = SORTABLE_FIELDS.get(sort_by)
    if sort_column is None:
        raise HTTPException(status_code=400, detail="Invalid sort field")

    filters = []
    if spot_type is not None:
        filters.append(ParkingSpot.spot_type == spot_type)
    if is_occupied is not None:
        filters.append(ParkingSpot.is_occupied == is_occupied)

    total = db.scalar(select(func.count(ParkingSpot.id)).where(*filters)) or 0
    spots = db.scalars(
        select(ParkingSpot)
        .where(*filters)
        .order_by(sort_column)
        .offset(skip)
        .limit(limit)
    ).all()
    return {
        "data": list(spots),
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/spots/ev/available")
def available_ev_spots(db: Session = Depends(get_db)) -> dict[str, int]:
    count = db.scalar(
        select(func.count(ParkingSpot.id)).where(
            ParkingSpot.spot_type == "ev",
            ParkingSpot.is_occupied.is_(False),
        )
    ) or 0
    return {"available_ev_spots": count}
