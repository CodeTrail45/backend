from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .config import Base, SQLALCHEMY_DATABASE_URL
from . import models

def init_db():
    """Initialize the database by creating all tables."""
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    return engine

def get_test_db():
    """Get a test database session."""
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return TestingSessionLocal()

if __name__ == "__main__":
    print("Creating database tables...")
    init_db()
    print("Database tables created successfully!") 