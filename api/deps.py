from fastapi import Depends, HTTPException, status
from jose import JWTError, jwt
from core.config import config
from fastapi.security import OAuth2PasswordBearer
from typing import Annotated
from passlib.context import CryptContext


bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="auth/token")


def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        user_name: str = payload.get("sub") or ""
        user_id: int = payload.get("id") or -1

        if user_name is None or user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate user",
            )

        return {"user_name": user_name, "user_id": user_id}

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate user"
        )


CurrentUser = Annotated[dict, Depends(get_current_user)]
