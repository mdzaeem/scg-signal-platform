import os
import shutil
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
import psycopg2
from psycopg2.extras import RealDictCursor
from io import BytesIO
import shutil
import time
import os

# Import from parent/sibling directories
from db import get_connection, file_exists  # Imports the get_connection function from db.py
from services.parser import parse_filename # Imports the parser

router = APIRouter()

# Define a temporary upload folder
UPLOAD_DIRECTORY = "./uploads"
if not os.path.exists(UPLOAD_DIRECTORY):
    os.makedirs(UPLOAD_DIRECTORY)

#two lines below for csv auto pickup testing can delete later code-1.1
SAMPLE_FILE_NAME = "Artifacts_F1_BBox2_Orange_Operator_URS_10.06.2025.csv"
SAMPLE_FILE_PATH = os.path.join(UPLOAD_DIRECTORY, SAMPLE_FILE_NAME)


#for csv auto pickup testing can delete later code-1.2 (Final)
@router.get("/dev/upload-sample")
async def dev_upload_sample():
    """
    DEV-ONLY:
    - Scan ./uploads folder for CSV files
    - Skip files that already exist in DB
    - Upload only new files
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

        # Check DB
        if file_exists(file_name):
            skipped.append(f"{file_name} (already exists in DB)")
            continue

        # Read file and wrap as UploadFile
        try:
            with open(file_path, "rb") as f:
                data = f.read()

            upload = UploadFile(
                filename=file_name,
                file=BytesIO(data)
            )

            # IMPORTANT FIX — DO NOT PASS conn
            result = await upload_csv(upload)

            uploaded.append(result)

        except Exception as e:
            skipped.append(f"{file_name} (error: {str(e)})")

    return {
        "uploaded": uploaded,
        "skipped": skipped,
        "total_files": len(files)
    }




# @router.get("/dev/upload-sample")
# async def dev_upload_sample(conn: psycopg2.extensions.connection = Depends(get_connection)):
#     """
#     DEV-ONLY helper:
#     - Picks a fixed CSV from ./uploads
#     - Reuses the same logic as /api/upload-csv
#     - Lets you test without manually choosing a file each time
#     """
#     if not os.path.exists(SAMPLE_FILE_PATH):
#         raise HTTPException(
#             status_code=404,
#             detail=f"Sample file not found at {SAMPLE_FILE_PATH}. "
#                    f"Make sure it exists in the 'uploads' folder."
#         )

    # Read the file bytes
    # with open(SAMPLE_FILE_PATH, "rb") as f:
    #     data = f.read()

    # # Wrap it as an UploadFile so we can reuse upload_csv()
    # upload = UploadFile(
    #     filename=SAMPLE_FILE_NAME,
    #     file=BytesIO(data)
    # )

    # # Call your existing logic
    # return await upload_csv(upload, conn)


#upload manually via API
# @router.post("/upload-csv")
# async def upload_csv(file: UploadFile = File(...), conn: psycopg2.extensions.connection = Depends(get_connection)):

@router.post("/upload-csv")
async def upload_csv(file: UploadFile = File(...)):
    conn = get_connection()
    
    """
    This endpoint performs PHASE 4:
    1. Receives a CSV file.
    2. Saves it temporarily to the './uploads' folder.
    3. Parses the filename to extract metadata.
    4. Inserts that metadata into the 'datasets' table.
    5. Returns the new 'dataset_id' for the next step.
    """

    from fastapi.params import Depends as DependsClass

    if conn is None or not hasattr(conn, "cursor"):
        conn = get_connection()


   
    
    file_location = os.path.join(UPLOAD_DIRECTORY, file.filename)
    filename = file.filename


    if file_exists(filename):
        raise HTTPException(
            status_code=409,   # HTTP 409 = Conflict
            detail=f"The file '{filename}' already exists in the database."
        )
    
    try:
        # 1. Save the file temporarily
        with open(file_location, "wb+") as file_object:
            shutil.copyfileobj(file.file, file_object)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")
    finally:
        file.file.close()

    # 2. Parse metadata from the filename
    print(f"Parsing filename: {file.filename}")
    metadata = parse_filename(file.filename)
    
    if "file_name_error" in metadata:
        raise HTTPException(status_code=400, detail=f"Failed to parse filename: {metadata['file_name_error']}")

    print(f"Parsed metadata: {metadata}")

    # 3. Insert metadata into 'datasets' table
    try:
        with conn.cursor() as cursor:
            # SQL query to insert metadata and get the new ID
            sql = """
                INSERT INTO datasets (
                    file_name, file_date, flight_code, 
                    box_name, box_color, role, person_name
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING dataset_id;
            """
            
            cursor.execute(sql, (
                file.filename,
                metadata.get("file_date"),
                metadata.get("flight_code"),
                metadata.get("box_name"),
                metadata.get("box_color"),
                metadata.get("role"),
                metadata.get("person_name")
            ))
            
            # Fetch the new dataset_id
            result = cursor.fetchone()
            if not result:
                raise HTTPException(status_code=500, detail="Failed to create dataset entry in database.")
                
            new_dataset_id = result['dataset_id']
            
            # Commit the transaction
            conn.commit()
            
            print(f"Successfully created dataset record with ID: {new_dataset_id}")

    except Exception as e:
        conn.rollback() # Rollback on error
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    finally:
        conn.close()

    # 4. Return success
    return {
        "message": "File uploaded and metadata saved.",
        "dataset_id": new_dataset_id,
        "file_name": file.filename,
        "temp_path": file_location,
        "metadata": metadata
    }




# Ensure the upload directory exists
UPLOAD_DIR = "uploads/signals"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload-signals/{dataset_id}")
def upload_signals(dataset_id: int, file: UploadFile = File(...)):
    """
    Uploads a large signal CSV, stages it, and moves it to the hypertable.
    """
    start_time = time.time()
    file_path = os.path.join(UPLOAD_DIR, f"dataset_{dataset_id}_{file.filename}")

    # 1. Basic Validation
    if not file.filename.endswith(".csv"):
        raise HTTPException(400, "Only .csv files are allowed.")

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # 2. Check if dataset exists
            cursor.execute("SELECT dataset_id FROM datasets WHERE dataset_id = %s", (dataset_id,))
            if not cursor.fetchone():
                raise HTTPException(404, f"Dataset ID {dataset_id} not found.")

            # 3. Check if signals already exist (Prevent Duplicates)
            cursor.execute("SELECT 1 FROM signals WHERE dataset_id = %s LIMIT 1", (dataset_id,))
            if cursor.fetchone():
                raise HTTPException(409, f"Signals for Dataset {dataset_id} already exist.")

        # 4. Stream file to disk (Low memory usage)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 5. Bulk Import Process
        with conn.cursor() as cursor:
            print(f"Starting import for Dataset {dataset_id}...")

            # A. Clear Staging
            cursor.execute("TRUNCATE TABLE signals_staging;")

            # B. Copy CSV to Staging
            with open(file_path, "r") as f:
                cursor.copy_expert("COPY signals_staging FROM STDIN WITH (FORMAT CSV, HEADER TRUE)", f)
            
            # C. Insert into Final Table (Fixing Time & Typo)
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
                    %s, -- dataset_id
                    CAST(time * 1000000 AS BIGINT), -- Convert Seconds -> Microseconds
                    header,
                    ax_alpha, ax_beta, ax_gamma,
                    ay_alpha, ay_beta, ay_gamma,
                    az_alpha, az_beta, az_gamma,
                    gx_alpha, gx_beta, gx_gamma,
                    gy_alpha, gy_beta, gy_gamma,
                    gz_alpha, gz_beta, gz_gamma,
                    ecg, 
                    frame_seperator -- Maps 'seperator' (CSV) to 'separator' (DB)
                FROM signals_staging;
            """
            cursor.execute(sql_transfer, (dataset_id,))
            row_count = cursor.rowcount
            
            # D. Cleanup
            cursor.execute("TRUNCATE TABLE signals_staging;")
            conn.commit()

            duration = round(time.time() - start_time, 2)
            print(f"✅ Inserted {row_count} rows in {duration}s.")

            return {
                "message": "Signal import successful",
                "dataset_id": dataset_id,
                "rows_inserted": row_count,
                "duration_seconds": duration
            }

    except Exception as e:
        conn.rollback()
        print(f"❌ Import failed: {e}")
        raise HTTPException(500, f"Import failed: {str(e)}")
        
    finally:
        conn.close()
