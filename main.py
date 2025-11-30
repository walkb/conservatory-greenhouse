import os
import datetime
from fastapi import FastAPI, Depends, HTTPException, UploadFile, Form, File, Query
from fastapi.staticfiles import StaticFiles
from typing import Annotated, List
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select
from database import SessionLocal
import schema
import models

app = FastAPI()

# Create photo directory if doesn't exist
os.makedirs("photos", exist_ok=True)

# Mount static photo files for access
app.mount("/static", StaticFiles(directory="photos"), name="photos")


# Dependable: get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
async def root():
    return {"message": "hi"}


# Create a plant
@app.post("/plants/", response_model=schema.PlantResponse)
def create_plant(plant_in: schema.PlantCreate, db: Session = Depends(get_db)):
    plant = models.Plant(**plant_in.model_dump())
    db.add(plant)
    db.commit()
    db.refresh(plant)
    return plant


# Get all plants (optional: add pagination)
@app.get("/plants", response_model=list[schema.PlantResponse])
def get_all_plants(db: Session = Depends(get_db)):
    query = select(models.Plant).options(selectinload(models.Plant.photos))
    res = db.execute(query)
    return res.scalars().all()


# Get a plant by id
@app.get("/plants/{id}", response_model=schema.PlantResponse)
def get_plant_by_id(id: int, db: Session = Depends(get_db)):
    query = (
        select(models.Plant)
        .where(models.Plant.id == id)
        .options(selectinload(models.Plant.photos))
    )
    plant = db.execute(query).scalars().first()
    if not plant:
        raise HTTPException(status_code=404, detail=f"Plant with id {id} not found.")
    return plant


# Update a plant by id
@app.patch("/plants/{id}", response_model=schema.PlantResponse)
def update_plant_by_id(
    id: int, plant_in: schema.PlantUpdate, db: Session = Depends(get_db)
):
    plant = db.get(models.Plant, id)
    if not plant:
        raise HTTPException(status_code=404, detail=f"Plant with id {id} not found.")

    # update keys
    for key, value in plant_in.model_dump(exclude_unset=True).items():
        setattr(plant, key, value)
    db.commit()
    db.refresh(plant)
    return plant


# Delete a plant by id
@app.delete("/plants/{id}")
def delete_plant_by_id(id: int, db: Session = Depends(get_db)):
    plant = db.get(models.Plant, id)
    if not plant:
        raise HTTPException(status_code=404, detail=f"Plant with id {id} not found.")

    # delete plant
    db.delete(plant)
    db.commit()
    return


# Get a plant's photos or latest photo
@app.get("/plants/{id}/photos")
def get_plant_photos(
    id: int, start: int = 0, limit: int = 1, db: Session = Depends(get_db)
):
    plant = db.get(models.Plant, id)
    if not plant:
        raise HTTPException(status_code=404, detail=f"Plant with id {id} not found.")

    photos = (
        db.query(models.Photo)
        .filter(models.Photo.plant_id == id)
        .order_by(models.Photo.date.desc())
        .offset(start)
        .limit(limit)
        .all()
    )
    return photos


# Get a plant's waterings or latest watering
@app.get("/plants/{id}/waterings")
def get_plant_waterings(
    id: int, start: int = 0, limit: int = 3, db: Session = Depends(get_db)
):
    plant = db.get(models.Plant, id)
    if not plant:
        raise HTTPException(status_code=404, detail=f"Plant with id {id} not found.")

    waterings = (
        db.query(models.Watering)
        .filter(models.Watering.plant_id == id)
        .order_by(models.Watering.date.desc())
        .offset(start)
        .limit(limit)
        .all()
    )
    return waterings


# Get a plant's notes or latest notes
@app.get("/plants/{id}/notes")
def get_plant_notes(
    id: int, start: int = 0, limit: int = 3, db: Session = Depends(get_db)
):
    plant = db.get(models.Plant, id)
    if not plant:
        raise HTTPException(status_code=404, detail=f"Plant with id {id} not found.")

    notes = (
        db.query(models.Note)
        .filter(models.Note.plant_id == id)
        .order_by(models.Note.date.desc())
        .offset(start)
        .limit(limit)
        .all()
    )
    return notes


# Create a watering
@app.post("/waterings/", response_model=schema.WateringResponse)
def create_watering(watering_in: schema.WateringCreate, db: Session = Depends(get_db)):
    # Check if a plant exists with plant_id
    plant = (
        db.query(models.Plant).filter(models.Plant.id == watering_in.plant_id).first()
    )
    if not plant:
        raise HTTPException(
            status_code=404, detail=f"Plant with id {watering_in.plant_id} not found."
        )

    watering = models.Watering(**watering_in.model_dump())
    db.add(watering)
    db.commit()
    db.refresh(watering)
    return watering


# Delete a watering by watering id
@app.delete("/waterings/{id}")
def delete_watering(id: int, db: Session = Depends(get_db)):
    w = db.get(models.Watering, id)
    if not w:
        raise HTTPException(status_code=404, detail=f"Watering with id {id} not found.")
    db.delete(w)
    db.commit()
    return


# Get all waterings
@app.get("/waterings", response_model=list[schema.WateringResponse])
def get_all_waterings(db: Session = Depends(get_db)):
    res = db.query(models.Watering)
    return res.all()


# Helper dependency to allow Pydantic input
def photo_form(
    plant_id: Annotated[int, Form()], date: Annotated[datetime.date, Form()]
) -> schema.PhotoCreate:
    return schema.PhotoCreate(plant_id=plant_id, date=date)


# Create (upload) a photo for a plant
@app.post("/photos", response_model=schema.PhotoResponse)
async def add_photo(
    photo_data: Annotated[schema.PhotoCreate, Depends(photo_form)],
    photo: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    pid = photo_data.plant_id
    plant = db.query(models.Plant).filter(models.Plant.id == pid).first()
    if not plant:
        raise HTTPException(status_code=404, detail=f"Plant with id {pid} not found.")
    plant.name

    file_name = f"{photo_data.date.isoformat()}-{plant.name.replace(" ", "_")}"
    file_location = f"photos/{file_name}"

    with open(file_location, "wb") as f:
        f.write(await photo.read())

    photo_entry = models.Photo(**photo_data.model_dump(), path=f"static/{file_name}")
    db.add(photo_entry)
    db.commit()
    db.refresh(photo_entry)
    return photo_entry


# Get all photos
@app.get("/photos", response_model=list[schema.PhotoResponse])
def get_all_photos(db: Session = Depends(get_db)):
    res = db.query(models.Photo)
    return res.all()


# Delete a photo by id
@app.delete("/photos/{id}")
def delete_photo(id: int, db: Session = Depends(get_db)):
    p = db.get(models.Photo, id)
    if not p:
        raise HTTPException(status_code=404, detail=f"Photo with id {id} not found.")
    db.delete(p)
    db.commit()
    return


# Create a note for a plant
@app.post("/notes", response_model=schema.WateringResponse)
def create_note(note_in: schema.NoteCreate, db: Session = Depends(get_db)):
    # Check if a plant exists with plant_id
    plant = db.query(models.Plant).filter(models.Plant.id == note_in.plant_id).first()
    if not plant:
        raise HTTPException(
            status_code=404, detail=f"Plant with id {note_in.plant_id} not found."
        )

    note = models.Note(**note_in.model_dump())
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


# Read a note by id
@app.get("/notes/{id}", response_model=schema.NoteResponse)
def get_note_by_id(id: int, db: Session = Depends(get_db)):
    note = db.get(models.Note, id)
    if not note:
        raise HTTPException(status_code=404, detail=f"Plant with id {id} not found.")
    return note


# Update a note for a plant
@app.patch("/notes/{id}", response_model=schema.NoteResponse)
def update_note_by_id(
    id: int, note_in: schema.NoteUpdate, db: Session = Depends(get_db)
):
    note = db.get(models.Note, id)
    if not note:
        raise HTTPException(status_code=404, detail=f"Note with id {id} not found.")

    # update keys
    for key, value in note_in.model_dump(exclude_unset=True).items():
        setattr(note, key, value)
    db.commit()
    db.refresh(note)
    return note


# Delete a note by id
@app.delete("/notes/{id}")
def delete_note(id: int, db: Session = Depends(get_db)):
    n = db.get(models.Note, id)
    if not n:
        raise HTTPException(status_code=404, detail=f"Note with id {id} not found.")
    db.delete(n)
    db.commit()
    return
