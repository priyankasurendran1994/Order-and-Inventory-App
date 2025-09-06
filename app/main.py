from fastapi import FastAPI
from app.routers import products, orders
from app.database import engine
from app import models

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Order & Inventory API",
    description="A concurrency-safe e-commerce Order & Inventory backend",
    version="1.0.0",
)

# Include routers
app.include_router(products.router)
app.include_router(orders.router)

@app.get("/")
def read_root():
    return {"message": "Order & Inventory API is running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)