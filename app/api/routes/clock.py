from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.clock import checkout_overdue_sessions
from app.db import get_db
from app.models import User

router = APIRouter(tags=["clock"])


@router.post("/clock")
def run_clock(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> dict[str, object]:
    checked_out = checkout_overdue_sessions(db)
    return {
        "checked_out_count": len(checked_out),
        "sessions": checked_out,
    }
