import os
import requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import csv
import uuid
from pathlib import Path



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


class PushToLabelStudioRequest(BaseModel):
    dataset_id: int
    filter: str = ""
    
@router.post("/push")
def push_filtered_data_to_label_studio(payload: PushToLabelStudioRequest):
    dataset_id = payload.dataset_id
    filter_q = payload.filter or ""

    # --------------------------------------------
    # 1. Fetch ALL filtered rows from backend API
    # --------------------------------------------
    url = (
        f"http://127.0.0.1:8000/api/dataset-rows/{dataset_id}"
        f"?offset=0&limit=1000000{filter_q}"
    )

    r = requests.get(url, timeout=30)
    if r.status_code != 200:
        raise HTTPException(status_code=500, detail=r.text)

    data = r.json()
    rows = data.get("rows", [])

    if not rows:
        raise HTTPException(status_code=400, detail="No rows found for given filter")

    # --------------------------------------------
    # 2. Convert rows → TimeSeries format
    # --------------------------------------------
    timeseries = {
    "time": [],
    "ay_alpha": [],
    "ay_beta": [],
    "ay_gamma": [],
    "ecg": []
}

    for row in rows:
        timeseries["time"].append(float(row["time"]))
        timeseries["ay_alpha"].append(row["ay_alpha"])
        timeseries["ay_beta"].append(row["ay_beta"])
        timeseries["ay_gamma"].append(row["ay_gamma"])
        timeseries["ecg"].append(row["ecg"])


    task_payload = {
        "data": {
            "timeseries": timeseries
        },
        "meta": {
            "dataset_id": dataset_id,
            "filter": filter_q,
        }
    }

    # --------------------------------------------
    # 3. Push task to Label Studio
    # --------------------------------------------
    ls_resp = requests.post(
        f"{LABEL_STUDIO_URL}/api/projects/{LABEL_STUDIO_PROJECT_ID}/tasks/",
        headers=HEADERS,
        json=task_payload,
        timeout=30,
    )

    if ls_resp.status_code != 201:
        raise HTTPException(status_code=500, detail=ls_resp.text)

    task = ls_resp.json()

    return {
        "message": "Task pushed to Label Studio",
        "task_id": task["id"],
        "task_url": f"{LABEL_STUDIO_URL}/projects/{LABEL_STUDIO_PROJECT_ID}/tasks/{task['id']}",
        "rows_sent": len(rows),
    }


