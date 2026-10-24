"""Dependency injection for FastAPI (inventory).

Connects the presentation layer with infrastructure and application.
"""

from __future__ import annotations

from typing import Generator, Optional

from fastapi import Depends
from sqlalchemy import Engine, create_engine
from sqlalchemy.engine import Connection

from inventory.infrastructure.config import (
    POS_DB_HOST,
    POS_DB_PORT,
    POS_DB_NAME,
    POS_DB_USER,
    POS_DB_PASSWORD,
    ERROR_RATE,
    ENABLE_NEGATIVE_INVENTORY,
    MAX_STOCK,
    VALID_TOKENS,
)
from inventory.infrastructure.persistence.sqlalchemy_seller_repository import (
    SqlAlchemySellerRepository,
)
from inventory.infrastructure.persistence.sqlalchemy_stock_repository import (
    SqlAlchemyStockRepository,
)
from inventory.domain.repositories.seller_repository import SellerRepository
from inventory.domain.repositories.stock_repository import StockRepository
from inventory.application.use_cases.get_seller_inventory import (
    GetSellerInventoryUseCase,
)
from inventory.application.use_cases.list_sellers import (
    ListSellersUseCase,
)
from inventory.application.use_cases.calculate_stock import (
    CalculateStockUseCase,
)

_engine: Optional[Engine] = None


def get_engine() -> Engine:
    """Get or lazily initialize the SQLAlchemy engine with connection pooling."""
    global _engine
    if _engine is None:
        if not POS_DB_NAME or not POS_DB_USER or not POS_DB_PASSWORD:
            raise RuntimeError(
                "PostgreSQL credentials are not configured. "
                "Set POS_DB_NAME, POS_DB_USER, and POS_DB_PASSWORD in .env"
            )
        database_url = (
            f"postgresql+psycopg://{POS_DB_USER}:{POS_DB_PASSWORD}"
            f"@{POS_DB_HOST}:{POS_DB_PORT}/{POS_DB_NAME}"
        )
        _engine = create_engine(database_url, pool_pre_ping=True)
    return _engine


def get_db_connection() -> Generator[Connection, None, None]:
    """Yield a PostgreSQL connection from the engine connection pool."""
    engine = get_engine()
    with engine.connect() as connection:
        yield connection


def get_seller_repository(
    connection: Connection = Depends(get_db_connection),
) -> SellerRepository:
    """Provide a PostgreSQL-backed SellerRepository."""
    return SqlAlchemySellerRepository(connection=connection)


def get_stock_repository() -> StockRepository:
    """Provide a StockRepository instance."""
    return SqlAlchemyStockRepository()


def get_seller_inventory_use_case(
    seller_repository: SellerRepository = Depends(get_seller_repository),
) -> GetSellerInventoryUseCase:
    """Provide the seller inventory use case."""
    return GetSellerInventoryUseCase(
        seller_repository=seller_repository,
        valid_tokens=VALID_TOKENS,
        error_rate=ERROR_RATE,
        enable_negative_inventory=ENABLE_NEGATIVE_INVENTORY,
        max_stock=MAX_STOCK,
    )


def get_calculate_stock_use_case(
    stock_repository: StockRepository = Depends(get_stock_repository),
) -> CalculateStockUseCase:
    """Provide the stock calculation use case."""
    return CalculateStockUseCase(stock_repository=stock_repository)


def get_list_sellers_use_case(
    seller_repository: SellerRepository = Depends(get_seller_repository),
) -> ListSellersUseCase:
    """Provide the list sellers use case."""
    return ListSellersUseCase(seller_repository=seller_repository)
