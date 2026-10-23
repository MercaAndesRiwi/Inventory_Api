"""Unit tests for deterministic inventory calculation."""

from inventory.application.use_cases.calculate_stock import CalculateStockUseCase
from inventory.infrastructure.persistence.sqlalchemy_stock_repository import (
    SqlAlchemyStockRepository,
)


class FakeStockRepository:
    """Fake repository for stock tests."""

    def __init__(self, stock_value: int = 42):
        self._stock_value = stock_value

    def get_stock_level(self, seed: int, sku: str, store_id: str, max_stock: int = 450):
        return type(
            "Stock",
            (),
            {
                "sku": sku,
                "store_id": store_id,
                "seed": seed,
                "quantity": self._stock_value,
                "max_stock": max_stock,
                "is_available": self._stock_value > 0,
            },
        )()


def test_stock_level_is_deterministic():
    """Same input must return the same stock."""
    repo = FakeStockRepository()
    use_case = CalculateStockUseCase(stock_repository=repo)

    result1 = use_case.execute(seed=42, sku="SKU-001", store_id="STO-CO-FIS-001")
    result2 = use_case.execute(seed=42, sku="SKU-001", store_id="STO-CO-FIS-001")

    assert result1.quantity == result2.quantity
    assert result1.sku == result2.sku
    assert result1.store_id == result2.store_id


def test_stock_level_within_bounds():
    """Stock must be between 0 and max_stock."""
    repo = FakeStockRepository()
    use_case = CalculateStockUseCase(stock_repository=repo)

    result = use_case.execute(seed=42, sku="SKU-001", store_id="STO-CO-FIS-001")

    assert 0 <= result.quantity <= result.max_stock


def test_sqlalchemy_stock_repository_deterministic():
    """The real repository must be deterministic."""
    repo = SqlAlchemyStockRepository()
    result1 = repo.get_stock_level(seed=42, sku="SKU-001", store_id="STO-CO-FIS-001")
    result2 = repo.get_stock_level(seed=42, sku="SKU-001", store_id="STO-CO-FIS-001")

    assert result1.quantity == result2.quantity
    assert result1.sku == result2.sku
    assert result1.store_id == result2.store_id
