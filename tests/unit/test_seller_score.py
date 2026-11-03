"""Tests for reading persisted seller scores."""

from datetime import datetime, timezone
from decimal import Decimal

from fastapi.testclient import TestClient

from inventory.application.use_cases.get_seller_score import GetSellerScoreUseCase
from inventory.domain.entities.seller import SellerScore
from inventory.infrastructure.persistence.sqlalchemy_seller_repository import (
    SqlAlchemySellerRepository,
)
from inventory.presentation.fastapi.deps import get_seller_score_use_case
from inventory.presentation.fastapi.main import app

SELLER_ID = "bd5c2fd2-2165-49e7-a1b8-48aaee3021e4"
API_SELLER_ID = "SEL-001"


class FakeSellerRepository:
    def __init__(self, score=None, seller_ids=None):
        self.score = score
        self.seller_ids = seller_ids or []

    def get_score(self, seller_id):
        if not self.score:
            return None
        if seller_id == self.score.seller_id or seller_id in self.seller_ids:
            return self.score
        return None


def make_score(seller_id=SELLER_ID):
    return SellerScore(
        seller_id=seller_id,
        score=Decimal("82.50"),
        dispatch_pct=Decimal("90.00"),
        review_rating=Decimal("4.50"),
        inventory_accuracy=Decimal("80.00"),
        cancellation_rate=Decimal("10.00"),
        calculated_at=datetime(2026, 10, 20, tzinfo=timezone.utc),
    )


def test_get_seller_score_returns_stored_score():
    use_case = GetSellerScoreUseCase(FakeSellerRepository(score=make_score()))

    result = use_case.execute(SELLER_ID)

    assert result == make_score()


def test_get_seller_score_is_not_available_without_saved_score():
    use_case = GetSellerScoreUseCase(FakeSellerRepository())

    assert use_case.execute("SEL-404") is None


def test_get_seller_score_accepts_dim_seller_uuid():
    score = make_score()
    use_case = GetSellerScoreUseCase(FakeSellerRepository(score=score))

    assert use_case.execute(SELLER_ID) == score


def test_seller_score_endpoint_returns_persisted_fields():
    repository = FakeSellerRepository(score=make_score())
    use_case = GetSellerScoreUseCase(repository)
    app.dependency_overrides[get_seller_score_use_case] = lambda: use_case

    try:
        response = TestClient(app).get(f"/api/v1/sellers/{SELLER_ID}/score")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["score"] == 82.5
    assert response.json()["cancellation_rate"] == 10.0


def test_seller_score_endpoint_returns_404_when_score_is_not_ready():
    repository = FakeSellerRepository()
    use_case = GetSellerScoreUseCase(repository)
    app.dependency_overrides[get_seller_score_use_case] = lambda: use_case

    try:
        response = TestClient(app).get(f"/api/v1/sellers/{SELLER_ID}/score")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert "not available" in response.json()["detail"]


def test_seller_score_endpoint_accepts_existing_api_seller_id():
    repository = FakeSellerRepository(
        score=make_score(), seller_ids=[API_SELLER_ID]
    )
    app.dependency_overrides[get_seller_score_use_case] = lambda: GetSellerScoreUseCase(
        repository
    )

    try:
        response = TestClient(app).get(f"/api/v1/sellers/{API_SELLER_ID}/score")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["seller_id"] == SELLER_ID


def test_repository_resolves_api_seller_id_through_source_key_table():
    class Result:
        def fetchone(self):
            score = make_score()
            return (
                score.seller_id,
                score.score,
                score.dispatch_pct,
                score.review_rating,
                score.inventory_accuracy,
                score.cancellation_rate,
                score.calculated_at,
            )

    class Connection:
        def execute(self, statement, parameters):
            self.statement = str(statement)
            self.parameters = parameters
            return Result()

    connection = Connection()
    repository = SqlAlchemySellerRepository(connection)

    result = repository.get_score(API_SELLER_ID)

    assert result.seller_id == SELLER_ID
    assert "public.dim_seller_source_key" in connection.statement
    assert connection.parameters == {"seller_id": API_SELLER_ID}
