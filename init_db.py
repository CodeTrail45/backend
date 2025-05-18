from database.init_db import init_db
from database import models

def main():
    """Initialize the database for development."""
    print("Initializing database...")
    engine = init_db()
    print("Database initialized successfully!")

if __name__ == "__main__":
    main() 