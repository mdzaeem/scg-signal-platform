from fastapi import FastAPI
from routes.uploads import router as upload_router
# We will add more routers here later (e.g., for querying)

app = FastAPI(title="Sensor Data API")

# Register upload route
app.include_router(upload_router, prefix="/api", tags=["Uploads"])

@app.get("/")
def read_root():
    return {"message": "Welcome to the Sensor Data API."}