from passlib.context import CryptContext
from datetime import datetime, timedelta
from fastapi import HTTPException
from jose import jwt
from core.config import config


bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt_context.verify(plain_password, hashed_password)


def create_access_token(username: str, user_id: int, expired_delta: timedelta):
    encode = {"sub": username, "id": user_id}
    expires = datetime.utcnow() + expired_delta
    encode.update({"exp": expires})

    try:
        return jwt.encode(encode, config.SECRET_KEY, algorithm=config.ALGORITHM)
    except Exception as e:
        raise HTTPException(
            status_code=501, detail=f"The error is in encoding jwt : {str(e)}"
        )


def get_password_hash(password: str) -> str:
    return bcrypt_context.hash(password)
