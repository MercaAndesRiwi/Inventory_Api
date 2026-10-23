"""FastAPI application entry point."""

from fastapi import FastAPI, status

from inventory.presentation.fastapi.routes import sellers as sellers_routes
from inventory.presentation.fastapi.routes import stock as stock_routes


app = FastAPI(
    title="Seller Inventory Simulator API (F3)",
    version="1.0.0",
    description="Mock REST API for seller inventory simulation featuring pagination, rate limits, and intermittent error injection.",
)

app.include_router(sellers_routes.router)
app.include_router(stock_routes.router)


@app.get("/", tags=["health"], response_model=dict, status_code=status.HTTP_200_OK)
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "api-inventory", "version": "1.0.0"}
