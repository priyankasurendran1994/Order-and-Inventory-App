import pytest
from pydantic import ValidationError
from app.schemas import ProductCreate, ProductUpdate, OrderCreate, OrderItemCreate

def test_product_validation():
    # Valid product
    valid_product = ProductCreate(name="Valid Product", price=10.0, stock=5)
    assert valid_product.name == "Valid Product"
    
    # Invalid price (negative)
    with pytest.raises(ValidationError):
        ProductCreate(name="Invalid Product", price=-5.0, stock=5)
    
    # Invalid stock (negative)
    with pytest.raises(ValidationError):
        ProductCreate(name="Invalid Product", price=10.0, stock=-1)
    
    # Empty name
    with pytest.raises(ValidationError):
        ProductCreate(name="", price=10.0, stock=5)

def test_order_validation():
    # Valid order
    valid_order = OrderCreate(
        items=[OrderItemCreate(product_id=1, quantity=2)]
    )
    assert len(valid_order.items) == 1
    
    # Empty items list
    with pytest.raises(ValidationError):
        OrderCreate(items=[])
    
    # Invalid quantity
    with pytest.raises(ValidationError):
        OrderCreate(
            items=[OrderItemCreate(product_id=1, quantity=0)]
        )
    
    # Invalid product_id
    with pytest.raises(ValidationError):
        OrderCreate(
            items=[OrderItemCreate(product_id=0, quantity=1)]
        )
