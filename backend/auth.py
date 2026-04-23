import os
import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from backend.db import get_db
from backend.models import User

SECRET_KEY = os.getenv("AUTH_SECRET") or secrets.token_urlsafe(64)
ALGORITHM = "HS256"
TOKEN_TTL_HOURS = 24 * 7  # 1 week

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login", auto_error=True)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def create_access_token(email: str) -> str:
    expires = datetime.now(timezone.utc) + timedelta(hours=TOKEN_TTL_HOURS)
    return jwt.encode({"sub": email, "exp": expires}, SECRET_KEY, algorithm=ALGORITHM)


def current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    creds_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
    except jwt.PyJWTError:
        raise creds_exc

    if not email:
        raise creds_exc

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise creds_exc
    return user
