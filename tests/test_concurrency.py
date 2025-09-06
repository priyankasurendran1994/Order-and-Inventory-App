import pytest
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

def test_concurrent_order_creation_no_oversell(client):
    """
    Integration test that fires ~50 parallel order requests for a product
    with stock 10 and asserts no oversell.
    """
    # Create a product with limited stock
    product_data = {"name": "Limited Product", "price": 100.0, "stock": 10}
    product_response = client.post("/products/", json=product_data)
    product_id = product_response.json()["id"]
    
    def create_order(thread_id):
        order_data = {"items": [{"product_id": product_id, "quantity": 1}]}
        idempotency_key = f"test-key-{thread_id}-{time.time()}"
        
        response = client.post(
            "/orders/",
            json=order_data,
            headers={"Idempotency-Key": idempotency_key}
        )
        return response.status_code, response.json() if response.status_code != 409 else None
    
    # Fire 50 concurrent requests
    successful_orders = 0
    failed_orders = 0
    
    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(create_order, i) for i in range(50)]
        
        for future in as_completed(futures):
            status_code, response_data = future.result()
            if status_code == 201:
                successful_orders += 1
            elif status_code == 409:  # Conflict - insufficient stock
                failed_orders += 1
    
    # Should have exactly 10 successful orders (matching the stock)
    assert successful_orders == 10
    assert failed_orders == 40
    
    # Verify the product stock is 0
    product_check = client.get(f"/products/{product_id}")
    assert product_check.json()["stock"] == 0

def test_concurrent_order_creation_with_idempotency(client):
    """Test that concurrent requests with the same idempotency key don't cause issues"""
    # Create a product
    product_data = {"name": "Idempotent Product", "price": 50.0, "stock": 20}
    product_response = client.post("/products/", json=product_data)
    product_id = product_response.json()["id"]
    
    idempotency_key = "shared-key-123"
    
    def create_order_with_shared_key():
        order_data = {"items": [{"product_id": product_id, "quantity": 1}]}
        response = client.post(
            "/orders/",
            json=order_data,
            headers={"Idempotency-Key": idempotency_key}
        )
        return response.status_code, response.json()
    
    # Fire 10 concurrent requests with the same idempotency key
    order_ids = set()
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(create_order_with_shared_key) for _ in range(10)]
        
        for future in as_completed(futures):
            status_code, response_data = future.result()
            assert status_code == 201
            order_ids.add(response_data["id"])
    
    # All requests should return the same order ID
    assert len(order_ids) == 1
    
    # Product stock should only be decremented once
    product_check = client.get(f"/products/{product_id}")
    assert product_check.json()["stock"] == 19
