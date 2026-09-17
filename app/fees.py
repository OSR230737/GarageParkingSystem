from datetime import datetime, timedelta
from math import ceil

DEFAULT_RATE = {
    "first_hour": 5.00,
    "additional_hour": 3.00,
    "daily_cap": 20.00,
    "ev_surcharge": 2.00,
}


def calculate_fee(
    checked_in_at: datetime,
    checked_out_at: datetime,
    spot_type: str,
    vehicle_type: str,
    rate_card: dict[str, dict[str, float]] | None = None,
) -> float:
    hours = max(1, ceil((checked_out_at - checked_in_at).total_seconds() / 3600))
    rates = (rate_card or {}).get(spot_type.lower(), DEFAULT_RATE)
    fee = rates["first_hour"] + (hours - 1) * rates["additional_hour"]

    if spot_type.lower() == "ev" and vehicle_type.lower() == "ev":
        fee += hours * rates["ev_surcharge"]

    return float(min(fee, rates["daily_cap"]))


if __name__ == "__main__":
    start = datetime(2026, 1, 1, 8, 0)
    cases = [
        ("30 min, standard, regular", start, start + timedelta(minutes=30), "standard", "regular"),
        ("1hr 10min, standard, regular", start, start + timedelta(hours=1, minutes=10), "standard", "regular"),
        ("10 hrs, standard, regular", start, start + timedelta(hours=10), "standard", "regular"),
        ("2 hrs, ev, ev", start, start + timedelta(hours=2), "ev", "ev"),
        ("9 hrs, ev, ev", start, start + timedelta(hours=9), "ev", "ev"),
    ]

    for description, checked_in_at, checked_out_at, spot_type, vehicle_type in cases:
        fee = calculate_fee(checked_in_at, checked_out_at, spot_type, vehicle_type)
        print(f"{description} -> ${fee:.2f}")
