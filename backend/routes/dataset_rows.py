from fastapi import APIRouter
from db import get_connection

router = APIRouter()

@router.get("/dataset-rows/{dataset_id}")
def get_dataset_rows(
    dataset_id: int,
    offset: int = 0,
    limit: int = 200,
    parabola: int | None = None,
    parabola_from: int | None = None,
    parabola_to: int | None = None,
):
    conn = get_connection()
    cursor = conn.cursor()

    if parabola_from is not None and parabola_to is not None:
        if parabola_from > parabola_to:
            raise ValueError("parabola_from must be <= parabola_to")


    # --------------------------------------------------
# STEP 1: Fetch ONE parabola time range (if filter exists)
# --------------------------------------------------
    range_start = None
    range_end = None

    # Case A: single parabola -> use its start/end
    if parabola is not None:
        cursor.execute(
            """
            SELECT
                start_time,
                end_time
            FROM parabolas
            WHERE dataset_id = %s
            AND parabola_number = %s
            """,
            (dataset_id, parabola),
        )

        row = cursor.fetchone()
        if row:
            range_start = row["start_time"]
            range_end = row["end_time"]

    # Case B: parabola range -> start of parabola_from, end of parabola_to
    elif parabola_from is not None and parabola_to is not None:
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


    # --------------------------------------------------
    # STEP 2: Build dynamic WHERE clause
    # --------------------------------------------------
    where_clause = "dataset_id = %s"
    params = [dataset_id]

    if range_start is not None and range_end is not None:
        where_clause += " AND time BETWEEN %s AND %s"
        params.extend([range_start, range_end])

    cursor.execute(
    f"SELECT COUNT(*) FROM signals WHERE {where_clause};",
    params,
    )
    total_rows = cursor.fetchone()["count"]

    cursor.execute(
        f"""
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
        WHERE {where_clause}
        ORDER BY time ASC
        LIMIT %s OFFSET %s;
        """,
        (*params, limit, offset),
    )

    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return {
        "total_rows": total_rows,
        "rows": rows,
    }

    # return {
    #     "total_rows": total_rows,
    #     "rows": [
    #         {
    #             "dataset_id": r["dataset_id"],
    #             "time": r["time"],
    #             "header": r["header"],
    #             "ax_alpha": r["ax_alpha"],
    #             "ax_beta": r["ax_beta"],
    #             "ax_gamma": r["ax_gamma"],
    #             "ay_alpha": r["ay_alpha"],
    #             "ay_beta": r["ay_beta"],
    #             "ay_gamma": r["ay_gamma"],
    #             "az_alpha": r["az_alpha"],
    #             "az_beta": r["az_beta"],
    #             "az_gamma": r["az_gamma"],
    #             "gx_alpha": r["gx_alpha"],
    #             "gx_beta": r["gx_beta"],
    #             "gx_gamma": r["gx_gamma"],
    #             "gy_alpha": r["gy_alpha"],
    #             "gy_beta": r["gy_beta"],
    #             "gy_gamma": r["gy_gamma"],
    #             "gz_alpha": r["gz_alpha"],
    #             "gz_beta": r["gz_beta"],
    #             "gz_gamma": r["gz_gamma"],
    #             "ecg": r["ecg"],
    #             "frame_separator": r["frame_separator"],
    #         }
    #         for r in rows
    #     ],
    # }
