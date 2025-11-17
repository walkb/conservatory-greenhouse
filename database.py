from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base

SQLALCHEMY_DB_URL = "sqlite:///./conservatory.db"

engine = create_engine(
    SQLALCHEMY_DB_URL, connect_args={"check_same_thread": False}  # required for SQLite
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create all tables if they don't exist
Base.metadata.create_all(bind=engine)
