"""Unit tests for RF-03: Seller score query with tenant authorization and status/penalties."""

from datetime import datetime, timezone
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient

from inventory.application.use_cases.get_seller_score import GetSellerScoreUseCase
from inventory.domain.entities.seller import SellerScore
from inventory.presentation.fastapi.deps import get_seller_score_use_case
from inventory.presentation.fastapi.main import app

SELLER_A = "SEL-001"
SELLER_B = "SEL-002"


class FakeSellerScoreRepo:
    def get_score(self, seller_id):
        if seller_id == SELLER_A:
            return SellerScore(
                seller_id=SELLER_A,
                score=Decimal("88.00"),
                dispatch_pct=Decimal("95.00"),
                review_rating=Decimal("4.80"),
                inventory_accuracy=Decimal("90.00"),
                cancellation_rate=Decimal("5.00"),
                calculated_at=datetime.now(timezone.utc),
                status="active",
                penalties=(),
                reason="active",
            )
        elif seller_id == SELLER_B:
            return SellerScore(
                seller_id=SELLER_B,
                score=Decimal("55.00"),
                dispatch_pct=Decimal("60.00"),
                review_rating=Decimal("2.50"),
                inventory_accuracy=Decimal("50.00"),
                cancellation_rate=Decimal("25.00"),
                calculated_at=datetime.now(timezone.utc),
                status="probation",
                penalties=("Score below 60 for 2 consecutive weeks (RN-08)",),
                reason="Score below 60 for 2 consecutive weeks (RN-08)",
            )
        return None


@pytest.fixture
def client():
    fake_repo = FakeSellerScoreRepo()
    app.dependency_overrides[get_seller_score_use_case] = lambda: GetSellerScoreUseCase(fake_repo)
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_seller_score_own_token_success(client):
    """TC-RF03-01: Querying own score with seller token succeeds and includes status and penalties."""
    headers = {"Authorization": f"Bearer token-{SELLER_A}"}
    response = client.get(f"/api/v1/sellers/{SELLER_A}/score", headers=headers)
    assert response.status_code == 200
    data = response.json()

    assert data["seller_id"] == SELLER_A
    assert float(data["score"]) == 88.0
    assert data["status"] == "active"
    assert data["penalties"] == []


def test_seller_score_probation_with_penalties(client):
    """TC-RF03-02: Querying seller on probation returns penalty reasons."""
    headers = {"Authorization": f"Bearer token-{SELLER_B}"}
    response = client.get(f"/api/v1/sellers/{SELLER_B}/score", headers=headers)
    assert response.status_code == 200
    data = response.json()

    assert data["seller_id"] == SELLER_B
    assert float(data["score"]) == 55.0
    assert data["status"] == "probation"
    assert len(data["penalties"]) == 1
    assert "Score below 60" in data["penalties"][0]


def test_seller_score_other_seller_token_forbidden(client):
    """TC-RF03-03: Accessing another seller's score is blocked with 403 Forbidden (RF-03)."""
    # Seller B attempts to access Seller A's score
    headers = {"Authorization": f"Bearer token-{SELLER_B}"}
    response = client.get(f"/api/v1/sellers/{SELLER_A}/score", headers=headers)
    assert response.status_code == 403
    assert "only query your own" in response.json()["detail"]
