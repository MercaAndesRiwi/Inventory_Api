"""Data Transfer Objects for the application layer.

DTOs that transport data between the presentation layer and use cases,
without depending on external frameworks (neither Pydantic nor SQLAlchemy).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class InventoryItemDTO:
    """DTO for an inventory item."""

    sku: str
    quantity: int
    updated_at: str


@dataclass
class PaginatedSellerInventoryDTO:
    """DTO for the paginated seller inventory response."""

    seller_id: str
    page: int
    limit: int
    total_items: int
    total_pages: int
    data: List[InventoryItemDTO]


@dataclass
class StockDTO:
    """DTO for stock calculation."""

    sku: str
    store_id: str
    seed: int
    quantity: int
    max_stock: int

