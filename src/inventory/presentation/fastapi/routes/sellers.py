"""Route to get seller inventory."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from inventory.application.use_cases.get_seller_inventory import (
    GetSellerInventoryUseCase,
)
from inventory.application.use_cases.list_sellers import (
    ListSellersUseCase,
)
from inventory.presentation.fastapi.deps import (
    get_list_sellers_use_case,
    get_seller_inventory_use_case,
)

router = APIRouter(prefix="/api/v1/sellers", tags=["sellers"])

security_scheme = HTTPBearer()


@router.get(
    "",
    summary="List all sellers",
    description="Returns a list of all registered sellers with their IDs from PostgreSQL.",
    status_code=status.HTTP_200_OK,
)
def list_sellers(
    use_case: ListSellersUseCase = Depends(get_list_sellers_use_case),
):
    sellers = use_case.execute()
    return [
        {
            "seller_id": s.seller_id,
            "name": s.name,
            "seller_type": s.seller_type,
            "country": s.country,
        }
        for s in sellers
    ]


@router.get(
    "/{seller_id}",
    summary="Get Seller by ID",
    description="Retrieves information for a single seller by their ID from PostgreSQL.",
    status_code=status.HTTP_200_OK,
)
def get_seller(
    seller_id: str = Path(..., description="Seller ID"),
    use_case: ListSellersUseCase = Depends(get_list_sellers_use_case),
):
    sellers = use_case.execute()
    seller = next((s for s in sellers if s.seller_id == seller_id), None)
    if not seller:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Seller '{seller_id}' not found",
        )
    return {
        "seller_id": seller.seller_id,
        "name": seller.name,
        "seller_type": seller.seller_type,
        "country": seller.country,
    }


@router.get(
    "/{seller_id}/inventory",
    summary="Get Seller Inventory",
    description=(
        "Retrieves paginated inventory for a given seller. Updates deterministically "
        "every 10 minutes from a pool of 50,000 SKUs. Optionally filterable by SKU."
    ),
)
def get_seller_inventory(
    seller_id: str = Path(..., description="Seller ID"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    sku: Optional[str] = Query(None, description="Optional product SKU filter"),
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    use_case: GetSellerInventoryUseCase = Depends(get_seller_inventory_use_case),
):
    try:
        result = use_case.execute(
            seller_id=seller_id,
            page=page,
            limit=limit,
            token=credentials.credentials,
            sku=sku,
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc).strip("'\""),
        )
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        )
    except RuntimeError as exc:
        status_code = (
            status.HTTP_429_TOO_MANY_REQUESTS
            if "Rate limit" in str(exc)
            else status.HTTP_503_SERVICE_UNAVAILABLE
        )
        raise HTTPException(status_code=status_code, detail=str(exc))

    return {
        "seller_id": result.seller_id,
        "page": result.page,
        "limit": result.limit,
        "total_items": result.total_items,
        "total_pages": result.total_pages,
        "data": [
            {
                "sku": item.sku,
                "quantity": item.quantity,
                "updated_at": item.updated_at,
            }
            for item in result.data
        ],
    }


@router.get(
    "/{seller_id}/inventory/{sku}",
    summary="Get Seller Inventory for a specific SKU",
    description="Retrieves the inventory stock for a single SKU belonging to a given seller.",
)
def get_seller_sku_inventory(
    seller_id: str = Path(..., description="Seller ID"),
    sku: str = Path(..., description="Product SKU (e.g. SKU-00001)"),
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    use_case: GetSellerInventoryUseCase = Depends(get_seller_inventory_use_case),
):
    try:
        item = use_case.get_seller_sku_stock(
            seller_id=seller_id,
            sku=sku,
            token=credentials.credentials,
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc).strip("'\""),
        )
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        )
    except RuntimeError as exc:
        status_code = (
            status.HTTP_429_TOO_MANY_REQUESTS
            if "Rate limit" in str(exc)
            else status.HTTP_503_SERVICE_UNAVAILABLE
        )
        raise HTTPException(status_code=status_code, detail=str(exc))

    return {
        "seller_id": seller_id,
        "sku": item.sku,
        "quantity": item.quantity,
        "updated_at": item.updated_at,
    }
