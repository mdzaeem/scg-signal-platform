import os
import requests
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from urllib.parse import parse_qs
from db import get_connection
import uuid

# MAX_LS_ROWS = 100000

router = APIRouter(prefix="/label-studio", tags=["Label Studio"])

LABEL_STUDIO_URL = os.getenv("LABEL_STUDIO_URL")
LABEL_STUDIO_API_KEY = os.getenv("LABEL_STUDIO_API_KEY")
LABEL_STUDIO_PROJECT_ID = os.getenv("LABEL_STUDIO_PROJECT_ID")

HEADERS = {
    "Authorization": f"Token {LABEL_STUDIO_API_KEY}",
    "Content-Type": "application/json",
}

@router.get("/health")
def health():
    r = requests.get(
        f"{LABEL_STUDIO_URL}/api/projects/",
        headers=HEADERS,
        timeout=10,
    )
    if r.status_code != 200:
        raise HTTPException(status_code=500, detail=r.text)
    return r.json()


@router.post("/create-test-task")
def create_test_task():
    payload = {
        "data": {
            "text": "Hello from FastAPI → Label Studio"
        }
    }

    r = requests.post(
        f"{LABEL_STUDIO_URL}/api/projects/{LABEL_STUDIO_PROJECT_ID}/tasks/",
        headers=HEADERS,
        json=payload,
        timeout=10,
    )

    if r.status_code != 201:
        raise HTTPException(status_code=500, detail=r.text)

    task = r.json()
    return {
        "task_id": task["id"],
        "url": f"{LABEL_STUDIO_URL}/projects/{LABEL_STUDIO_PROJECT_ID}/tasks/{task['id']}",
    }

def parse_filter_string(filter_q: str):
    """
    filter_q examples coming from frontend:
    "" 
    "&parabola=7"
    "&parabola_from=5&parabola_to=6"
    "?parabola_from=5&parabola_to=6"
    """
    if not filter_q:
        return None, None, None

    q = filter_q.lstrip("?&")
    parsed = parse_qs(q)

    def as_int(key: str):
        v = parsed.get(key)
        if not v:
            return None
        try:
            return int(v[0])
        except Exception:
            return None

    return as_int("parabola"), as_int("parabola_from"), as_int("parabola_to")


def resolve_time_window(cursor, dataset_id: int, parabola: int | None, parabola_from: int | None, parabola_to: int | None):
    """
    Same logic as dataset_rows.py:
    - single parabola -> its start/end
    - range -> MIN(start) + MAX(end)
    - no filter -> (None, None)
    """
    range_start = None
    range_end = None

    if parabola is not None:
        cursor.execute(
            """
            SELECT start_time, end_time
            FROM parabolas
            WHERE dataset_id = %s AND parabola_number = %s
            """,
            (dataset_id, parabola),
        )
        row = cursor.fetchone()
        if row:
            range_start = row["start_time"]
            range_end = row["end_time"]

    elif parabola_from is not None and parabola_to is not None:
        if parabola_from > parabola_to:
            raise HTTPException(status_code=400, detail="parabola_from must be <= parabola_to")

        cursor.execute(
            """
            SELECT
                MIN(start_time) AS range_start,
                MAX(end_time) AS range_end
            FROM parabolas
            WHERE dataset_id = %s
            AND parabola_number BETWEEN %s AND %s
            """,
            (dataset_id, parabola_from, parabola_to),
        )
        row = cursor.fetchone()
        if row and row["range_start"] is not None:
            range_start = row["range_start"]
            range_end = row["range_end"]

    return range_start, range_end



class PushToLabelStudioRequest(BaseModel):
    dataset_id: int
    filter: str = ""





def resolve_parabola_numbers(parabola, parabola_from, parabola_to):
    if parabola is not None:
        return [parabola]

    if parabola_from is not None and parabola_to is not None:
        if parabola_from > parabola_to:
            raise HTTPException(status_code=400, detail="parabola_from must be <= parabola_to")
        return list(range(parabola_from, parabola_to + 1))

    raise HTTPException(status_code=400, detail="No parabola filter provided")

def get_annotations_for_parabola(cursor, parabola_id: int):
    cursor.execute(
        """
        SELECT label, start_time, end_time
        FROM annotations
        WHERE parabola_id = %s
        ORDER BY start_time ASC
        """,
        (parabola_id,),
    )
    return cursor.fetchall()

# def build_ls_annotations(db_annotations):
#     """
#     Convert DB annotations → Label Studio annotation format
#     """
#     if not db_annotations:
#         return []

#     results = []

#     for ann in db_annotations:
#         results.append({
#             "id": str(uuid.uuid4()),
#             "from_name": "label",
#             "to_name": "ts",
#             "type": "timeserieslabels",
#             "value": {
#                 "start": float(ann["start_time"]),
#                 "end": float(ann["end_time"]),
#                 "timeserieslabels": [ann["label"]],
#             },
#         })

#     return [{
#         "result": results
#     }]

@router.post("/push")
def push_filtered_data_to_label_studio(payload: PushToLabelStudioRequest):
    dataset_id = payload.dataset_id
    filter_q = payload.filter or ""

    parabola, parabola_from, parabola_to = parse_filter_string(filter_q)
    parabola_numbers = resolve_parabola_numbers(parabola, parabola_from, parabola_to)

    conn = get_connection()
    cursor = conn.cursor()

    try:
        for p_no in parabola_numbers:
            # 1) Load parabola metadata
            cursor.execute("""
                SELECT parabola_id, start_time, end_time, parabola_name
                FROM parabolas
                WHERE dataset_id = %s AND parabola_number = %s
            """, (dataset_id, p_no))
            row = cursor.fetchone()
            if not row:
                continue

            parabola_id = row["parabola_id"]
            start_time = row["start_time"]
            end_time = row["end_time"]
            parabola_name = row["parabola_name"]

            # 2) Load signals
            cursor.execute("""
                SELECT time, ay_alpha, ay_beta, ay_gamma, ecg
                FROM signals
                WHERE dataset_id = %s AND time BETWEEN %s AND %s
                ORDER BY time ASC
            """, (dataset_id, start_time, end_time))
            rows = cursor.fetchall()
            if not rows:
                continue

            timeseries = {
                "time": [],
                "ay_alpha": [],
                "ay_beta": [],
                "ay_gamma": [],
                "ecg": [],
            }

            for r in rows:
                timeseries["time"].append(float(r["time"]))
                timeseries["ay_alpha"].append(r["ay_alpha"])
                timeseries["ay_beta"].append(r["ay_beta"])
                timeseries["ay_gamma"].append(r["ay_gamma"])
                timeseries["ecg"].append(r["ecg"])

            # 3) Load DB annotations
            cursor.execute("""
                SELECT label, start_time, end_time
                FROM annotations
                WHERE parabola_id = %s
                ORDER BY start_time
            """, (parabola_id,))
            db_annotations = cursor.fetchall()

            # 4) Convert to PREDICTIONS (THIS IS KEY)
            predictions = []
            for ann in db_annotations:
                predictions.append({
                    "id": str(uuid.uuid4()),
                    "from_name": "label",
                    "to_name": "ts",
                    "type": "timeserieslabels",
                    "value": {
                        "start": float(ann["start_time"]),
                        "end": float(ann["end_time"]),
                        "timeserieslabels": [ann["label"]],
                    },
                })

            # 5) Final payload
            task_payload = {
                "data": {
                    "task_name": parabola_name,
                    "timeseries": timeseries,
                },
                "meta": {
                    "dataset_id": dataset_id,
                    "parabola_id": parabola_id,
                    "parabola_number": p_no,
                },
            }

            if predictions:
                task_payload["predictions"] = [{
                    "result": predictions
                }]

            # 6) IMPORT
            resp = requests.post(
                f"{LABEL_STUDIO_URL}/api/projects/{LABEL_STUDIO_PROJECT_ID}/import",
                headers=HEADERS,
                json=[task_payload],
                timeout=30,
            )

            if resp.status_code not in (200, 201):
                raise HTTPException(status_code=500, detail=resp.text)

    finally:
        cursor.close()
        conn.close()

    return {
        "message": "Parabolas imported with predictions",
        "count": len(parabola_numbers),
    }



@router.post("/export")
def export_annotations_from_label_studio():
    conn = get_connection()
    cursor = conn.cursor()
    exported_segments = 0

    try:
        page = 1
        page_size = 100

        while True:
            r = requests.get(
                f"{LABEL_STUDIO_URL}/api/projects/{LABEL_STUDIO_PROJECT_ID}/tasks/",
                headers=HEADERS,
                params={"page": page, "page_size": page_size},
                timeout=30,
            )

            if r.status_code != 200:
                raise HTTPException(status_code=500, detail=r.text)

            resp = r.json()

            # Handle both paginated and non-paginated LS responses
            if isinstance(resp, list):
                tasks = resp
            else:
                tasks = resp.get("results", [])

            if not tasks:
                break

            for task in tasks:
                meta = task.get("meta") or {}
                parabola_id = meta.get("parabola_id")

                if parabola_id is None:
                    continue

                annotations = task.get("annotations") or []
                if not annotations:
                    continue

                # Delete old annotations for this parabola
                cursor.execute(
                    "DELETE FROM annotations WHERE parabola_id = %s",
                    (parabola_id,)
                )

                for ann in annotations:
                    for res in ann.get("result", []):
                        value = res.get("value", {})
                        labels = value.get("timeserieslabels")
                        if not labels:
                            continue

                        cursor.execute(
                            """
                            INSERT INTO annotations (parabola_id, label, start_time, end_time)
                            VALUES (%s, %s, %s, %s)
                            """,
                            (
                                parabola_id,
                                labels[0],
                                value.get("start"),
                                value.get("end"),
                            ),
                        )
                        exported_segments += 1

            if isinstance(resp, list) or resp.get("next") is None:
                break

            page += 1

        conn.commit()

    finally:
        cursor.close()
        conn.close()

    return {
        "message": "Annotations exported successfully",
        "segments_saved": exported_segments,
    }

