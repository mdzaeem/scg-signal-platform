import os
import shutil
import time
from io import BytesIO

from fastapi import APIRouter, UploadFile, File, HTTPException

from db import get_connection, file_exists
from services.parser import parse_filename

router = APIRouter()


# Where we temporarily store uploaded CSVs
UPLOAD_DIRECTORY = "./uploads"
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)


# ============================================================
# Helper Functions
# ============================================================

def save_temp_file(file: UploadFile) -> str:
    """
    Save the uploaded CSV to the local ./uploads folder.
    Returns the full file path.
    """
    out_path = os.path.join(UPLOAD_DIRECTORY, file.filename)
    print(f"💾 [Temp Save] Saving file to {out_path} ...")

    try:
        with open(out_path, "wb+") as buffer:
            shutil.copyfileobj(file.file, buffer)
            print(f"✔ [Temp Save] File saved: {out_path}")
    except Exception as e:
        print(f"❌ [Temp Save] Error while saving: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")
    finally:
        file.file.close()

    return out_path


def check_duplicate_or_raise(filename: str):
    """
    If the given filename already exists in the datasets table,
    raise an HTTP 409 Conflict.
    """
    print(f"🔍 [Duplicate Check] Checking if '{filename}' exists in datasets...")
    if file_exists(filename):
        print(f"❌ [Duplicate Check] Duplicate found: {filename}",flush=True)
        raise HTTPException(
            status_code=409,
            detail=f"File '{filename}' already exists in database."
        )
    print(f"✅ [Duplicate Check] No duplicate found for: {filename}",flush=True)


def insert_metadata_and_related(cursor, filename: str, metadata: dict) -> int:
    print("🗂 [Dataset Insert] Inserting dataset row...")
    """
    Insert into datasets, and upsert into persons + flights.
    Returns the new dataset_id.
    """
    # 1) Insert dataset row
    sql_dataset = """
        INSERT INTO datasets (
            file_name,
            file_date,
            flight_code,
            box_name,
            box_color,
            role,
            person_name
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING dataset_id;
    """
    
    cursor.execute(
        sql_dataset,
        (
            filename,
            metadata.get("file_date"),
            metadata.get("flight_code"),
            metadata.get("box_name"),
            metadata.get("box_color"),
            metadata.get("role"),
            metadata.get("person_name"),
        ),
    )
    row = cursor.fetchone()
    if not row:
        raise HTTPException(
            status_code=500,
            detail="Failed to create dataset entry in database."
        )

    dataset_id = row["dataset_id"]

    # 2) Upsert into persons
    person_name = metadata.get("person_name")
    role = metadata.get("role")
    if person_name:
        cursor.execute(
            """
            INSERT INTO persons (person_name, role)
            VALUES (%s, %s)
            ON CONFLICT (person_name)
            DO UPDATE SET role = EXCLUDED.role;
            """,
            (person_name, role),
        )

    # 3) Upsert into flights
    flight_code = metadata.get("flight_code")
    file_date = metadata.get("file_date")
    if flight_code and file_date:
        cursor.execute(
            """
            INSERT INTO flights (flight_code, flight_date)
            VALUES (%s, %s)
            ON CONFLICT (flight_code)
            DO UPDATE SET flight_date = EXCLUDED.flight_date;
            """,
            (flight_code, file_date),
        )
#zaeem
    box_name = metadata.get("box_name")
    color = metadata.get("box_color")
    if color and box_name:
        cursor.execute(
            """
            INSERT INTO boxes (box_name, color)
            VALUES (%s, %s)
            ON CONFLICT (box_name,color)
            DO NOTHING;
            """,
            (box_name,color),
        )

    return dataset_id


def ingest_signals(cursor, dataset_id: int, csv_path: str) -> int:
    print("🧹 [Staging] TRUNCATE signals_staging before COPY...")
    """
    Load the CSV from disk into signals_staging, then insert into signals table.
    Returns the number of rows inserted into signals.
    """
    print(f"📤 [COPY] Copying CSV → signals_staging from {csv_path}...")
    # A) Clear staging
    cursor.execute("TRUNCATE TABLE signals_staging;")

    # B) COPY from CSV into staging
    with open(csv_path, "r") as f:
        cursor.copy_expert(
            "COPY signals_staging FROM STDIN WITH (FORMAT CSV, HEADER TRUE)", f
        )
    print(f"📥 [Insert Signals] Moving rows to signals for dataset_id={dataset_id}...")
    # C) Move from staging -> signals hypertable
    sql_transfer = """
        INSERT INTO signals (
            dataset_id, time, header,
            ax_alpha, ax_beta, ax_gamma,
            ay_alpha, ay_beta, ay_gamma,
            az_alpha, az_beta, az_gamma,
            gx_alpha, gx_beta, gx_gamma,
            gy_alpha, gy_beta, gy_gamma,
            gz_alpha, gz_beta, gz_gamma,
            ecg, frame_separator
        )
        SELECT
            %s AS dataset_id,
            CAST(time * 1000000 AS BIGINT) AS time, -- seconds -> microseconds
            header,
            ax_alpha, ax_beta, ax_gamma,
            ay_alpha, ay_beta, ay_gamma,
            az_alpha, az_beta, az_gamma,
            gx_alpha, gx_beta, gx_gamma,
            gy_alpha, gy_beta, gy_gamma,
            gz_alpha, gz_beta, gz_gamma,
            ecg,
            frame_seperator  -- CSV typo -> DB column
        FROM signals_staging;
    """
    cursor.execute(sql_transfer, (dataset_id,))
    row_count = cursor.rowcount

    # D) Cleanup staging
    cursor.execute("TRUNCATE TABLE signals_staging;")

    return row_count


# ============================================================
# MAIN ALL-IN-ONE ENDPOINT
# ============================================================

@router.post("/upload-csv")
async def upload_csv(file: UploadFile = File(...)):
    print("🔥🔥🔥 upload_csv() STARTED — CODE IS RUNNING FROM THIS FILE 🔥🔥🔥")
    """
    ALL-IN-ONE PIPELINE (Disk-based, stable):

    1) Check duplicate filename in datasets.
    2) Save CSV to ./uploads.
    3) Parse metadata from filename.
    4) In ONE DB transaction:
        - insert into datasets, persons, flights
        - load CSV into signals_staging via COPY
        - insert from staging into signals hypertable
    5) Return dataset_id, metadata, row counts, and duration.
    """

    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only .csv files are allowed.")

    # 1) Check duplicates early
    check_duplicate_or_raise(file.filename)

    # 2) Save file temporarily
    start_time = time.time()
    csv_path = save_temp_file(file)

    # 3) Parse filename → metadata
    metadata = parse_filename(file.filename)
    if "file_name_error" in metadata:
        raise HTTPException(
            status_code=400,
            detail=f"Filename parse error: {metadata['file_name_error']}",
        )

    conn = get_connection()
    try:
        conn.autocommit = False  # manual transaction
        with conn.cursor() as cursor:
            # 4A) Insert into datasets + persons + flights
            dataset_id = insert_metadata_and_related(
                cursor=cursor,
                filename=file.filename,
                metadata=metadata,
            )

            # 4B) Ingest signals from CSV into TimescaleDB
            rows_inserted = ingest_signals(
                cursor=cursor,
                dataset_id=dataset_id,
                csv_path=csv_path,
            )

        conn.commit()
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Upload failed: {e}")
    finally:
        conn.close()
        # Optional: delete CSV to save disk space
        # try:
        #     os.remove(csv_path)
        # except OSError:
        #     pass

    duration = round(time.time() - start_time, 2)

    return {
        "message": "Dataset and signals uploaded successfully.",
        "dataset_id": dataset_id,
        "file_name": file.filename,
        "metadata": metadata,
        "rows_inserted": rows_inserted,
        "duration_seconds": duration,
        "temp_path": csv_path,  # for debugging; can remove later
    }


# ============================================================
# DEV ENDPOINT: auto-upload all CSVs from ./uploads
# ============================================================

@router.get("/dev/upload-sample")
async def dev_upload_sample():
    """
    DEV:
    - Scan ./uploads for .csv files
    - Skip files already in datasets
    - For each new file, call the same /upload-csv logic.
    """
    if not os.path.exists(UPLOAD_DIRECTORY):
        return {"error": "Uploads folder does not exist"}

    files = [f for f in os.listdir(UPLOAD_DIRECTORY) if f.lower().endswith(".csv")]

    if not files:
        return {"message": "No CSV files found in uploads folder"}

    uploaded = []
    skipped = []

    for file_name in files:
        file_path = os.path.join(UPLOAD_DIRECTORY, file_name)

        if file_exists(file_name):
            skipped.append(f"{file_name} (already exists in DB)")
            continue

        try:
            with open(file_path, "rb") as f:
                data = f.read()

            upload = UploadFile(
                filename=file_name,
                file=BytesIO(data),
            )

            result = await upload_csv(upload)
            uploaded.append(result)
        except Exception as e:
            skipped.append(f"{file_name} (error: {str(e)})")

    return {
        "uploaded": uploaded,
        "skipped": skipped,
        "total_files": len(files),
    }

@router.post("/dev/reset-db")
def dev_reset_db():
    """
    DEV-ONLY:
    Safely reset all project tables for re-testing.
    Keeps schema & hypertable, only clears data.
    """
    print("\n======================================")
    print("🧹 DEV RESET STARTED — Clearing tables")
    print("======================================\n")

    conn = get_connection()

    try:
        conn.autocommit = False
        with conn.cursor() as cursor:

            print("→ TRUNCATE signals_staging ...")
            cursor.execute("TRUNCATE TABLE signals_staging;")
            print("✔ signals_staging cleared\n")

            print("→ TRUNCATE signals (CASCADE) ...")
            cursor.execute("TRUNCATE TABLE signals CASCADE;")
            print("✔ signals cleared (CASCADE applied)\n")

            print("→ TRUNCATE datasets (RESTART IDENTITY CASCADE) ...")
            cursor.execute("TRUNCATE TABLE datasets RESTART IDENTITY CASCADE;")
            print("✔ datasets cleared and ID reset\n")

            print("→ TRUNCATE persons ...")
            cursor.execute("TRUNCATE TABLE persons;")
            print("✔ persons cleared\n")

            print("→ TRUNCATE flights ...")
            cursor.execute("TRUNCATE TABLE flights;")
            print("✔ flights cleared\n")
#added trunk for boxes table
            print("→ TRUNCATE boxes ...")
            cursor.execute("TRUNCATE TABLE boxes;")
            print("✔ boxes cleared\n")

        conn.commit()
        print("💾 Transaction committed successfully!")
        print("✅ DEV RESET COMPLETED ✔\n")

        return {
            "message": "Database reset successful. All tables cleared.",
            "status": "success"
        }

    except Exception as e:
        conn.rollback()
        print(f"❌ ERROR during reset: {e}\n")
        raise HTTPException(status_code=500, detail=f"Reset failed: {e}")

    finally:
        conn.close()
        print("🔌 DB connection closed.")
