import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class AuthSettings(BaseModel):
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 120


class Settings(BaseModel):
    database_url: str
    port: int = 8080
    host: str = "127.0.0.1"
    rate_limit_requests: int = 120
    rate_limit_window_seconds: int = 60
    auth: AuthSettings


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} is not set. Add {name} to .env")
    return value


def load_config() -> Settings:
    return Settings(
        database_url=_required_env("DATABASE_URL"),
        port=int(os.getenv("APP_PORT", "8080")),
        host=os.getenv("APP_HOST", "127.0.0.1"),
        rate_limit_requests=int(os.getenv("RATE_LIMIT_REQUESTS", "120")),
        rate_limit_window_seconds=int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60")),
        auth=AuthSettings(
            secret_key=_required_env("SECRET_KEY"),
            algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
            access_token_expire_minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "120")),
        ),
    )


settings = load_config()
