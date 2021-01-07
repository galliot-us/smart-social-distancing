from fastapi import APIRouter, status
from starlette.exceptions import HTTPException

from api.models.auth import AuthDTO, Token
from api.utils import bad_request_serializer
from libs.utils.auth import create_access_token, create_api_user, validate_user_credentials

auth_router = APIRouter()


@auth_router.post("/create_api_user", status_code=status.HTTP_204_NO_CONTENT)
async def create_user(auth_info: AuthDTO):
    """
    Creates the API user (if it's not already created) with the given password.
    """
    try:
        create_api_user(auth_info.user, auth_info.password)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=bad_request_serializer(str(e))
        )


@auth_router.put("/access_token", response_model=Token)
async def get_access_token(auth_info: AuthDTO):
    if not validate_user_credentials(auth_info.user, auth_info.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    return {
        "token": create_access_token(auth_info.user)
    }
