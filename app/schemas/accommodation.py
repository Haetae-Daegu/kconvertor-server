from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from decimal import Decimal
from datetime import datetime

class AccommodationBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str
    price_per_month: Decimal = Field(..., gt=0)
    security_deposit: Optional[Decimal] = Field(0, ge=0)
    location: str = Field(..., min_length=1, max_length=200)
    bedrooms: int = Field(..., gt=0)
    bathrooms: int = Field(..., gt=0)
    max_guests: int = Field(..., gt=0)
    minimum_stay: Optional[int] = Field(1, gt=0)
    amenities: Optional[List[str]] = []
    house_rules: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    @field_validator('price_per_month', 'security_deposit')
    @classmethod
    def validate_price(cls, v):
        return round(v, 2)

class AccommodationCreate(AccommodationBase):
    pass

class AccommodationUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    price_per_month: Optional[Decimal] = Field(None, gt=0)
    security_deposit: Optional[Decimal] = Field(None, ge=0)
    location: Optional[str] = Field(None, min_length=1, max_length=200)
    bedrooms: Optional[int] = Field(None, gt=0)
    bathrooms: Optional[int] = Field(None, gt=0)
    max_guests: Optional[int] = Field(None, gt=0)
    minimum_stay: Optional[int] = Field(None, gt=0)
    amenities: Optional[List[str]] = None
    house_rules: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class AccommodationResponse(AccommodationBase):
    id: int
    host_id: int
    created_at: datetime
    updated_at: datetime
    status: str = 'active'

    class Config:
        from_attributes = True 