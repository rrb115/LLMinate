from fastapi import Header, HTTPException

from app.core.config import settings


def require_local_auth(x_local_auth: str = Header(default="")) -> None:
    if x_local_auth != settings.local_auth_token:
        raise HTTPException(status_code=401, detail="Invalid local auth token")
