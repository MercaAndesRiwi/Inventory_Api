"""Domain entity: Seller.

Represents a seller in the MercadAndes system.
No external framework dependencies (pure Python).
"""

from __future__ import annotations

from dataclasses import dataclass


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
