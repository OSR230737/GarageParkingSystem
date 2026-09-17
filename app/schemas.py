from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserCreate(BaseModel):
    username: str = Field(min_length=1)
    email: str = Field(min_length=3)
    password: str = Field(min_length=8)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    created_at: datetime


class TokenResponse(BaseModel):
    token: str
    username: str


class LoginRequest(BaseModel):
    username: str
    password: str


class SpotCreate(BaseModel):
    spot_number: str = Field(min_length=1)
    spot_type: str
    floor_level: int


class SpotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    spot_number: str
    spot_type: str
    floor_level: int
    is_occupied: bool


class SpotListResponse(BaseModel):
    data: list[SpotResponse]
    total: int
    skip: int
    limit: int


class CheckInRequest(BaseModel):
    plate_number: str = Field(min_length=1)
    vehicle_type: str
    spot_id: int


class ParkingSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    spot_id: int
    plate_number: str
    vehicle_type: str
    checked_in_at: datetime
    checked_out_at: datetime | None
    fee_charged: float | None
    checked_in_by: int


class ParkingSessionListResponse(BaseModel):
    data: list[ParkingSessionResponse]
    total: int
    skip: int
    limit: int


class CheckoutResponse(BaseModel):
    session_id: int
    plate_number: str
    fee_charged: float
    checked_in_at: datetime
    checked_out_at: datetime
    duration_hours: int