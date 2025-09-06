from sqlalchemy.orm import Session
from app.database import SessionLocal
import uuid

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def generate_idempotency_key():
    return str(uuid.uuid4())