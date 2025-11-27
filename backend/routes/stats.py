from fastapi import APIRouter
from db import get_connection

router = APIRouter()

@router.get("/stats")
def get_stats():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM datasets")
    datasets = cursor.fetchone()["count"]

    cursor.execute("SELECT COUNT(*) FROM persons")
    persons = cursor.fetchone()["count"]

    cursor.execute("SELECT COUNT(*) FROM flights")
    flights = cursor.fetchone()["count"]

    cursor.execute("SELECT COUNT(*) FROM boxes")
    boxes = cursor.fetchone()["count"]

    #cursor.execute("SELECT COUNT(*) FROM parabolas")
    parabolas = 0

    cursor.close()
    conn.close()

    return {
        "datasets": datasets,
        "persons": persons,
        "flights": flights,
        "boxes": boxes,
        "parabolas": parabolas
    }