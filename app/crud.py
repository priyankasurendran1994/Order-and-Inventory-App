# app/crud.py
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, select, func
from typing import List, Optional, Tuple
from app import models, schemas
from app.database import redis_client
import json
from datetime import datetime

class ProductCRUD:
    def get(self, db: Session, product_id: int) -> Optional[models.Product]:
        return db.query(models.Product).filter(models.Product.id == product_id).first()
    
    def get_multi(self, db: Session, skip: int = 0, limit: int = 100) -> List[models.Product]:
        # Try to get from cache first
        if redis_client:
            cache_key = f"products_list_{skip}_{limit}"
            cached = redis_client.get(cache_key)
            if cached:
                try:
                    products_data = json.loads(cached)
                    return [models.Product(**data) for data in products_data]
                except Exception:
                    pass
        
        # Order by ID ascending for consistent ordering
        products = db.query(models.Product).order_by(models.Product.id).offset(skip).limit(limit).all()
        
        # Cache the results
        if redis_client and products:
            cache_key = f"products_list_{skip}_{limit}"
            products_data = [
                {
                    "id": p.id,
                    "name": p.name,
                    "price": p.price,
                    "stock": p.stock,
                    "created_at": p.created_at.isoformat() if p.created_at else None,
                    "updated_at": p.updated_at.isoformat() if p.updated_at else None
                }
                for p in products
            ]
            redis_client.setex(cache_key, 300, json.dumps(products_data))  # 5 min cache
        
        return products
    
    def create(self, db: Session, product: schemas.ProductCreate) -> models.Product:
        db_product = models.Product(**product.model_dump())
        db.add(db_product)
        db.commit()
        db.refresh(db_product)
        
        # Invalidate cache
        self._invalidate_products_cache()
        
        return db_product
    
    def update(self, db: Session, product_id: int, product: schemas.ProductUpdate) -> Optional[models.Product]:
        db_product = self.get(db, product_id)
        if not db_product:
            return None
        
        # Only update fields that were actually provided (exclude_unset=True)
        update_data = product.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_product, field, value)
        
        # Update the updated_at timestamp
        db_product.updated_at = func.now()
        
        db.commit()
        db.refresh(db_product)
        
        # Invalidate cache
        self._invalidate_products_cache()
        
        return db_product
    
    def delete(self, db: Session, product_id: int) -> bool:
        db_product = self.get(db, product_id)
        if not db_product:
            return False
        
        db.delete(db_product)
        db.commit()
        
        # Invalidate cache
        self._invalidate_products_cache()
        
        return True
    
    def get_for_update(self, db: Session, product_id: int) -> Optional[models.Product]:
        """Get product with row-level lock for update"""
        return db.query(models.Product).filter(
            models.Product.id == product_id
        ).with_for_update().first()
    
    def _invalidate_products_cache(self):
        if redis_client:
            # Delete all product list cache keys
            for key in redis_client.scan_iter(match="products_list_*"):
                redis_client.delete(key)

class OrderCRUD:
    def get(self, db: Session, order_id: int) -> Optional[models.Order]:
        return db.query(models.Order).filter(models.Order.id == order_id).first()
    
    def get_by_idempotency_key(self, db: Session, idempotency_key: str) -> Optional[models.Order]:
        return db.query(models.Order).filter(
            models.Order.idempotency_key == idempotency_key
        ).first()
    
    def get_multi_paginated(
        self, 
        db: Session, 
        limit: int = 50, 
        cursor: Optional[str] = None
    ) -> Tuple[List[models.Order], Optional[str], bool]:
        query = db.query(models.Order).order_by(
            desc(models.Order.created_at), 
            desc(models.Order.id)
        )
        
        if cursor:
            try:
                # Parse cursor: "timestamp_id"
                created_at_str, order_id_str = cursor.split('_')
                cursor_created_at = datetime.fromisoformat(created_at_str)
                cursor_id = int(order_id_str)
                
                query = query.filter(
                    and_(
                        models.Order.created_at <= cursor_created_at,
                        models.Order.id < cursor_id
                    )
                )
            except (ValueError, TypeError):
                # Invalid cursor, ignore
                pass
        
        orders = query.limit(limit + 1).all()
        
        has_more = len(orders) > limit
        if has_more:
            orders = orders[:-1]
        
        next_cursor = None
        if has_more and orders:
            last_order = orders[-1]
            next_cursor = f"{last_order.created_at.isoformat()}_{last_order.id}"
        
        return orders, next_cursor, has_more
    
    def create_with_items(
        self, 
        db: Session, 
        order_data: schemas.OrderCreate, 
        idempotency_key: str
    ) -> models.Order:
        # Check if order already exists (idempotency)
        existing_order = self.get_by_idempotency_key(db, idempotency_key)
        if existing_order:
            return existing_order
        
        # Calculate total and validate stock with row-level locking
        total_amount = 0
        order_items_data = []
        
        for item in order_data.items:
            # Lock the product row for update
            product = product_crud.get_for_update(db, item.product_id)
            if not product:
                raise ValueError(f"Product with id {item.product_id} not found")
            
            if product.stock < item.quantity:
                raise ValueError(f"Insufficient stock for product {product.name}. Available: {product.stock}, Requested: {item.quantity}")
            
            # Decrement stock
            product.stock -= item.quantity
            
            item_total = product.price * item.quantity
            total_amount += item_total
            
            order_items_data.append({
                "product_id": item.product_id,
                "quantity": item.quantity,
                "price": product.price
            })
        
        # Create order
        db_order = models.Order(
            idempotency_key=idempotency_key,
            total_amount=total_amount
        )
        db.add(db_order)
        db.flush()  # Get the order ID
        
        # Create order items
        for item_data in order_items_data:
            db_item = models.OrderItem(
                order_id=db_order.id,
                **item_data
            )
            db.add(db_item)
        
        db.commit()
        db.refresh(db_order)
        
        # Invalidate product cache since stock changed
        product_crud._invalidate_products_cache()
        
        return db_order

# Create CRUD 
product_crud = ProductCRUD()
order_crud = OrderCRUD()