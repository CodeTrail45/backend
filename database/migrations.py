from sqlalchemy import create_engine, text
from .config import SQLALCHEMY_DATABASE_URL, Base
from . import models

def run_migrations():
    """Run database migrations (create tables if not exist)."""
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    Base.metadata.create_all(bind=engine, checkfirst=True)

# def run_migrations():
#     """Run database migrations."""
#     engine = create_engine(SQLALCHEMY_DATABASE_URL)
#
#     # Create all tables
#     Base.metadata.create_all(bind=engine)
#
#     # Verify tables exist
#     with engine.connect() as conn:
#         # Check if songs table exists and has required columns
#         result = conn.execute(text("""
#             SELECT column_name
#             FROM information_schema.columns
#             WHERE table_name = 'songs'
#         """))
#         columns = [row[0] for row in result]
#
#         # If songs table doesn't exist or is missing columns, recreate it
#         if not columns or 'title' not in columns:
#             # Drop existing table if it exists
#             conn.execute(text("DROP TABLE IF EXISTS songs CASCADE"))
#             # Recreate table
#             models.Song.__table__.create(engine)
#
#         # Check if comments table exists and has required columns
#         result = conn.execute(text("""
#             SELECT column_name
#             FROM information_schema.columns
#             WHERE table_name = 'comments'
#         """))
#         columns = [row[0] for row in result]
#
#         # If comments table doesn't exist or is missing columns, recreate it
#         if not columns or 'content' not in columns:
#             # Drop existing table if it exists
#             conn.execute(text("DROP TABLE IF EXISTS comments CASCADE"))
#             # Recreate table
#             models.Comment.__table__.create(engine)

if __name__ == "__main__":
    print("Running database migrations...")
    run_migrations()
    print("Database migrations completed successfully!") 