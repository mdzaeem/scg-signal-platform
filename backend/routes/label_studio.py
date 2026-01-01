import os
import requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from urllib.parse import parse_qs
from db import get_connection

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

@router.post("/push")
def push_filtered_data_to_label_studio(payload: PushToLabelStudioRequest):
    dataset_id = payload.dataset_id
    filter_q = payload.filter or ""

    parabola, parabola_from, parabola_to = parse_filter_string(filter_q)
    parabola_numbers = resolve_parabola_numbers(parabola, parabola_from, parabola_to)

    created_tasks = []

    conn = get_connection()
    cursor = conn.cursor()

    try:
        for p_no in parabola_numbers:
            # --------------------------------------------
            # 1) Resolve time window for THIS parabola
            # --------------------------------------------
            cursor.execute(
                """
                SELECT start_time, end_time
                FROM parabolas
                WHERE dataset_id = %s AND parabola_number = %s
                """,
                (dataset_id, p_no),
            )
            row = cursor.fetchone()
            if not row:
                continue

            start_time = row["start_time"]
            end_time = row["end_time"]

            # --------------------------------------------
            # 2) Fetch ALL rows for THIS parabola (NO LIMIT)
            # --------------------------------------------
            cursor.execute(
                """
                SELECT time, ay_alpha, ay_beta, ay_gamma, ecg
                FROM signals
                WHERE dataset_id = %s
                AND time BETWEEN %s AND %s
                ORDER BY time ASC
                """,
                (dataset_id, start_time, end_time),
            )
            rows = cursor.fetchall()
            if not rows:
                continue

            # --------------------------------------------
            # Fetch dataset metadata ONCE
            # --------------------------------------------
            cursor.execute(
                """
                SELECT flight_code, person_name
                FROM datasets
                WHERE dataset_id = %s
                """,
                (dataset_id,),
            )
            ds = cursor.fetchone()

            if not ds:
                raise HTTPException(status_code=404, detail="Dataset not found")

            flight_code = ds["flight_code"] or "FX"
            person_name = ds["person_name"] or "Unknown"


            # --------------------------------------------
            # 3) Convert to timeseries
            # --------------------------------------------
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

            task_payload = {
                "data": {
                    "task_name": f"{flight_code} {person_name} P{p_no}",
                    "timeseries": timeseries
                },
                "meta": {
                    "dataset_id": dataset_id,
                    "parabola_number": p_no,
                    "start_time": start_time,
                    "end_time": end_time,
                }
            }

            # --------------------------------------------
            # 4) Push ONE task to Label Studio
            # --------------------------------------------
            try:
                ls_resp = requests.post(
                    f"{LABEL_STUDIO_URL}/api/projects/{LABEL_STUDIO_PROJECT_ID}/tasks/",
                    headers=HEADERS,
                    json=task_payload,
                    timeout=30,
                )
            except requests.RequestException as e:
                raise HTTPException(status_code=502, detail=str(e))

            if ls_resp.status_code != 201:
                raise HTTPException(status_code=500, detail=ls_resp.text)

            created_tasks.append({
                "parabola": p_no,
                "task_id": ls_resp.json()["id"],
            })

    finally:
        cursor.close()
        conn.close()

    return {
        "message": "Parabola tasks created",
        "tasks_created": created_tasks,
        "count": len(created_tasks),
    }

# #lines skiupped bit working 
# @router.post("/push")
# def push_filtered_data_to_label_studio(payload: PushToLabelStudioRequest):
#     dataset_id = payload.dataset_id
#     filter_q = payload.filter or ""


#     # --------------------------------------------
#     # 1) Fetch filtered rows directly from DB (NO self-HTTP)
#     # --------------------------------------------
#     parabola, parabola_from, parabola_to = parse_filter_string(filter_q)

#     conn = get_connection()
#     cursor = conn.cursor()
#     try:
#         range_start, range_end = resolve_time_window(
#             cursor,
#             dataset_id,
#             parabola,
#             parabola_from,
#             parabola_to
#         )

#         print(
#         f"[LS PUSH] dataset={dataset_id}, "
#         f"parabola={parabola}, "
#         f"range=({parabola_from},{parabola_to}), "
#         f"time_window=({range_start},{range_end})"
#         )

#         where_clause = "dataset_id = %s"
#         params = [dataset_id]

#         if range_start is not None and range_end is not None:
#             where_clause += " AND time BETWEEN %s AND %s"
#             params.extend([range_start, range_end])

#         cursor.execute(
#             f"""
#             SELECT time, ay_alpha, ay_beta, ay_gamma, ecg
#             FROM signals
#             WHERE {where_clause}
#             ORDER BY time ASC
#             LIMIT %s;
#             """,
#             (*params, MAX_LS_ROWS),
#         )

#         rows = cursor.fetchall()

#         if not rows:
#             raise HTTPException(status_code=400, detail="No rows found for given filter")

#         if len(rows) >= MAX_LS_ROWS:
#             print(f"⚠️ Truncated rows to MAX_LS_ROWS={MAX_LS_ROWS}")


#     finally:
#         cursor.close()
#         conn.close()


#     # --------------------------------------------
#     # 2. Convert rows → TimeSeries format
#     # --------------------------------------------
#     timeseries = {
#         "time": [],
#         "ay_alpha": [],
#         "ay_beta": [],
#         "ay_gamma": [],
#         "ecg": []
#     }

#     for row in rows:
#         timeseries["time"].append(float(row["time"]))
#         timeseries["ay_alpha"].append(row["ay_alpha"])
#         timeseries["ay_beta"].append(row["ay_beta"])
#         timeseries["ay_gamma"].append(row["ay_gamma"])
#         timeseries["ecg"].append(row["ecg"])


#     task_payload = {
#         "data": {
#             "timeseries": timeseries
#         },
#         "meta": {
#             "dataset_id": dataset_id,
#             "filter": filter_q,
#         }
#     }

#     # --------------------------------------------
#     # 3. Push task to Label Studio
#     # --------------------------------------------
#     try:
#         ls_resp = requests.post(
#             f"{LABEL_STUDIO_URL}/api/projects/{LABEL_STUDIO_PROJECT_ID}/tasks/",
#             headers=HEADERS,
#             json=task_payload,
#             timeout=30,
#         )
#     except requests.RequestException as e:
#         raise HTTPException(
#             status_code=502,
#             detail=f"Label Studio request failed: {e}"
#         )

#     if ls_resp.status_code != 201:
#         raise HTTPException(status_code=500, detail=ls_resp.text)

#     task = ls_resp.json()

#     return {
#         "message": "Task pushed to Label Studio",
#         "task_id": task["id"],
#         "task_url": f"{LABEL_STUDIO_URL}/projects/{LABEL_STUDIO_PROJECT_ID}/tasks/{task['id']}",
#         "rows_sent": len(rows),
#     }


