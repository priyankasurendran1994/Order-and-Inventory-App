import pytest
from fastapi import status

def test_create_product(client, sample_product_data):
    response = client.post("/products/", json=sample_product_data)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == sample_product_data["name"]
    assert data["price"] == sample_product_data["price"]
    assert data["stock"] == sample_product_data["stock"]
    assert "id" in data
    assert "created_at" in data

def test_create_product_invalid_data(client):
    # Test with negative price
    response = client.post("/products/", json={
        "name": "Invalid Product",
        "price": -10.0,
        "stock": 5
    })
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Test with negative stock
    response = client.post("/products/", json={
        "name": "Invalid Product",
        "price": 10.0,
        "stock": -5
    })
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_read_products(client, sample_product_data):
    # Create a product first
    client.post("/products/", json=sample_product_data)
    
    response = client.get("/products/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1

def test_read_product(client, sample_product_data):
    # Create a product first
    create_response = client.post("/products/", json=sample_product_data)
    product_id = create_response.json()["id"]
    
    response = client.get(f"/products/{product_id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == product_id
    assert data["name"] == sample_product_data["name"]

def test_read_product_not_found(client):
    response = client.get("/products/999")
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_update_product(client, sample_product_data):
    # Create a product first
    create_response = client.post("/products/", json=sample_product_data)
    product_id = create_response.json()["id"]
    
    update_data = {"name": "Updated Product", "price": 149.99}
    response = client.put(f"/products/{product_id}", json=update_data)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == update_data["name"]
    assert data["price"] == update_data["price"]
    assert data["stock"] == sample_product_data["stock"]  # Unchanged

def test_update_product_not_found(client):
    response = client.put("/products/999", json={"name": "Updated"})
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_delete_product(client, sample_product_data):
    # Create a product first
    create_response = client.post("/products/", json=sample_product_data)
    product_id = create_response.json()["id"]
    
    response = client.delete(f"/products/{product_id}")
    assert response.status_code == status.HTTP_200_OK
    
    # Verify it's deleted
    get_response = client.get(f"/products/{product_id}")
    assert get_response.status_code == status.HTTP_404_NOT_FOUND

def test_delete_product_not_found(client):
    response = client.delete("/products/999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
