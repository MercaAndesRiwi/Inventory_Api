"""Use case: Get paginated seller inventory.

Orchestrates retrieval of seller information and their products,
applying token validation, fault injection, 10-minute snapshot updates,
and pagination over a pool of 50,000 SKUs.
"""

from __future__ import annotations

from datetime import datetime, timezone
import random
from typing import List, Optional

from inventory.domain.repositories.seller_repository import SellerRepository
from inventory.application.use_cases.dto import (
    InventoryItemDTO,
    PaginatedSellerInventoryDTO,
)

TOTAL_SKUS = 50_000
ALL_SKUS = [f"SKU-{i:05d}" for i in range(1, TOTAL_SKUS + 1)]


class GetSellerInventoryUseCase:
    """Use case for getting paginated seller inventory."""

    def __init__(
        self,
        seller_repository: SellerRepository,
        valid_tokens: List[str],
        error_rate: float = 0.03,
        enable_negative_inventory: bool = True,
        max_stock: int = 450,
    ):
        self.seller_repository = seller_repository
        self.valid_tokens = valid_tokens
        self.error_rate = max(0.03, error_rate) if error_rate > 0 else 0.0
        self.enable_negative_inventory = enable_negative_inventory
        self.max_stock = max_stock
        self.mock_skus = ALL_SKUS

    def validate_token(self, token: str) -> None:
        """Validates that the token is valid."""
        if token not in self.valid_tokens:
            raise PermissionError("Forbidden: Invalid seller token")

    def inject_fault(self) -> None:
        """Injects random faults (429 or 503) in at least 3% of requests."""
        if self.error_rate > 0 and random.random() < self.error_rate:
            error_status = random.choice([429, 503])
            if error_status == 429:
                raise RuntimeError("Rate limit exceeded. Try again later.")
            else:
                raise RuntimeError("Service temporarily unavailable (Simulated fault).")

    @staticmethod
    def get_time_window(as_of: Optional[datetime] = None) -> tuple[int, str]:
        """Calculates 10-minute time bucket and ISO 8601 window timestamp."""
        now = as_of or datetime.now(timezone.utc)
        ts = int(now.timestamp())
        bucket = ts // 600  # 600 seconds = 10 minutes

        window_minute = (now.minute // 10) * 10
        window_start = now.replace(minute=window_minute, second=0, microsecond=0)
        iso_str = window_start.strftime("%Y-%m-%dT%H:%M:%SZ")
        return bucket, iso_str

    def _generate_all_seller_items(
        self,
        seller_id: str,
        as_of: Optional[datetime] = None,
    ) -> List[InventoryItemDTO]:
        """Generates the full inventory list for a seller in the current 10-minute window."""
        seller_base_seed = sum(ord(c) for c in seller_id)
        catalog_rng = random.Random(seller_base_seed)

        # Each seller carries a stable catalog of products from the 50,000 SKUs pool
        num_products = catalog_rng.randint(25, 100)
        seller_skus = catalog_rng.sample(self.mock_skus, num_products)

        # Quantities refresh deterministically every 10 minutes
        time_bucket, updated_at = self.get_time_window(as_of)
        stock_rng = random.Random(seller_base_seed + time_bucket)

        inventory_data: List[InventoryItemDTO] = []
        for sku in seller_skus:
            if self.enable_negative_inventory and stock_rng.random() < 0.10:
                qty = stock_rng.randint(-10, -1)
            else:
                qty = stock_rng.randint(0, self.max_stock)

            inventory_data.append(
                InventoryItemDTO(
                    sku=sku,
                    quantity=qty,
                    updated_at=updated_at,
                )
            )

        return inventory_data

    def generate_inventory(
        self,
        seller_id: str,
        page: int,
        limit: int,
        sku: Optional[str] = None,
        as_of: Optional[datetime] = None,
    ) -> PaginatedSellerInventoryDTO:
        """Generates paginated inventory deterministically per seller and 10-min window."""
        # Fault injection (rate limit 429 or service unavailable 503)
        self.inject_fault()

        items = self._generate_all_seller_items(seller_id, as_of)

        if sku is not None:
            items = [item for item in items if item.sku.lower() == sku.strip().lower()]

        total_items = len(items)
        total_pages = (total_items + limit - 1) // limit if total_items > 0 else 0
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_data = items[start_idx:end_idx]

        return PaginatedSellerInventoryDTO(
            seller_id=seller_id,
            page=page,
            limit=limit,
            total_items=total_items,
            total_pages=total_pages,
            data=paginated_data,
        )

    def get_seller_sku_stock(
        self,
        seller_id: str,
        sku: str,
        token: str,
        as_of: Optional[datetime] = None,
    ) -> InventoryItemDTO:
        """Retrieves inventory for a specific seller and SKU."""
        self.validate_token(token)

        seller = self.seller_repository.get_by_id(seller_id)
        if seller is None:
            raise KeyError(f"Seller '{seller_id}' not found")

        self.inject_fault()

        items = self._generate_all_seller_items(seller_id, as_of)
        matched = next(
            (item for item in items if item.sku.lower() == sku.strip().lower()),
            None,
        )
        if matched is None:
            raise KeyError(
                f"SKU '{sku}' is not present in seller '{seller_id}' inventory"
            )
        return matched

    def execute(
        self,
        seller_id: str,
        page: int,
        limit: int,
        token: str,
        sku: Optional[str] = None,
        as_of: Optional[datetime] = None,
    ) -> PaginatedSellerInventoryDTO:
        """Executes the paginated seller inventory use case."""
        self.validate_token(token)

        seller = self.seller_repository.get_by_id(seller_id)
        if seller is None:
            raise KeyError(f"Seller '{seller_id}' not found")

        return self.generate_inventory(
            seller_id=seller_id,
            page=page,
            limit=limit,
            sku=sku,
            as_of=as_of,
        )
