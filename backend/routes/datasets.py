from fastapi import APIRouter, HTTPException
from db import get_connection

router = APIRouter()   

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


@router.get("/datasets/{dataset_id}")
def get_dataset(dataset_id: int):
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
        WHERE dataset_id = %s;
    """, (dataset_id,))

    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if row is None:
        raise HTTPException(status_code=404, detail="Dataset not found")

    return row