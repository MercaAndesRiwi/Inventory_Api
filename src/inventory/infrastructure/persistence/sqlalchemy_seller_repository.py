"""SQLAlchemy implementation of SellerRepository.

Persists and queries sellers in the public.sellers table of PostgreSQL.
"""

from __future__ import annotations

from typing import List, Optional

from sqlalchemy import text
from sqlalchemy.engine import Connection

from inventory.domain.entities.seller import Seller
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
