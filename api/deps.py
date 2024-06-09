from fastapi import Depends, HTTPException, status
from jose import JWTError, jwt
from fuzzywuzzy import fuzz
from core.config import config
from fastapi.security import OAuth2PasswordBearer
from typing import Annotated, List
from passlib.context import CryptContext
from core.security import get_password_hash


bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="api/v1/auth/token")


def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        user_name: str = payload.get("sub")
        user_id: int = payload.get("id")

        if user_name is None or user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate user",
            )

        return {"user_name": user_name, "user_id": user_id}

    except JWTError:
        print("CANT DECODE JWT")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate user"
        )


CurrentUser = Annotated[dict, Depends(get_current_user)]
