"""LAWDECODE Main Application.

FastAPI entrypoint serving:
- REST API routes (/api/health, /api/agents, /api/analyze)
- Interactive web frontend at root (/)
"""

from pathlib import Path
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from core.config import settings, BASE_DIR
from api.routes import router as api_router

# Initialize FastAPI app
app = FastAPI(
    title="LAWDECODE",
    description="Legal document analysis and assistive intelligence platform",
    version=settings.PROJECT_VERSION,
)

# CORS middleware for seamless local and portable client interaction
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router)

# Mount frontend directory
frontend_dir = BASE_DIR / "frontend"
if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")

    @app.get("/", include_in_schema=False)
    async def serve_index():
        """Serve the LAWDECODE single page application."""
        return FileResponse(frontend_dir / "index.html")


if __name__ == "__main__":
    print("=" * 60)
    print(" LAWDECODE - Phase 1 Server Starting")
    print(f" URL: http://{settings.HOST}:{settings.PORT}")
    print(f" API Docs: http://{settings.HOST}:{settings.PORT}/docs")
    print(f" Gemini Key Status: {settings.api_key_status}")
    print("=" * 60)
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=True)
