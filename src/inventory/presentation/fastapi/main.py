"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware

from inventory.infrastructure.persistence.seed_sellers import main as seed_db
from inventory.presentation.fastapi.routes import sellers as sellers_routes
from inventory.presentation.fastapi.routes import stock as stock_routes


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Automatically initialize database schema and seed sellers on startup if reachable."""
    try:
        seed_db()
    except Exception as exc:
        print(f"Notice: Database auto-seed skipped or failed: {exc}")
    yield


app = FastAPI(
    title="Seller Inventory Simulator API (F3)",
    version="1.0.0",
    description="Mock REST API for seller inventory simulation featuring pagination, rate limits, and intermittent error injection.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sellers_routes.router)
app.include_router(stock_routes.router)


@app.get("/", tags=["health"], response_model=dict, status_code=status.HTTP_200_OK)
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "api-inventory", "version": "1.0.0"}
