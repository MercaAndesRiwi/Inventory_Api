"""Minimal inventory snapshot (F3).

Stock per (sku, store) is deterministic from (seed, sku, store_id).

Built-in validations (autonomous, without relying on an external orchestrator):
- Validates that MASTER_SEED is a valid integer.
- Validates that MAX_STOCK is a positive integer.
- Validates that sku and store_id are not empty.
"""

from __future__ import annotations

import hashlib
import random
import sys

from inventory.config import MASTER_SEED, MAX_STOCK


def validate_environment() -> None:
    """Validates that inventory environment variables are correct."""
    if MASTER_SEED <= 0:
        print(f"ERROR: MASTER_SEED must be a positive integer. Current value: {MASTER_SEED}")
        sys.exit(1)

    if MAX_STOCK <= 0:
        print(f"ERROR: MAX_STOCK must be a positive integer. Current value: {MAX_STOCK}")
        sys.exit(1)

    print("Environment validation: OK")


def stock_level(
    seed: int,
    sku: str,
    store_id: str,
    max_stock: int = 450,
) -> int:
    """Deterministic on-hand units for one SKU in one store."""
    if not sku or not sku.strip():
        raise ValueError("sku must not be empty.")
    if not store_id or not store_id.strip():
        raise ValueError("store_id must not be empty.")
    if max_stock <= 0:
        raise ValueError("max_stock must be a positive integer.")
    if seed <= 0:
        raise ValueError("seed must be a positive integer.")

    digest = hashlib.sha256(
        f"{seed}-{sku}-{store_id}".encode()
    ).digest()
    rng = random.Random(int.from_bytes(digest[:8], "big"))
    return rng.randint(0, max_stock)


def main() -> None:
    """Example usage of stock calculation."""
    validate_environment()

    sku = "SKU-HEALTH-CO-00001"
    store_id = "STO-CO-FIS-001"

    if not sku or not store_id:
        print("ERROR: sku and store_id must not be empty.")
        sys.exit(1)

    level = stock_level(MASTER_SEED, sku, store_id, MAX_STOCK)
    print(f"Stock for {sku} at {store_id}: {level}")


if __name__ == "__main__":
    main()
