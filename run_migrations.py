from database.migrations import run_migrations

if __name__ == "__main__":
    print("Starting database migrations...")
    run_migrations()
    print("Database migrations completed!") 