from datetime import datetime, timedelta
from math import ceil


def calculate_fee(
    checked_in_at: datetime,
    checked_out_at: datetime,
    spot_type: str,
    vehicle_type: str,
) -> float:
    hours = max(1, ceil((checked_out_at - checked_in_at).total_seconds() / 3600))
    fee = 5.00 + (hours - 1) * 3.00

    if spot_type == "ev" and vehicle_type == "ev":
        fee += hours * 2.00

    return float(min(fee, 20.00))


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
