import pytest
import time

def test_single_order_creation_performance(client, sample_product_data):
    """
    Simple perf smoke: ensure single order creation typically < 150 ms on local dev.
    """
    # Create a product first
    product_response = client.post("/products/", json=sample_product_data)
    product_id = product_response.json()["id"]
    
    order_data = {"items": [{"product_id": product_id, "quantity": 1}]}
    
    # Measure order creation time
    start_time = time.time()
    response = client.post("/orders/", json=order_data)
    end_time = time.time()
    
    assert response.status_code == 201
    
    duration_ms = (end_time - start_time) * 1000
    print(f"Order creation took: {duration_ms:.2f}ms")
    
    # Allow some flexibility for CI/test environments
    assert duration_ms < 500  # 500ms threshold instead of 150ms for test environments

def test_product_list_performance(client):
    """Test that product listing is reasonably fast"""
    # Create multiple products
    for i in range(20):
        product_data = {"name": f"Product {i}", "price": float(i + 1), "stock": 10}
        client.post("/products/", json=product_data)
    
    # Measure product list performance
    start_time = time.time()
    response = client.get("/products/")
    end_time = time.time()
    
    assert response.status_code == 200
    assert len(response.json()) == 20
    
    duration_ms = (end_time - start_time) * 1000
    print(f"Product listing took: {duration_ms:.2f}ms")
    
    # Should be very fast
    assert duration_ms < 100
