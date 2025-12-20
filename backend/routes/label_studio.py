import os
import requests
from fastapi import APIRouter, HTTPException

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
