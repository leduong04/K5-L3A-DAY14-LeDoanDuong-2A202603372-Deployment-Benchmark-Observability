"""API key authentication dependency."""
import hmac
from fastapi import Header, HTTPException
from app.config import settings


def verify_api_key(x_api_key: str | None = Header(default=None, alias="X-API-Key")) -> str:
    if not x_api_key or not settings.agent_api_key or not hmac.compare_digest(x_api_key, settings.agent_api_key):
        raise HTTPException(status_code=401, detail="Invalid or missing API key", headers={"WWW-Authenticate": "ApiKey"})
    return x_api_key
