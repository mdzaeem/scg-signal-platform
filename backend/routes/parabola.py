from fastapi import APIRouter, HTTPException
from pathlib import Path
import json

from db import get_connection

router = APIRouter(prefix="/parabolas", tags=["parabolas"])


@router.post("/import")
def import_parabolas_from_json(json_path: str):
    """
    Import parabolas from a JSON file into the database.

    Parameters
    ----------
    json_path : str
        Absolute or relative path to the JSON file
    """

    # --------------------------------------------------
    # 1. Check JSON file
    # --------------------------------------------------
    json_file = Path(json_path)

    if not json_file.exists():
        raise HTTPException(status_code=404, detail="JSON file not found")

    # --------------------------------------------------
    # 2. Load JSON
    # --------------------------------------------------
    with open(json_file, "r") as f:
        data = json.load(f)

    if "dataset_file_name" not in data:
        raise HTTPException(
            status_code=400,
            detail="Missing 'dataset_file_name' in JSON"
        )

    if "parabolas" not in data:
        raise HTTPException(
            status_code=400,
            detail="Missing 'parabolas' list in JSON"
        )

    dataset_file_name = data["dataset_file_name"]
    parabolas = data["parabolas"]

    # --------------------------------------------------
    # 3. Open DB connection
    # --------------------------------------------------
    conn = get_connection()
    cursor = conn.cursor()

    # --------------------------------------------------
    # 4. Resolve dataset_id
    # --------------------------------------------------
    cursor.execute(
        """
        SELECT dataset_id, flight_code, person_name
        FROM datasets
        WHERE file_name = %s
        """,
        (dataset_file_name,)
    )
    row = cursor.fetchone()

    if row is None:
        cursor.close()
        conn.close()
        raise HTTPException(
            status_code=404,
            detail=f"Dataset not found for file_name={dataset_file_name}"
        )

    dataset_id = row["dataset_id"]
    flight_code = row["flight_code"]
    person_name = row["person_name"]


    # --------------------------------------------------
    # 5. Insert parabolas
    # --------------------------------------------------
    inserted = 0
    skipped = 0

    for p in parabolas:
        # Skip invalid parabolas if flag exists
        parabola_name = f"{flight_code}{person_name}P{p['parabola_number']}".upper()
        if "is_valid" in p and p["is_valid"] is False:
            skipped += 1
            continue

        cursor.execute(
            """
            INSERT INTO parabolas (
                dataset_id,
                parabola_number,
                parabola_name,
                start_time,
                end_time,
                two_g_left_time,
                two_g_right_time,
                zero_g_duration_s
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (dataset_id, parabola_number) DO NOTHING
            """,
            (
                dataset_id,
                p["parabola_number"],
                parabola_name,
                p["start_time"],
                p["end_time"],
                p["two_g_left_time"],
                p["two_g_right_time"],
                p["zero_g_duration_s"],
            )
        )
        inserted += 1

    conn.commit()
    cursor.close()
    conn.close()

    # --------------------------------------------------
    # 6. Response
    # --------------------------------------------------
    return {
        "dataset_file_name": dataset_file_name,
        "parabolas_in_json": len(parabolas),
        "parabolas_inserted": inserted,
        "parabolas_skipped": skipped
    }
