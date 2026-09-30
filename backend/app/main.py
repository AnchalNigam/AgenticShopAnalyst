from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.db import check_db_health, close_pool, init_pool
from app.routes.analyst import router as analyst_router
from app.routes.analyst_v2 import router as analyst_v2_router

STATIC_DIR = Path(__file__).resolve().parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage lifecycle resources, such as the database connection pool."""
    init_pool()
    try:
        yield
    finally:
        close_pool()


app = FastAPI(
    title="AgenticShop AI Business Analyst API",
    version="0.2.0",
    description="API for AgenticShop AI Business Analyst (V1 Reactive & V2 Plan-and-Solve).",
    lifespan=lifespan,
)

# Enable CORS for local web development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(analyst_router, prefix="/api/v1/analyst", tags=["analyst"])
app.include_router(analyst_v2_router, prefix="/api/v2/analyst", tags=["analyst_v2"])

# Mount static files and serve Web UI at root
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def serve_ui() -> FileResponse:
    """Serve the interactive AgenticShop web UI."""
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health", tags=["system"])
def health_check():
    """Verify service liveness and database connectivity."""
    db_alive = check_db_health()
    status_code = status.HTTP_200_OK if db_alive else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "ok" if db_alive else "degraded",
            "database": "connected" if db_alive else "disconnected",
        },
    )


