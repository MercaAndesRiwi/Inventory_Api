"""Route for calculating deterministic stock."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from inventory.application.use_cases.calculate_stock import (
    CalculateStockUseCase,
)
from inventory.presentation.fastapi.deps import get_calculate_stock_use_case

router = APIRouter(prefix="/api/v1/inventory", tags=["inventory"])


@router.get(
    "/stock",
    summary="Get Stock Level",
    description="Calculates deterministic stock for one SKU in one store.",
)
def get_stock_level(
    sku: str = Query(..., description="Product SKU"),
    store_id: str = Query(..., description="Store ID"),
    seed: int = Query(42, description="Seed for deterministic calculation"),
    max_stock: int = Query(450, ge=1, le=10000, description="Maximum possible stock"),
    use_case: CalculateStockUseCase = Depends(get_calculate_stock_use_case),
):
    stock = use_case.execute(
        seed=seed,
        sku=sku,
        store_id=store_id,
        max_stock=max_stock,
    )

    return {
        "sku": stock.sku,
        "store_id": stock.store_id,
        "seed": stock.seed,
        "quantity": stock.quantity,
        "max_stock": stock.max_stock,
        "is_available": stock.is_available,
    }
