"""SQLAlchemy implementation of SellerRepository.

Persists and queries sellers in the public.sellers table of PostgreSQL.
"""

from __future__ import annotations

from typing import List, Optional

from sqlalchemy import text
from sqlalchemy.engine import Connection

from inventory.domain.entities.seller import Seller, SellerScore
from inventory.domain.repositories.seller_repository import SellerRepository


class SqlAlchemySellerRepository(SellerRepository):
    """SellerRepository implementation using SQLAlchemy."""

    def __init__(self, connection: Connection):
        self.connection = connection

    def get_by_id(self, seller_id: str) -> Optional[Seller]:
        """Retrieves a seller by its ID from PostgreSQL."""
        result = self.connection.execute(
            text(
                """
                SELECT seller_id, name, seller_type, country
                FROM public.sellers
                WHERE seller_id = :seller_id
                """
            ),
            {"seller_id": seller_id},
        ).fetchone()

        if result is None:
            return None

        return Seller(
            seller_id=result[0],
            name=result[1],
            seller_type=result[2],
            country=result[3],
        )

    def list_all(self) -> List[Seller]:
        """Lists all sellers from PostgreSQL."""
        result = self.connection.execute(
            text(
                """
                SELECT seller_id, name, seller_type, country
                FROM public.sellers
                ORDER BY seller_id
                """
            ),
        ).fetchall()

        return [
            Seller(
                seller_id=row[0],
                name=row[1],
                seller_type=row[2],
                country=row[3],
            )
            for row in result
        ]

    def get_score(self, seller_id: str) -> Optional[SellerScore]:
        """Reads a stored score by canonical UUID or mapped API seller ID."""
        result = self.connection.execute(
            text(
                """
                SELECT score_row.seller_id, score_row.score, score_row.dispatch_pct,
                       score_row.review_rating, score_row.inventory_accuracy,
                       score_row.cancellation_rate, score_row.calculated_at
                FROM public.gold_seller_score score_row
                WHERE score_row.seller_id::text = :seller_id
                   OR EXISTS (
                       SELECT 1
                       FROM public.dim_seller_source_key seller_key
                       WHERE seller_key.source_system = 'inventory_api'
                         AND seller_key.source_seller_id = :seller_id
                         AND seller_key.seller_id::text = score_row.seller_id::text
                   )
                ORDER BY (score_row.seller_id::text = :seller_id) DESC
                LIMIT 1
                """
            ),
            {"seller_id": seller_id},
        ).fetchone()

        if result is None:
            return None

        return SellerScore(
            seller_id=result[0],
            score=result[1],
            dispatch_pct=result[2],
            review_rating=result[3],
            inventory_accuracy=result[4],
            cancellation_rate=result[5],
            calculated_at=result[6],
        )
