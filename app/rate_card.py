import csv
import io
from collections.abc import Iterable
from typing import TextIO

VALID_SPOT_TYPES = {"compact", "standard", "ev"}
RATE_FIELDS = ("first_hour", "additional_hour", "daily_cap", "ev_surcharge")
ACTIVE_RATE_CARD: dict[str, dict[str, float]] = {}


def _clean_price(value: str | None) -> float | None:
    if value is None:
        return None
    cleaned = value.strip().replace("$", "").replace(",", "")
    try:
        price = float(cleaned)
    except (TypeError, ValueError):
        return None
    return price if price >= 0 else None


def clean_rate_card(rows: Iterable[dict[str, str | None]]) -> dict[str, dict[str, float]]:
    cleaned_rates: dict[str, dict[str, float]] = {}

    for row in rows:
        normalized_row = {
            (key or "").strip().lower().replace(" ", "_"): (value or "")
            for key, value in row.items()
        }
        spot_type = normalized_row.get("spot_type", "").strip().lower()
        if spot_type not in VALID_SPOT_TYPES or spot_type in cleaned_rates:
            continue

        prices = {
            field: _clean_price(normalized_row.get(field))
            for field in RATE_FIELDS
        }
        if any(price is None for price in prices.values()):
            continue

        cleaned_rates[spot_type] = {
            field: price for field, price in prices.items() if price is not None
        }

    return cleaned_rates


def load_rate_card(source: TextIO | str) -> dict[str, dict[str, float]]:
    if isinstance(source, str):
        source = io.StringIO(source)
    return clean_rate_card(csv.DictReader(source))


def set_active_rate_card(rate_card: dict[str, dict[str, float]]) -> None:
    ACTIVE_RATE_CARD.clear()
    ACTIVE_RATE_CARD.update(rate_card)


def get_active_rate_card() -> dict[str, dict[str, float]]:
    return ACTIVE_RATE_CARD.copy()
