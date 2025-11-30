from fastapi import APIRouter
from db import get_connection

router = APIRouter()

@router.get("/dataset-rows/{dataset_id}")
def get_dataset_rows(dataset_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            dataset_id,
            time,
            header,
            ax_alpha, ax_beta, ax_gamma,
            ay_alpha, ay_beta, ay_gamma,
            az_alpha, az_beta, az_gamma,
            gx_alpha, gx_beta, gx_gamma,
            gy_alpha, gy_beta, gy_gamma,
            gz_alpha, gz_beta, gz_gamma,
            ecg,
            frame_separator
        FROM signals
        WHERE dataset_id = %s
        ORDER BY time ASC
        LIMIT 500;
    """, (dataset_id,))

    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return {
        "rows": [
            {
                "dataset_id": r["dataset_id"],
                "time": r["time"],
                "header": r["header"],

                "ax_alpha": r["ax_alpha"],
                "ax_beta": r["ax_beta"],
                "ax_gamma": r["ax_gamma"],

                "ay_alpha": r["ay_alpha"],
                "ay_beta": r["ay_beta"],
                "ay_gamma": r["ay_gamma"],

                "az_alpha": r["az_alpha"],
                "az_beta": r["az_beta"],
                "az_gamma": r["az_gamma"],

                "gx_alpha": r["gx_alpha"],
                "gx_beta": r["gx_beta"],
                "gx_gamma": r["gx_gamma"],

                "gy_alpha": r["gy_alpha"],
                "gy_beta": r["gy_beta"],
                "gy_gamma": r["gy_gamma"],

                "gz_alpha": r["gz_alpha"],
                "gz_beta": r["gz_beta"],
                "gz_gamma": r["gz_gamma"],

                "ecg": r["ecg"],
                "frame_separator": r["frame_separator"]
            }
            for r in rows
        ]
    }
