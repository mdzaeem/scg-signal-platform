from fastapi import FastAPI
from routes.uploads import router as upload_router
import os

print("="*50)
print("🔥🔥🔥 MAIN.PY IS RUNNING! THIS FILE IS BEING LOADED. 🔥🔥🔥")
print(f"Current Working Directory: {os.getcwd()}")
print("="*50)

app = FastAPI(title="Sensor Data API")

app.include_router(upload_router, prefix="/api", tags=["Uploads"])

@app.get("/")
def read_root():
    return {"message": "Welcome to the Sensor Data API."}



