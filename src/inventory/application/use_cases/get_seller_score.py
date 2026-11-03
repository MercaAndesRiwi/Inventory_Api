"""Use case for retrieving a seller's persisted score."""

from __future__ import annotations

from typing import Optional

from inventory.domain.entities.seller import SellerScore
from inventory.domain.repositories.seller_repository import SellerRepository


class GetSellerScoreUseCase:
    """Gets score data without recalculating it."""

    def __init__(self, seller_repository: SellerRepository):
        self.seller_repository = seller_repository

    def execute(self, seller_id: str) -> Optional[SellerScore]:
        """Return the score stored in Gold, or None if it is not available."""
        return self.seller_repository.get_score(seller_id)
