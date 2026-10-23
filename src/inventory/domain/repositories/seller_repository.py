"""Domain repository interface for Seller.

Defines the contract that any seller persistence implementation must fulfill.
No external framework dependencies.
"""

from __future__ import annotations

from typing import List, Optional

from inventory.domain.entities.seller import Seller


class SellerRepository:
    """Repository interface for sellers."""

    def get_by_id(self, seller_id: str) -> Optional[Seller]:
        """Retrieves a seller by its ID."""
        raise NotImplementedError

    def list_all(self) -> List[Seller]:
        """Lists all sellers."""
        raise NotImplementedError
