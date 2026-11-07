"""Domain entity: Seller.

Represents a seller in the MercadAndes system.
No external framework dependencies (pure Python).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True)
class Seller:
    """Domain entity: Seller."""

    seller_id: str
    name: str
    seller_type: str  # "own" | "third_party"
    country: str

    @property
    def is_own(self) -> bool:
        """Indicates whether the seller is owned by MercaAndes."""
        return self.seller_type == "own"


@dataclass(frozen=True)
class SellerScore:
    """Persisted seller score and its component metrics."""

    seller_id: str
    score: Decimal
    dispatch_pct: Decimal
    review_rating: Decimal
    inventory_accuracy: Decimal
    cancellation_rate: Decimal
    calculated_at: datetime
    status: str = "active"
    penalties: tuple[str, ...] = ()
    reason: str = "active"
