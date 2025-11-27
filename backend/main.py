from fastapi import FastAPI
from routes.uploads import router as upload_router
import os
from fastapi.middleware.cors import CORSMiddleware
from routes.stats import router as stats_router


print("="*50)
print("🔥🔥🔥 MAIN.PY IS RUNNING! THIS FILE IS BEING LOADED. 🔥🔥🔥")
print(f"Current Working Directory: {os.getcwd()}")
print("="*50)

app = FastAPI(title="Sensor Data API")

app.include_router(upload_router, prefix="/api", tags=["Uploads"])

app.include_router(stats_router, prefix="/api", tags=["Stats"])

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



