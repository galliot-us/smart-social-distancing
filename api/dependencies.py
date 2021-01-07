from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError

from libs.utils.auth import validate_jwt_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def validate_token(token: str = Depends(oauth2_scheme)):
    try:
        validate_jwt_token(token)
    except JWTError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
