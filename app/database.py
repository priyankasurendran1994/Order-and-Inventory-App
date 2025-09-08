from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import redis
from app.core.config import settings

# Select database based on environment
if settings.env == "test":
    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False}  # SQLite-specific
    )
else:
    engine = create_engine(settings.database_url)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Redis client
redis_client = None
if settings.redis_url:
    try:
        redis_client = redis.from_url(settings.redis_url, decode_responses=True)
    except Exception:
        redis_client = None

# Dependency for FastAPI & tests
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
