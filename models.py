import enum
import os
import shutil
from pathlib import Path
from typing import List, Optional
from datetime import date
from sqlalchemy import String, ForeignKey, event
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped, mapped_column, relationship

"""
SQLAlchemy ORM database models.

Represents Plant objects and other related schemas.
"""


class Base(DeclarativeBase):
    pass


class HealthStatus(enum.Enum):
    """String enum to represent plant states."""

    HEALTHY = "healthy"
    SICK = "sick"
    DEAD = "dead"


class Plant(Base):
    __tablename__ = "plants"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30))
    nickname: Mapped[Optional[str]]
    scientific: Mapped[Optional[str]]
    watering_frequency_days: Mapped[Optional[int]]
    acquisition_date: Mapped[date] = mapped_column(default=date.today())
    health_status: Mapped[HealthStatus] = mapped_column(default=HealthStatus.HEALTHY)
    waterings: Mapped[List["Watering"]] = relationship(
        back_populates="plant", cascade="all, delete-orphan"
    )
    photos: Mapped[List["Photo"]] = relationship(
        back_populates="plant", cascade="all, delete-orphan"
    )
    notes: Mapped[List["Note"]] = relationship(
        back_populates="plant", cascade="all, delete-orphan"
    )
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("plants.id"))
    parent: Mapped[Optional["Plant"]] = relationship(
        "Plant", remote_side=[id], foreign_keys=[parent_id], back_populates="children"
    )
    children: Mapped[List["Plant"]] = relationship("Plant", back_populates="parent")

    def __repr__(self) -> str:
        return f"Plant(id={self.id!r}, name={self.name})"


class Watering(Base):
    __tablename__ = "waterings"
    id: Mapped[int] = mapped_column(primary_key=True)
    plant_id: Mapped[int] = mapped_column(ForeignKey("plants.id"))
    plant: Mapped["Plant"] = relationship(back_populates="waterings")
    date: Mapped[date]


class Photo(Base):
    __tablename__ = "photos"
    id: Mapped[int] = mapped_column(primary_key=True)
    plant_id: Mapped[int] = mapped_column(ForeignKey("plants.id"))
    plant: Mapped["Plant"] = relationship(back_populates="photos")
    date: Mapped[date]
    path: Mapped[str]


@event.listens_for(Photo, "before_delete")
def archive_deleted_photo(mapper, connection, target: Photo):
    """Move photo to archive delete folder."""
    if target.path and os.path.exists(target.path):
        try:
            deleted_dir = Path("deleted_photos")
            deleted_dir.mkdir(exist_ok=True)

            source = Path(target.path)
            destination = deleted_dir / source.name
            shutil.move(str(source), str(destination))
        except Exception as e:
            print(f"Failed to move file {target.path}: {e}")


class Note(Base):
    __tablename__ = "notes"
    id: Mapped[int] = mapped_column(primary_key=True)
    plant_id: Mapped[int] = mapped_column(ForeignKey("plants.id"))
    plant: Mapped["Plant"] = relationship(back_populates="notes")
    date: Mapped[date]
    note: Mapped[str] = mapped_column(String(300))
