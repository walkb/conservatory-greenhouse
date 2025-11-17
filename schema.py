from pydantic import BaseModel
from typing import Optional
from datetime import date
from fastapi import UploadFile
from models import HealthStatus


# Base schema
class PlantBase(BaseModel):
    name: str
    nickname: Optional[str] = None
    scientific: Optional[str] = None
    watering_frequency_days: Optional[int] = None
    acquisition_date: Optional[date] = date.today()
    health_status: Optional[HealthStatus] = HealthStatus.HEALTHY


# Creating a plant (no id)
class PlantCreate(PlantBase):
    pass


class PlantUpdate(BaseModel):
    name: Optional[str] = None
    nickname: Optional[str] = None
    scientific: Optional[str] = None
    watering_frequency_days: Optional[int] = None
    acquisition_date: Optional[date] = None
    health_status: Optional[HealthStatus] = None


# Reading a plant (returns id)
class PlantResponse(PlantBase):
    id: int

    class Config:
        from_attributes = True


# Watering base schema
class WateringBase(BaseModel):
    plant_id: int
    date: date


class WateringCreate(WateringBase):
    pass


class WateringResponse(WateringBase):
    id: int
    plant_id: int
    date: date
    # uncomment if we want to fetch plant as well
    # plant: PlantResponse

    class Config:
        from_attributes = True


class PhotoBase(BaseModel):
    plant_id: int
    date: date


class PhotoCreate(PhotoBase):
    pass


class PhotoResponse(PhotoBase):
    id: int
    path: str

    class Config:
        from_attributes = True


class NoteBase(BaseModel):
    plant_id: int
    date: date
    note: str


class NoteCreate(NoteBase):
    pass


class NoteUpdate(BaseModel):
    plant_id: int
    date: date
    note: str


class NoteResponse(NoteBase):
    id: int
    plant_id: int

    class Config:
        from_attributes = True
