# routes/helpers.py
# Shared token extraction helper used by all route files

from jose import jwt, JWTError
from fastapi import HTTPException
import os

SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")
ALGORITHM = "HS256"

def extract_user_id(authorization: str) -> int:
    """Extract user_id from Bearer token in Authorization header"""
    try:
        token = authorization.replace("Bearer ", "").replace("bearer ", "")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        return int(user_id)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")