import os
import re
from db import get_connection

def parse_filename(filename: str):
    """
    Expected format:
    Artifacts_F1_BBox2_Orange_Operator_URS_10.06.2025.csv
    """

    base = os.path.basename(filename)
    name = base.replace(".csv", "")
    parts = name.split("_")

    if len(parts) < 7:
        raise ValueError("Filename format invalid.")

    return {
        "flight_code": parts[1],
        "box_name": parts[2],
        "box_color": parts[3],
        "role": parts[4],
        "person_name": parts[5],
        "file_date": parts[6]   # "10.06.2025"
    }


def process_uploaded_file(filepath: str):
    # Extract metadata
    meta = parse_filename(filepath)

    conn = get_connection()
    cursor = conn.cursor()

    # Insert into datasets table
    cursor.execute("""
        INSERT INTO datasets (file_name, flight_code, box_name, box_color, role, person_name, file_date)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING dataset_id;
    """, (
        os.path.basename(filepath),
        meta["flight_code"],
        meta["box_name"],
        meta["box_color"],
        meta["role"],
        meta["person_name"],
        meta["file_date"]
    ))

    dataset_id = cursor.fetchone()["dataset_id"]

    conn.commit()
    cursor.close()
    conn.close()

    print(f"✅ Metadata inserted (dataset_id = {dataset_id})")

    return dataset_id
