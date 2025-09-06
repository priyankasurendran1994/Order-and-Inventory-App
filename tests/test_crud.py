import pytest
from sqlalchemy.orm import Session
from app import crud, schemas, models

def test_product_crud_operations(db_session):
    # Test create
    product_data = schemas.ProductCreate(name="CRUD Product", price=25.0, stock=15)
    created_product = crud.product_crud.create(db_session, product_data)
    
    assert created_product.id is not None
    assert created_product.name == "CRUD Product"
    assert created_product.price == 25.0
    assert created_product.stock == 15
    
    # Test get
    fetched_product = crud.product_crud.get(db_session, created_product.id)
    assert fetched_product is not None
    assert fetched_product.id == created_product.id
    
    # Test update
    update_data = schemas.ProductUpdate(name="Updated CRUD Product", stock=20)
    updated_product = crud.product_crud.update(db_session, created_product.id, update_data)
    
    assert updated_product.name == "Updated CRUD Product"
    assert updated_product.stock == 20
    assert updated_product.price == 25.0  # Unchanged
    
    # Test delete
    delete_result = crud.product_crud.delete(db_session, created_product.id)
    assert delete_result == True
    
    # Verify deletion
    deleted_product = crud.product_crud.get(db_session, created_product.id)
    assert deleted_product is None

def test_order_crud_with_stock_locking(db_session):
    # Create a product
    product_data = schemas.ProductCreate(name="Lock Test Product", price=10.0, stock=5)
    product = crud.product_crud.create(db_session, product_data)
    
    # Create an order
    order_data = schemas.OrderCreate(
        items=[schemas.OrderItemCreate(product_id=product.id, quantity=2)]
    )
    
    created_order = crud.order_crud.create_with_items(
        db_session, order_data, "test-idempotency-key"
    )
    
    assert created_order.id is not None
    assert created_order.total_amount == 20.0  # 10.0 * 2
    assert len(created_order.items) == 1
    
    # Verify stock was decremented
    updated_product = crud.product_crud.get(db_session, product.id)
    assert updated_product.stock == 3  # 5 - 2
    
    # Test idempotency
    same_order = crud.order_crud.create_with_items(
        db_session, order_data, "test-idempotency-key"
    )
    assert same_order.id == created_order.id
    
    # Stock should not be decremented again
    product_after_idempotent = crud.product_crud.get(db_session, product.id)
    assert product_after_idempotent.stock == 3

def test_order_crud_insufficient_stock(db_session):
    # Create a product with limited stock
    product_data = schemas.ProductCreate(name="Limited Stock Product", price=15.0, stock=2)
    product = crud.product_crud.create(db_session, product_data)
    
    # Try to order more than available
    order_data = schemas.OrderCreate(
        items=[schemas.OrderItemCreate(product_id=product.id, quantity=5)]
    )
    
    with pytest.raises(ValueError, match="Insufficient stock"):
        crud.order_crud.create_with_items(db_session, order_data, "insufficient-stock-key")
