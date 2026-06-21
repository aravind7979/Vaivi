from datetime import datetime, timedelta
import os
import jwt
import hashlib
import json

from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db
import models
from cache import redis_client

# =========================
# CONFIG
# =========================

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "supersecretkey_vaivi_local_dev")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/login")


# =========================
# PASSWORD HANDLING
# =========================

def _pre_hash(password: str) -> str:
    """
    Normalize password to fixed length using SHA-256
    This avoids bcrypt 72-byte limitation.
    """
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    pre_hashed = _pre_hash(plain_password)
    return pwd_context.verify(pre_hashed, hashed_password)


def get_password_hash(password: str) -> str:
    pre_hashed = _pre_hash(password)
    return pwd_context.hash(pre_hashed)


# =========================
# JWT TOKEN
# =========================

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# =========================
# AUTH DEPENDENCY
# =========================

class CachedUser:
    def __init__(self, id, email, hashed_password, shortcut_keys):
        self.id = id
        self.email = email
        self.hashed_password = hashed_password
        self.shortcut_keys = shortcut_keys

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")

        if email is None:
            raise credentials_exception

    except jwt.PyJWTError:
        raise credentials_exception

    cache_key = f"user:email:{email}"
    
    if redis_client:
        cached_user = redis_client.get(cache_key)
        if cached_user:
            print(f"[CACHE HIT] Loaded user {email} from Redis")
            return CachedUser(**json.loads(cached_user))

    user = db.query(models.User).filter(models.User.email == email).first()

    if user is None:
        raise credentials_exception

    if redis_client:
        redis_client.setex(cache_key, 3600, json.dumps({
            "id": user.id,
            "email": user.email,
            "hashed_password": user.hashed_password,
            "shortcut_keys": user.shortcut_keys
        }))
        print(f"[CACHE MISS] Loaded user {email} from Postgres and populated Redis")

    return user