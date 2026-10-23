"""SQLAlchemy implementation of StockRepository.

Implements deterministic stock calculation using SHA-256.
Does not depend on database tables; it is pure computation.
"""

from __future__ import annotations

import hashlib
import random

from inventory.domain.entities.stock import Stock
from inventory.domain.repositories.stock_repository import StockRepository


class SqlAlchemyStockRepository(StockRepository):
    """StockRepository implementation with deterministic calculation."""

    def get_stock_level(
        self,
        seed: int,
        sku: str,
        store_id: str,
        max_stock: int = 450,
    ) -> Stock:
        """Calculates deterministic stock using SHA-256 of the compound identifier."""
        digest = hashlib.sha256(
            f"{seed}-{sku}-{store_id}".encode()
        ).digest()
        rng = random.Random(int.from_bytes(digest[:8], "big"))
        quantity = rng.randint(0, max_stock)

        return Stock(
            seed=seed,
            sku=sku,
            store_id=store_id,
            quantity=quantity,
            max_stock=max_stock,
        )
