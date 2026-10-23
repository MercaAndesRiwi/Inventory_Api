"""Use case: List all sellers."""

from __future__ import annotations

from typing import List

from inventory.domain.entities.seller import Seller
from inventory.domain.repositories.seller_repository import SellerRepository


class ListSellersUseCase:
    """Use case for listing all sellers."""

    def __init__(self, seller_repository: SellerRepository):
        self.seller_repository = seller_repository

    def execute(self) -> List[Seller]:
        """Returns all sellers."""
        return self.seller_repository.list_all()
