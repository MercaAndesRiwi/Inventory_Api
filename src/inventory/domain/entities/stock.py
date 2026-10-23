"""Stock domain entity."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Stock:
    """Domain entity representing stock for a SKU in a store."""

    sku: str
    store_id: str
    quantity: int
    max_stock: int
    seed: int

    @property
    def is_available(self) -> bool:
        """Returns True if stock is available."""
        return self.quantity > 0