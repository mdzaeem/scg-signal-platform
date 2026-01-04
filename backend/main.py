from fastapi import FastAPI
from routes.uploads import router as upload_router
import os
from fastapi.middleware.cors import CORSMiddleware
from routes.stats import router as stats_router
from routes.datasets import router as datasets_router
from routes.dataset_rows import router as dataset_rows_router
from routes.parabola import router as parabola_router
from routes.label_studio import router as label_studio_router
from fastapi.staticfiles import StaticFiles


print("="*50)
print("🔥🔥🔥 MAIN.PY IS RUNNING! THIS FILE IS BEING LOADED. 🔥🔥🔥")
print(f"Current Working Directory: {os.getcwd()}")
print("="*50)

app = FastAPI(title="Sensor Data API")

app.include_router(upload_router, prefix="/api", tags=["Uploads"])

app.include_router(stats_router, prefix="/api", tags=["Stats"])

app.include_router(datasets_router, prefix="/api", tags=["Datasets"])

app.include_router(dataset_rows_router, prefix="/api", tags=["Dataset Rows"])

app.include_router(parabola_router, prefix="/api", tags=["Parabolas"])

app.include_router(label_studio_router, prefix="/api", tags=["Label Studio"])

app.mount(
    "/files",
    StaticFiles(directory="uploads/label_studio"),
    name="label-studio-files",
)

allow_origins=[
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "Welcome to the Sensor Data API."}



