"""Use case: Calculate deterministic stock for a SKU in a store."""

from __future__ import annotations

from inventory.domain.entities.stock import Stock
from inventory.domain.repositories.stock_repository import StockRepository


class CalculateStockUseCase:
    """Use case for calculating deterministic stock."""

    def __init__(self, stock_repository: StockRepository):
        self.stock_repository = stock_repository

    def execute(
        self,
        seed: int,
        sku: str,
        store_id: str,
        max_stock: int = 450,
    ) -> Stock:
        """Calculates deterministic stock for a SKU in a store."""
        return self.stock_repository.get_stock_level(
            seed=seed,
            sku=sku,
            store_id=store_id,
            max_stock=max_stock,
        )
