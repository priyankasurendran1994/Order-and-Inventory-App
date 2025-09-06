from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.orm import Session
from typing import Optional
from app import crud, schemas
from app.dependencies import get_db, generate_idempotency_key

router = APIRouter(prefix="/orders", tags=["orders"])

@router.post("/", response_model=schemas.Order, status_code=status.HTTP_201_CREATED)
def create_order(
    order: schemas.OrderCreate,
    db: Session = Depends(get_db),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key")
):
    if not idempotency_key:
        idempotency_key = generate_idempotency_key()
        print("generated key",idempotency_key)
    
    try:
        return crud.order_crud.create_with_items(
            db=db, 
            order_data=order, 
            idempotency_key=idempotency_key
        )
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg
            )
        elif "Insufficient stock" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=error_msg
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )

@router.get("/", response_model=schemas.PaginatedOrders)
def read_orders(
    limit: int = 50,
    cursor: Optional[str] = None,
    db: Session = Depends(get_db)
):
    if limit > 100:
        limit = 100
    
    orders, next_cursor, has_more = crud.order_crud.get_multi_paginated(
        db, limit=limit, cursor=cursor
    )
    
    return schemas.PaginatedOrders(
        orders=orders,
        next_cursor=next_cursor,
        has_more=has_more
    )

@router.get("/{order_id}", response_model=schemas.Order)
def read_order(order_id: int, db: Session = Depends(get_db)):
    db_order = crud.order_crud.get(db, order_id=order_id)
    if db_order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    return db_order