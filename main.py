from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from routes import router

app = FastAPI(title="Ride Dispatch System")

# Mount static files for frontend
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include all routes
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 