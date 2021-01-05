from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError

from libs.utils.auth import validate_jwt_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def validate_token(token: str = Depends(oauth2_scheme)):
    try:
        validate_jwt_token(token)
    except JWTError as e:
        raise HTTPException(status_code=401, detail=str(e))
