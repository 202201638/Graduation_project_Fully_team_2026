from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.routers import auth, patients, xray_analysis
from app.database.mongodb import connect_to_mongodb, close_mongodb_connection
import uvicorn
import os

app = FastAPI(
    title="Medical System API",
    description="AI-Powered X-Ray Chest Diagnosis Backend",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],  # Angular frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for uploads
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(patients.router, prefix="/api/patients", tags=["patients"])
app.include_router(xray_analysis.router, prefix="/api/xray", tags=["xray-analysis"])

# MongoDB connection events
@app.on_event("startup")
async def startup_event():
    await connect_to_mongodb()

@app.on_event("shutdown")
async def shutdown_event():
    await close_mongodb_connection()

@app.get("/")
async def root():
    return {"message": "Medical System API is running"}

@app.get("/debug")
async def debug_info():
    """Debug endpoint to show all available routes"""
    from fastapi.routing import APIRoute
    routes = []
    for route in app.routes:
        if isinstance(route, APIRoute):
            routes.append({
                "path": route.path,
                "methods": list(route.methods),
                "name": route.name
            })
    return {
        "message": "Debug info",
        "total_routes": len(routes),
        "routes": routes
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "Medical System API"}

@app.get("/favicon.ico")
async def favicon():
    """Return favicon or 204 if not found"""
    favicon_path = "static/favicon.ico"
    if os.path.exists(favicon_path):
        return FileResponse(favicon_path)
    else:
        return {"message": "No favicon"}, 204

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
