from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    database_url: str = "postgresql://user:password@localhost:5432/orderdb"
    redis_url: Optional[str] = "redis://localhost:6379"
    
    class Config:
        env_file = ".env"

settings = Settings()