import unittest
from datetime import datetime
from unittest.mock import Mock, patch

from sqlalchemy import create_engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app import db
from app.db import Base
from app.models import ParkingSession, ParkingSpot, User


class DatabaseDependencyTests(unittest.TestCase):
    def test_get_db_yields_and_closes_session(self) -> None:
        session = Mock(spec=Session)

        with patch.object(db, "SessionLocal", return_value=session):
            database_session = db.get_db()
            self.assertIs(next(database_session), session)
            database_session.close()

        session.close.assert_called_once_with()


class ModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(cls.engine)
        cls.SessionLocal = sessionmaker(bind=cls.engine)

    @classmethod
    def tearDownClass(cls) -> None:
        Base.metadata.drop_all(cls.engine)
        cls.engine.dispose()

    def setUp(self) -> None:
        self.session = self.SessionLocal()

    def tearDown(self) -> None:
        self.session.rollback()
        self.session.close()

    def test_user_defaults_and_unique_fields(self) -> None:
        user = User(
            username="attendant",
            email="attendant@example.com",
            hashed_password="hashed-password",
        )
        self.session.add(user)
        self.session.commit()

        saved_user = self.session.scalar(
            select(User).where(User.username == "attendant")
        )
        self.assertIsNotNone(saved_user)
        self.assertIsInstance(saved_user.created_at, datetime)

        duplicate_user = User(
            username="attendant",
            email="another@example.com",
            hashed_password="another-hash",
        )
        self.session.add(duplicate_user)
        with self.assertRaises(IntegrityError):
            self.session.commit()

    def test_parking_spot_defaults(self) -> None:
        spot = ParkingSpot(
            spot_number="A-101",
            spot_type="standard",
            floor_level=1,
        )
        self.session.add(spot)
        self.session.commit()

        saved_spot = self.session.scalar(
            select(ParkingSpot).where(ParkingSpot.spot_number == "A-101")
        )
        self.assertIsNotNone(saved_spot)
        self.assertFalse(saved_spot.is_occupied)

    def test_parking_session_foreign_keys_and_spot_relationship(self) -> None:
        user = User(
            username="operator",
            email="operator@example.com",
            hashed_password="hashed-password",
        )
        spot = ParkingSpot(
            spot_number="EV-201",
            spot_type="ev",
            floor_level=2,
        )
        self.session.add_all([user, spot])
        self.session.flush()

        parking_session = ParkingSession(
            spot_id=spot.id,
            plate_number="ABC-123",
            vehicle_type="ev",
            checked_in_by=user.id,
        )
        self.session.add(parking_session)
        self.session.commit()

        saved_session = self.session.get(ParkingSession, parking_session.id)
        self.assertEqual(saved_session.spot.id, spot.id)
        self.assertEqual(saved_session.spot.spot_number, "EV-201")
        self.assertEqual(saved_session.checked_in_by, user.id)
        self.assertEqual(saved_session.vehicle_type, "ev")
        self.assertIsInstance(saved_session.checked_in_at, datetime)
        self.assertIsNone(saved_session.checked_out_at)
        self.assertIsNone(saved_session.fee_charged)


if __name__ == "__main__":
    unittest.main()
