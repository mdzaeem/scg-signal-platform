import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load .env file
load_dotenv()

def get_connection():
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            cursor_factory=RealDictCursor
        )
        print("✅ Connected to PostgreSQL!")
        return conn

    except Exception as e:
        print("❌ Database connection error:", e)
        raise

# Utility function to check if a file with the same name already exists in the database
def file_exists(file_name: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT dataset_id FROM datasets WHERE file_name = %s", (file_name,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result is not None
