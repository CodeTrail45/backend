import os
import shutil
import subprocess
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def backup_sqlite():
    """Backup SQLite database"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = "database_backups"
    os.makedirs(backup_dir, exist_ok=True)
    
    source_db = "test.db"
    backup_file = os.path.join(backup_dir, f"test_db_backup_{timestamp}.db")
    
    try:
        shutil.copy2(source_db, backup_file)
        print(f"✅ SQLite backup created successfully: {backup_file}")
    except Exception as e:
        print(f"❌ Error creating SQLite backup: {str(e)}")

def backup_postgres():
    """Backup PostgreSQL database"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = "database_backups"
    os.makedirs(backup_dir, exist_ok=True)
    
    # Get PostgreSQL configuration from environment variables
    db_name = os.getenv("POSTGRES_DB", "lyrics_db")
    db_user = os.getenv("POSTGRES_USER", "postgres")
    db_host = os.getenv("POSTGRES_HOST", "localhost")
    db_port = os.getenv("POSTGRES_PORT", "5432")
    
    backup_file = os.path.join(backup_dir, f"postgres_backup_{timestamp}.sql")
    
    try:
        # Construct pg_dump command
        cmd = [
            "pg_dump",
            f"--dbname=postgresql://{db_user}@{db_host}:{db_port}/{db_name}",
            f"--file={backup_file}"
        ]
        
        # Run pg_dump
        subprocess.run(cmd, check=True)
        print(f"✅ PostgreSQL backup created successfully: {backup_file}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error creating PostgreSQL backup: {str(e)}")
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")

def main():
    """Main function to create database backup"""
    env = os.getenv("ENV", "development")
    
    if env == "test":
        backup_sqlite()
    else:
        backup_postgres()

if __name__ == "__main__":
    main() 