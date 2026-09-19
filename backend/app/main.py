from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, status
from fastapi.responses import JSONResponse

from app.db import check_db_health, close_pool, init_pool


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
    version="0.1.0",
    description="API for AgenticShop AI Business Analyst.",
    lifespan=lifespan,
)


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

