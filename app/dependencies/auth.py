from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.repository.db import get_current_user

security = HTTPBearer()


async def get_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials

    response = get_current_user(token)

    if response.user is None:
        raise HTTPException(status_code=401, detail="Invalid token")

    return response.user