import csv

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.auth import get_current_user
from app.models import User
from app.rate_card import load_rate_card, set_active_rate_card

router = APIRouter(prefix="/admin/rates", tags=["admin rates"])


@router.post("/import")
async def import_rates(
    file: UploadFile = File(...),
    _: User = Depends(get_current_user),
) -> dict[str, object]:
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="A CSV file is required")

    try:
        contents = await file.read()
        rate_card = load_rate_card(contents.decode("utf-8-sig"))
    except (UnicodeDecodeError, csv.Error):
        raise HTTPException(status_code=400, detail="Could not read the CSV file")

    if not rate_card:
        raise HTTPException(status_code=400, detail="CSV contains no valid rate rows")

    set_active_rate_card(rate_card)
    return {
        "message": "Rates imported successfully",
        "rates": rate_card,
        "rate_count": len(rate_card),
    }
