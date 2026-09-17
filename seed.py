from sqlalchemy import select

from app.auth import hash_password
from app.db import SessionLocal, create_tables
from app.models import ParkingSpot, User


SPOTS = (
    [(str(number), "standard", 1) for number in range(101, 109)]
    + [(str(number), "compact", 1) for number in range(109, 113)]
    + [(str(number), "standard", 2) for number in range(201, 208)]
    + [(str(number), "compact", 2) for number in range(208, 211)]
    + [(str(number), "ev", 3) for number in range(301, 307)]
    + [(str(number), "compact", 3) for number in range(307, 313)]
)


def seed() -> None:
    create_tables()
    db = SessionLocal()
    try:
        admin = db.scalar(select(User).where(User.username == "admin"))
        if admin is None:
            db.add(
                User(
                    username="admin",
                    email="admin@parksmart.com",
                    hashed_password=hash_password("admin123"),
                )
            )
            print("Created user: admin")
        else:
            print("Skipped existing user: admin")

        created_spots = 0
        for spot_number, spot_type, floor_level in SPOTS:
            existing_spot = db.scalar(
                select(ParkingSpot).where(ParkingSpot.spot_number == spot_number)
            )
            if existing_spot is not None:
                continue
            db.add(
                ParkingSpot(
                    spot_number=spot_number,
                    spot_type=spot_type,
                    floor_level=floor_level,
                )
            )
            created_spots += 1

        db.commit()
        print(f"Created spots: {created_spots}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
