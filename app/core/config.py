from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    env: str = os.getenv("ENV", "dev")  # dev | test | prod
    database_url: str
    redis_url: Optional[str] = None
    debug: bool = False

    class Config:
        env_file = (
            ".env.dev" if os.getenv("ENV") == "dev"
            else ".env.test" if os.getenv("ENV") == "test"
            else ".env.prod"
        )

settings = Settings()
