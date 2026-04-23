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


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _cors_origins() -> list[str]:
    raw_origins = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:4200,http://127.0.0.1:4200",
    )
    return [origin.strip() for origin in raw_origins.split(",") if origin.strip()]


def _backend_path_from_env(name: str, default_relative: str) -> str:
    raw_value = os.getenv(name)
    path = raw_value if raw_value else os.path.join(BASE_DIR, default_relative)
    if os.path.isabs(path):
        return path
    return os.path.join(BASE_DIR, path)


DEBUG_MODE = _env_bool("DEBUG", False)


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
    allow_origins=_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for uploads
app.mount("/uploads", StaticFiles(directory=_backend_path_from_env("UPLOAD_DIR", "uploads")), name="uploads")

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(patients.router, prefix="/api/patients", tags=["patients"])
app.include_router(xray_analysis.router, prefix="/api/xray", tags=["xray-analysis"])

@app.get("/")
async def root():
    return {"message": "Medical System API is running"}

if DEBUG_MODE:
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
    uvicorn.run(
        "main:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", "8000")),
        reload=DEBUG_MODE,
    )
