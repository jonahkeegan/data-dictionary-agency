"""
Database connection and session management for the Data Dictionary Agency application.
"""
import logging
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from src.core.config import settings


logger = logging.getLogger(__name__)

# Create SQLAlchemy engine
engine = create_engine(
    settings.postgres_dsn,
    pool_pre_ping=True,
    pool_recycle=3600,
    connect_args={"application_name": "dda"},
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create declarative base for models
Base = declarative_base()


def get_db_session() -> Generator[Session, None, None]:
    """Get a database session.
    
    Yields:
        Session: SQLAlchemy session.
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


# MongoDB connection
try:
    import motor.motor_asyncio
    
    # Create MongoDB client
    mongodb_client = motor.motor_asyncio.AsyncIOMotorClient(settings.MONGODB_URI)
    mongodb_db = mongodb_client.get_default_database()
    
    logger.info("Connected to MongoDB database: %s", mongodb_db.name)
    
except ImportError:
    logger.warning("Motor MongoDB driver not installed, MongoDB support disabled")
    mongodb_db = None


def get_mongodb_collection(collection_name: str):
    """Get a MongoDB collection.
    
    Args:
        collection_name: Collection name.
        
    Returns:
        Collection: MongoDB collection.
        
    Raises:
        RuntimeError: If MongoDB support is disabled.
    """
    if mongodb_db is None:
        raise RuntimeError("MongoDB support is disabled")
    
    return mongodb_db[collection_name]
