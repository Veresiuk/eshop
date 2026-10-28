import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from eshop.database import get_session, create_db_and_tables
from eshop.models import Product, Category
from eshop.schemas import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    CategoryCreate,
    CategoryResponse,
    PurchaseRequest,
    PurchaseResponse,
    InventoryStats,
    BatchProductRequest,
)
from eshop.services import InventoryService
from eshop.external_api import fetch_multiple_products_async


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    create_db_and_tables()
    yield


app = FastAPI(
    title="E-Shop REST API",
    description="Інтернет-магазин (Лабораторна робота №8, Варіант 3) — Вересюк Ірина",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/", tags=["System"])
async def root() -> dict[str, str]:
    return {
        "status": "online",
        "service": "E-Shop REST API",
        "version": "1.0.0",
        "documentation": "/docs",
    }


# --- Categories ---
@app.post(
    "/categories",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Categories"],
)
async def create_category(
    data: CategoryCreate,
    session: Session = Depends(get_session),
) -> Category:
    service = InventoryService(session)
    try:
        return service.create_category(data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@app.get(
    "/categories",
    response_model=list[CategoryResponse],
    tags=["Categories"],
)
async def list_categories(
    session: Session = Depends(get_session),
) -> list[Category]:
    service = InventoryService(session)
    return service.get_all_categories()


@app.get(
    "/categories/{category_id}/products",
    response_model=list[ProductResponse],
    tags=["Categories", "Products"],
)
async def get_products_by_category(
    category_id: int,
    session: Session = Depends(get_session),
) -> list[Product]:
    service = InventoryService(session)
    try:
        return service.get_products_by_category(category_id)
    except KeyError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# --- Products ---
@app.get(
    "/products",
    response_model=list[ProductResponse],
    tags=["Products"],
)
async def list_products(
    query: str | None = Query(default=None, description="Пошук за назвою"),
    category_id: int | None = Query(default=None, description="Фільтр за категорією"),
    min_price: float | None = Query(default=None, ge=0, description="Мінімальна ціна"),
    max_price: float | None = Query(default=None, ge=0, description="Максимальна ціна"),
    skip: int = Query(default=0, ge=0, description="Зсув пагінації"),
    limit: int = Query(default=100, ge=1, le=100, description="Кількість записів"),
    session: Session = Depends(get_session),
) -> list[Product]:
    service = InventoryService(session)
    return service.search_products(
        query=query,
        category_id=category_id,
        min_price=min_price,
        max_price=max_price,
        skip=skip,
        limit=limit,
    )


@app.get(
    "/products/{product_id}",
    response_model=ProductResponse,
    tags=["Products"],
)
async def get_product(
    product_id: int,
    session: Session = Depends(get_session),
) -> Product:
    service = InventoryService(session)
    prod = service.get_product_by_id(product_id)
    if not prod:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found",
        )
    return prod


@app.post(
    "/products",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Products"],
)
async def create_product(
    data: ProductCreate,
    session: Session = Depends(get_session),
) -> Product:
    service = InventoryService(session)
    try:
        return service.create_product(data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.patch(
    "/products/{product_id}",
    response_model=ProductResponse,
    tags=["Products"],
)
async def update_product(
    product_id: int,
    data: ProductUpdate,
    session: Session = Depends(get_session),
) -> Product:
    service = InventoryService(session)
    try:
        updated = service.update_product(product_id, data)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {product_id} not found",
            )
        return updated
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.delete(
    "/products/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Products"],
)
async def delete_product(
    product_id: int,
    session: Session = Depends(get_session),
) -> None:
    service = InventoryService(session)
    deleted = service.delete_product(product_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found",
        )


@app.post(
    "/products/{product_id}/purchase",
    response_model=PurchaseResponse,
    tags=["Transactions"],
)
async def purchase_product(
    product_id: int,
    data: PurchaseRequest,
    session: Session = Depends(get_session),
) -> PurchaseResponse:
    service = InventoryService(session)
    try:
        return service.purchase_product(product_id, data.quantity)
    except KeyError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


# --- Statistics & Async Operations ---
@app.get(
    "/statistics/inventory",
    response_model=InventoryStats,
    tags=["Statistics"],
)
async def get_inventory_statistics(
    session: Session = Depends(get_session),
) -> InventoryStats:
    service = InventoryService(session)
    return service.get_inventory_stats()


@app.post(
    "/products/batch-fetch",
    tags=["Async Operations"],
)
async def batch_fetch_products(
    request: BatchProductRequest,
) -> list[dict]:
    try:
        return await fetch_multiple_products_async(
            base_url="http://127.0.0.1:8000",
            product_ids=request.product_ids,
            max_concurrency=3,
            timeout_seconds=5.0,
        )
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Batch request timed out",
        )