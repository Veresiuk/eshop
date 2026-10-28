import pytest
from httpx import AsyncClient
from eshop.external_api import fetch_multiple_products_async


def test_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "online"


def test_get_categories(client):
    response = client.get("/categories")
    assert response.status_code == 200
    assert len(response.json()) >= 2


def test_create_category(client):
    response = client.post("/categories", json={"name": "Планшети", "description": "Планшетні ПК"})
    assert response.status_code == 201
    assert response.json()["name"] == "Планшети"


def test_create_category_duplicate(client):
    response = client.post("/categories", json={"name": "Ноутбуки", "description": "Повтор"})
    assert response.status_code == 409


def test_list_products_and_search(client):
    response = client.get("/products")
    assert response.status_code == 200
    assert len(response.json()) == 3

    response_search = client.get("/products?query=MacBook")
    assert response_search.status_code == 200
    assert len(response_search.json()) == 1


def test_get_product_by_id(client):
    response = client.get("/products/1")
    assert response.status_code == 200
    assert response.json()["id"] == 1

    response_404 = client.get("/products/999")
    assert response_404.status_code == 404


def test_create_product(client):
    new_prod = {
        "name": "Lenovo Legion 5",
        "description": "Ігровий лептоп",
        "price": 54000.0,
        "stock": 10,
        "category_id": 1
    }
    response = client.post("/products", json=new_prod)
    assert response.status_code == 201
    assert response.json()["name"] == "Lenovo Legion 5"


def test_validation_invalid_price(client):
    invalid_prod = {
        "name": "Invalid Price Item",
        "description": "Test",
        "price": -100.0,
        "stock": 5,
        "category_id": 1
    }
    response = client.post("/products", json=invalid_prod)
    assert response.status_code == 422


def test_update_product_patch(client):
    update_data = {"price": 115000.0, "stock": 4}
    response = client.patch("/products/1", json=update_data)
    assert response.status_code == 200
    assert response.json()["price"] == 115000.0


def test_delete_product(client):
    response = client.delete("/products/1")
    assert response.status_code == 204
    assert client.get("/products/1").status_code == 404


def test_purchase_product_success(client):
    response = client.post("/products/2/purchase", json={"quantity": 3})
    assert response.status_code == 200
    data = response.json()
    assert data["quantity"] == 3
    assert data["remaining_stock"] == 5
    assert data["total_amount"] == 95000.0 * 3


def test_purchase_product_insufficient_stock(client):
    response = client.post("/products/2/purchase", json={"quantity": 100})
    assert response.status_code == 409
    assert "Insufficient stock" in response.json()["detail"]


def test_inventory_statistics(client):
    response = client.get("/statistics/inventory")
    assert response.status_code == 200
    data = response.json()
    assert data["total_products_count"] >= 1
    assert data["total_inventory_value"] > 0
    assert data["most_expensive_product"] is not None


@pytest.mark.asyncio
async def test_async_fetch_multiple_products(async_client: AsyncClient):
    results = await fetch_multiple_products_async(
        base_url="http://test",
        product_ids=[1, 2, 3],
        max_concurrency=2,
        timeout_seconds=5.0,
        client=async_client,
    )
    assert len(results) == 3
    ids = [r["id"] for r in results]
    assert 1 in ids and 2 in ids and 3 in ids