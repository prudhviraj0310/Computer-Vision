import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import StaticPool

# Fetch database URL from environment, fallback to local SQLite for easy development
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./trafficeye.db")

# SQLite needs specific connect_args and StaticPool for thread safety.
# StaticPool serializes all access through a single connection, preventing
# "database is locked" errors when multiple threads use SQLite concurrently.
connect_args = {}
engine_kwargs = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
    engine_kwargs["poolclass"] = StaticPool

engine = create_engine(DATABASE_URL, connect_args=connect_args, **engine_kwargs)
_session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
SessionLocal = scoped_session(_session_factory)

Base = declarative_base()

def get_db():
    """Dependency injection helper to yield database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        SessionLocal.remove()
