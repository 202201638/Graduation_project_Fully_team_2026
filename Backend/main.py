from contextlib import asynccontextmanager
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool
from app.routers import auth, patients, xray_analysis
from app.database.mongodb import (
    close_mongodb_connection,
    connect_to_mongodb,
    get_database_status,
)
from app.utils.xray_inference import xray_inference_service
import uvicorn

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


@asynccontextmanager
async def lifespan(_: FastAPI):
    await connect_to_mongodb()
    await run_in_threadpool(xray_inference_service.warmup)
    try:
        yield
    finally:
        await close_mongodb_connection()


app = FastAPI(
    title="Medical System API",
    description="AI-Powered X-Ray Chest Diagnosis Backend",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://127.0.0.1:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for uploads
app.mount("/uploads", StaticFiles(directory=os.path.join(BASE_DIR, "uploads")), name="uploads")

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(patients.router, prefix="/api/patients", tags=["patients"])
app.include_router(xray_analysis.router, prefix="/api/xray", tags=["xray-analysis"])

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
    model_status = xray_inference_service.get_status()
    database_status = get_database_status()

    overall_status = (
        "healthy"
        if model_status["weights_exists"] and not model_status.get("load_error")
        else "degraded"
    )

    return {
        "status": overall_status,
        "service": "Medical System API",
        "model": model_status,
        "database": database_status,
    }

@app.get("/favicon.ico")
async def favicon():
    """Return favicon or 204 if not found"""
    favicon_path = os.path.join(BASE_DIR, "static", "favicon.ico")
    if os.path.exists(favicon_path):
        return FileResponse(favicon_path)
    return Response(status_code=204)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
