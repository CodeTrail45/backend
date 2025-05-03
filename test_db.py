import psycopg2
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Database credentials
DB_USER = os.getenv('DB_USER')
DB_HOST = os.getenv('DB_HOST')
DB_NAME = os.getenv('DB_NAME')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_PORT = os.getenv('DB_PORT')

# Test database connection
try:
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    print("Database connection successful.")
    conn.close()
except Exception as e:
    print("Error connecting to database:", e)
    
    
    
print(DB_USER, DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT)

