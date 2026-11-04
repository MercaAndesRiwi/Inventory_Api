"""Unit tests for the Sellers API (Sellers - F3)."""

from datetime import datetime, timezone, timedelta
import pytest
from inventory.application.use_cases.get_seller_inventory import (
    GetSellerInventoryUseCase,
    TOTAL_SKUS,
)
from inventory.domain.entities.seller import Seller


class FakeSellerRepository:
    """Fake repository for tests."""

    def __init__(self, sellers=None):
        self._sellers = sellers or {}

    def get_by_id(self, seller_id: str):
        return self._sellers.get(seller_id)

    def list_all(self):
        return list(self._sellers.values())


def test_get_seller_inventory_valid_token():
    """Must return inventory with a valid token."""
    repo = FakeSellerRepository(
        {
            "SEL-001": Seller(
                seller_id="SEL-001",
                name="MercaAndes Retail Colombia",
                seller_type="own",
                country="CO",
            )
        }
    )
    use_case = GetSellerInventoryUseCase(
        seller_repository=repo,
        valid_tokens=["valid-token"],
        error_rate=0.0,
    )

    result = use_case.execute(
        seller_id="SEL-001",
        page=1,
        limit=10,
        token="valid-token",
    )

    assert result.seller_id == "SEL-001"
    assert result.page == 1
    assert result.limit == 10
    assert result.total_items > 0
    assert len(result.data) <= 10


def test_get_seller_inventory_invalid_token():
    """Must raise PermissionError with invalid token."""
    repo = FakeSellerRepository({})
    use_case = GetSellerInventoryUseCase(
        seller_repository=repo,
        valid_tokens=["valid-token"],
        error_rate=0.0,
    )

    try:
        use_case.execute(
            seller_id="SEL-001",
            page=1,
            limit=10,
            token="invalid-token",
        )
        assert False, "Should have raised PermissionError"
    except PermissionError as exc:
        assert "Forbidden" in str(exc)


def test_get_seller_inventory_unknown_seller():
    """Must raise KeyError if seller does not exist in repository."""
    repo = FakeSellerRepository({})
    use_case = GetSellerInventoryUseCase(
        seller_repository=repo,
        valid_tokens=["valid-token"],
        error_rate=0.0,
    )

    with pytest.raises(KeyError) as exc_info:
        use_case.execute(
            seller_id="NONEXISTENT",
            page=1,
            limit=10,
            token="valid-token",
        )
    assert "NONEXISTENT" in str(exc_info.value)


def test_get_seller_inventory_deterministic():
    """Same seller_id must return the same products within the same 10-min window."""
    repo = FakeSellerRepository(
        {
            "SEL-ABC": Seller(
                seller_id="SEL-ABC",
                name="Test Seller",
                seller_type="own",
                country="CO",
            )
        }
    )
    use_case = GetSellerInventoryUseCase(
        seller_repository=repo,
        valid_tokens=["valid-token"],
        error_rate=0.0,
    )

    fixed_time = datetime(2026, 10, 22, 14, 23, 0, tzinfo=timezone.utc)
    result1 = use_case.execute(
        seller_id="SEL-ABC", page=1, limit=10, token="valid-token", as_of=fixed_time
    )
    result2 = use_case.execute(
        seller_id="SEL-ABC", page=1, limit=10, token="valid-token", as_of=fixed_time
    )

    assert result1.data == result2.data
    assert result1.total_items == result2.total_items


def test_get_seller_inventory_ten_minute_update():
    """Quantities and timestamps must refresh across 10-minute windows."""
    repo = FakeSellerRepository(
        {
            "SEL-ABC": Seller(
                seller_id="SEL-ABC",
                name="Test Seller",
                seller_type="own",
                country="CO",
            )
        }
    )
    use_case = GetSellerInventoryUseCase(
        seller_repository=repo,
        valid_tokens=["valid-token"],
        error_rate=0.0,
    )

    t1 = datetime(2026, 10, 22, 14, 5, 0, tzinfo=timezone.utc)
    t2 = t1 + timedelta(minutes=15)

    res1 = use_case.execute(
        seller_id="SEL-ABC", page=1, limit=10, token="valid-token", as_of=t1
    )
    res2 = use_case.execute(
        seller_id="SEL-ABC", page=1, limit=10, token="valid-token", as_of=t2
    )

    # updated_at must reflect different 10-minute window
    assert res1.data[0].updated_at != res2.data[0].updated_at


def test_get_seller_inventory_50k_skus():
    """All items must belong to the 50,000 SKUs pool."""
    assert TOTAL_SKUS == 50_000

    repo = FakeSellerRepository(
        {
            "SEL-001": Seller(
                seller_id="SEL-001",
                name="MercaAndes Retail Colombia",
                seller_type="own",
                country="CO",
            )
        }
    )
    use_case = GetSellerInventoryUseCase(
        seller_repository=repo,
        valid_tokens=["valid-token"],
        error_rate=0.0,
    )

    result = use_case.execute(
        seller_id="SEL-001", page=1, limit=50, token="valid-token"
    )
    for item in result.data:
        sku_num = int(item.sku.replace("SKU-", ""))
        assert 1 <= sku_num <= 50_000


def test_get_seller_inventory_filter_by_sku():
    """Must filter inventory by SKU when requested."""
    repo = FakeSellerRepository(
        {
            "SEL-001": Seller(
                seller_id="SEL-001",
                name="MercaAndes Retail Colombia",
                seller_type="own",
                country="CO",
            )
        }
    )
    use_case = GetSellerInventoryUseCase(
        seller_repository=repo,
        valid_tokens=["valid-token"],
        error_rate=0.0,
    )

    full = use_case.execute(
        seller_id="SEL-001", page=1, limit=100, token="valid-token"
    )
    target_sku = full.data[0].sku

    filtered = use_case.execute(
        seller_id="SEL-001", page=1, limit=10, token="valid-token", sku=target_sku
    )
    assert filtered.total_items == 1
    assert filtered.data[0].sku == target_sku


def test_get_seller_sku_stock_direct():
    """Must fetch single SKU directly or raise KeyError if missing."""
    repo = FakeSellerRepository(
        {
            "SEL-001": Seller(
                seller_id="SEL-001",
                name="MercaAndes Retail Colombia",
                seller_type="own",
                country="CO",
            )
        }
    )
    use_case = GetSellerInventoryUseCase(
        seller_repository=repo,
        valid_tokens=["valid-token"],
        error_rate=0.0,
    )

    full = use_case.execute(
        seller_id="SEL-001", page=1, limit=10, token="valid-token"
    )
    target_sku = full.data[0].sku

    item = use_case.get_seller_sku_stock(
        seller_id="SEL-001", sku=target_sku, token="valid-token"
    )
    assert item.sku == target_sku

    with pytest.raises(KeyError):
        use_case.get_seller_sku_stock(
            seller_id="SEL-001", sku="NON-EXISTENT-SKU", token="valid-token"
        )


def test_get_seller_inventory_pagination():
    """Must respect pagination parameters."""
    repo = FakeSellerRepository(
        {
            "SEL-001": Seller(
                seller_id="SEL-001",
                name="MercaAndes Retail Colombia",
                seller_type="own",
                country="CO",
            )
        }
    )
    use_case = GetSellerInventoryUseCase(
        seller_repository=repo,
        valid_tokens=["valid-token"],
        error_rate=0.0,
    )

    result = use_case.execute(
        seller_id="SEL-001", page=1, limit=5, token="valid-token"
    )

    assert result.page == 1
    assert result.limit == 5
    assert len(result.data) <= 5


def test_seller_entity_creation():
    """Must create a Seller entity correctly."""
    seller = Seller(
        seller_id="SEL-001",
        name="MercaAndes Retail Colombia",
        seller_type="own",
        country="CO",
    )

    assert seller.seller_id == "SEL-001"
    assert seller.name == "MercaAndes Retail Colombia"
    assert seller.seller_type == "own"
    assert seller.country == "CO"
    assert seller.is_own is True


def test_seller_entity_third_party():
    """Must correctly identify third-party sellers."""
    seller = Seller(
        seller_id="SEL-3P-101",
        name="AndesMarket Global",
        seller_type="third_party",
        country="CO",
    )

    assert seller.is_own is False


def test_get_seller_by_id_endpoint():
    """Must return a specific seller by ID via API."""
    from fastapi.testclient import TestClient
    from inventory.presentation.fastapi.deps import get_seller_repository
    from inventory.presentation.fastapi.main import app

    fake_repo = FakeSellerRepository(
        {
            "SEL-001": Seller(
                seller_id="SEL-001",
                name="MercaAndes Retail Colombia",
                seller_type="own",
                country="CO",
            )
        }
    )
    app.dependency_overrides[get_seller_repository] = lambda: fake_repo
    try:
        client = TestClient(app)
        response = client.get("/api/v1/sellers/SEL-001")
        assert response.status_code == 200
        data = response.json()
        assert data["seller_id"] == "SEL-001"
        assert data["name"] == "MercaAndes Retail Colombia"
    finally:
        app.dependency_overrides.clear()


def test_get_seller_by_id_not_found():
    """Must return 404 for unknown seller ID."""
    from fastapi.testclient import TestClient
    from inventory.presentation.fastapi.deps import get_seller_repository
    from inventory.presentation.fastapi.main import app

    fake_repo = FakeSellerRepository({})
    app.dependency_overrides[get_seller_repository] = lambda: fake_repo
    try:
        client = TestClient(app)
        response = client.get("/api/v1/sellers/UNKNOWN-ID")
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_seller_sku_endpoint():
    """Must fetch single seller SKU through API endpoint."""
    from fastapi.testclient import TestClient
    from inventory.presentation.fastapi.deps import (
        get_seller_repository,
        get_seller_inventory_use_case,
    )
    from inventory.presentation.fastapi.main import app

    fake_repo = FakeSellerRepository(
        {
            "SEL-001": Seller(
                seller_id="SEL-001",
                name="MercaAndes Retail Colombia",
                seller_type="own",
                country="CO",
            )
        }
    )
    use_case = GetSellerInventoryUseCase(
        seller_repository=fake_repo,
        valid_tokens=["token-seller-123"],
        error_rate=0.0,
    )
    app.dependency_overrides[get_seller_repository] = lambda: fake_repo
    app.dependency_overrides[get_seller_inventory_use_case] = lambda: use_case

    try:
        client = TestClient(app)
        # Fetch inventory to get an existing SKU
        inv_res = client.get(
            "/api/v1/sellers/SEL-001/inventory",
            headers={"Authorization": "Bearer token-seller-123"},
        )
        assert inv_res.status_code == 200
        first_sku = inv_res.json()["data"][0]["sku"]

        sku_res = client.get(
            f"/api/v1/sellers/SEL-001/inventory/{first_sku}",
            headers={"Authorization": "Bearer token-seller-123"},
        )
        assert sku_res.status_code == 200
        sku_data = sku_res.json()
        assert sku_data["seller_id"] == "SEL-001"
        assert sku_data["sku"] == first_sku
    finally:
        app.dependency_overrides.clear()


def test_cors_preflight_headers():
    """Verify that OPTIONS preflight requests return CORS headers."""
    from fastapi.testclient import TestClient
    from inventory.presentation.fastapi.main import app

    client = TestClient(app)
    response = client.options(
        "/api/v1/sellers",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"
