from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app import crud, schemas
from app.dependencies import get_db

router = APIRouter(prefix="/products", tags=["products"])

@router.post("/", response_model=schemas.Product, status_code=status.HTTP_201_CREATED)
def create_product(
    product: schemas.ProductCreate,
    db: Session = Depends(get_db)
):
    return crud.product_crud.create(db=db, product=product)

@router.get("/", response_model=List[schemas.Product])
def read_products(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    return crud.product_crud.get_multi(db, skip=skip, limit=limit)

@router.get("/{product_id}", response_model=schemas.Product)
def read_product(product_id: int, db: Session = Depends(get_db)):
    db_product = crud.product_crud.get(db, product_id=product_id)
    if db_product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    return db_product

@router.put("/{product_id}", response_model=schemas.Product)
def update_product(
    product_id: int,
    product: schemas.ProductUpdate,
    db: Session = Depends(get_db)
):
    db_product = crud.product_crud.update(db, product_id=product_id, product=product)
    if db_product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    return db_product

@router.delete("/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    success = crud.product_crud.delete(db, product_id=product_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    return {"message": "Product deleted successfully"}