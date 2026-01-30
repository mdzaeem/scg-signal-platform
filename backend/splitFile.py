import pandas as pd
import os
import json
from math import ceil

# ====== CONFIG ======
INPUT_CSV = r"D:\Documents\Projects\SCG-labelling\backend\bulk_uploads\dataset1\Artifacts_F6_BBox2_Orange_Subject_KAZI_30.10.2025.csv"

OUTPUT_DIR = r"D:\Documents\Projects\SCG-labelling\backend\bulk_uploads\dataset1"

NUM_PARTS = 30
# ====================

# Create output directory
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Read CSV ONCE
df = pd.read_csv(INPUT_CSV)

# Assume:
# column 0 = time
# column 1..N = signals
time_col = df.columns[0]
signal_cols = df.columns[1:]

# Rows per chunk
rows_per_part = ceil(len(df) / NUM_PARTS)

created = 0

for i in range(NUM_PARTS):
    start = i * rows_per_part
    end = start + rows_per_part
    part_df = df.iloc[start:end]

    if part_df.empty:
        break

    # Build Label Studio TimeSeries JSON
    task = {
        "data": {
            "ts": {
                "time": part_df[time_col].tolist(),
                "series": [
                    {
                        "name": col,
                        "value": part_df[col].tolist()
                    }
                    for col in signal_cols
                ]
            }
        }
    }

    out_path = os.path.join(OUTPUT_DIR, f"part_{i+1}.json")

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(task, f)

    created += 1

print(f"Done ✅ Created {created} JSON files in:\n{OUTPUT_DIR}")
