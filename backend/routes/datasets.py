from fastapi import APIRouter
from db import get_connection

router = APIRouter()   # ✅ must exist and must be named exactly `router`

@router.get("/datasets")
def list_datasets():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            dataset_id,
            file_name,
            person_name,
            role,
            flight_code,
            box_name,
            box_color,
            file_date
        FROM datasets
        ORDER BY dataset_id DESC;
    """)

    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    return rows
