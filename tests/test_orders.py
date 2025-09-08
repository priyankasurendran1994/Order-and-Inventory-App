import pytest
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from app.models import Order
from fastapi import status

def test_create_order(client, sample_product_data):
    # Create a product first
    product_response = client.post("/products/", json=sample_product_data)
    product_id = product_response.json()["id"]
    
    order_data = {"items": [{"product_id": product_id, "quantity": 2}]}
    response = client.post("/orders/", json=order_data)
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert "id" in data
    assert "idempotency_key" in data
    assert data["total_amount"] == sample_product_data["price"] * 2
    assert len(data["items"]) == 1
    assert data["items"][0]["quantity"] == 2

def test_create_order_with_idempotency_key(client, sample_product_data):
    # Create a product first
    product_response = client.post("/products/", json=sample_product_data)
    product_id = product_response.json()["id"]
    
    order_data = {"items": [{"product_id": product_id, "quantity": 2}]}
    idempotency_key = "test-key-123"
    
    # First request
    response1 = client.post(
        "/orders/", 
        json=order_data,
        headers={"Idempotency-Key": idempotency_key}
    )
    assert response1.status_code == status.HTTP_201_CREATED
    order_id_1 = response1.json()["id"]
    
    # Second request with same key should return the same order
    response2 = client.post(
        "/orders/", 
        json=order_data,
        headers={"Idempotency-Key": idempotency_key}
    )
    assert response2.status_code == status.HTTP_201_CREATED
    order_id_2 = response2.json()["id"]
    
    assert order_id_1 == order_id_2

def test_create_order_insufficient_stock(client, sample_product_data):
    # Create a product with limited stock
    product_data = {**sample_product_data, "stock": 5}
    product_response = client.post("/products/", json=product_data)
    product_id = product_response.json()["id"]
    
    # Try to order more than available
    order_data = {"items": [{"product_id": product_id, "quantity": 10}]}
    response = client.post("/orders/", json=order_data)
    
    assert response.status_code == status.HTTP_409_CONFLICT
    assert "Insufficient stock" in response.json()["detail"]

def test_create_order_product_not_found(client):
    order_data = {"items": [{"product_id": 999, "quantity": 1}]}
    response = client.post("/orders/", json=order_data)
    
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in response.json()["detail"]

def test_create_order_multiple_items(client):
    # Create multiple products
    product1_data = {"name": "Product 1", "price": 10.0, "stock": 5}
    product2_data = {"name": "Product 2", "price": 20.0, "stock": 3}
    
    product1_response = client.post("/products/", json=product1_data)
    product2_response = client.post("/products/", json=product2_data)
    
    product1_id = product1_response.json()["id"]
    product2_id = product2_response.json()["id"]
    
    order_data = {
        "items": [
            {"product_id": product1_id, "quantity": 2},
            {"product_id": product2_id, "quantity": 1}
        ]
    }
    
    response = client.post("/orders/", json=order_data)
    assert response.status_code == status.HTTP_201_CREATED
    
    data = response.json()
    expected_total = (10.0 * 2) + (20.0 * 1)
    assert data["total_amount"] == expected_total
    assert len(data["items"]) == 2

def test_read_orders_pagination(client, sample_product_data):
    # Create a product first
    product_response = client.post("/products/", json={**sample_product_data, "stock": 100})
    product_id = product_response.json()["id"]
    
    # Create multiple orders
    for i in range(5):
        order_data = {"items": [{"product_id": product_id, "quantity": 1}]}
        client.post("/orders/", json=order_data)
    
    # Test pagination
    response = client.get("/orders/?limit=3")
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert len(data["orders"]) == 3
    assert data["has_more"] == True
    assert data["next_cursor"] is not None
    
    # Get next page
    next_response = client.get(f"/orders/?limit=3&cursor={data['next_cursor']}")
    assert next_response.status_code == status.HTTP_200_OK
    
    next_data = next_response.json()
    assert len(next_data["orders"]) == 2
    assert next_data["has_more"] == False

def test_read_order(client, sample_product_data):
    # Create a product and order first
    product_response = client.post("/products/", json=sample_product_data)
    product_id = product_response.json()["id"]
    
    order_data = {"items": [{"product_id": product_id, "quantity": 2}]}
    order_response = client.post("/orders/", json=order_data)
    order_id = order_response.json()["id"]
    
    response = client.get(f"/orders/{order_id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == order_id

def test_read_order_not_found(client):
    response = client.get("/orders/999")
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_read_orders_pagination(client, sample_product_data, db_session):
    db_session.query(Order).delete()
    db_session.commit()
