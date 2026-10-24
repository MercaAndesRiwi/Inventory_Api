"""Domain repository interface for Stock.

Defines the contract for calculating or retrieving deterministic stock.
"""

from __future__ import annotations

from inventory.domain.entities.stock import Stock


class StockRepository:
    """Repository interface for stock calculation."""

    def get_stock_level(
        self,
        seed: int,
        sku: str,
        store_id: str,
        max_stock: int = 450,
    ) -> Stock:
        """Calculates deterministic stock for a SKU in a store."""
        raise NotImplementedError
