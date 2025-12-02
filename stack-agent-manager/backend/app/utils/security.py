from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
import bcrypt

from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Ensure password is a string
    if isinstance(plain_password, bytes):
        plain_password = plain_password.decode('utf-8')
    
    # Ensure password doesn't exceed bcrypt's 72-byte limit
    password_bytes = plain_password.encode('utf-8')
    if len(password_bytes) > 72:
        # Truncate to 72 bytes, but try to preserve valid UTF-8
        truncated = password_bytes[:72]
        # Remove any incomplete UTF-8 sequences at the end
        while truncated and truncated[-1] & 0x80 and not (truncated[-1] & 0x40):
            truncated = truncated[:-1]
        plain_password = truncated.decode('utf-8', errors='ignore')
    
    # Use bcrypt directly to match the hashing function
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    # Ensure password is a string
    if isinstance(password, bytes):
        password = password.decode('utf-8')
    
    # Ensure password doesn't exceed bcrypt's 72-byte limit
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        # Truncate to 72 bytes, but try to preserve valid UTF-8
        truncated = password_bytes[:72]
        # Remove any incomplete UTF-8 sequences at the end
        while truncated and truncated[-1] & 0x80 and not (truncated[-1] & 0x40):
            truncated = truncated[:-1]
        password = truncated.decode('utf-8', errors='ignore')
    
    # Use bcrypt directly to avoid passlib initialization issues
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.access_token_expire_minutes
        )
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except JWTError:
        return None

