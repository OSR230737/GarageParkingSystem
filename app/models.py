from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )


class ParkingSpot(Base):
    __tablename__ = "parking_spots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    spot_number: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    spot_type: Mapped[str] = mapped_column(String, nullable=False)
    floor_level: Mapped[int] = mapped_column(Integer, nullable=False)
    is_occupied: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )


class ParkingSession(Base):
    __tablename__ = "parking_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    spot_id: Mapped[int] = mapped_column(
        ForeignKey("parking_spots.id"), nullable=False
    )
    plate_number: Mapped[str] = mapped_column(String, nullable=False)
    vehicle_type: Mapped[str] = mapped_column(String, nullable=False)
    checked_in_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    checked_out_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    fee_charged: Mapped[float] = mapped_column(Float, nullable=True)
    checked_in_by: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )

    spot: Mapped[ParkingSpot] = relationship()
