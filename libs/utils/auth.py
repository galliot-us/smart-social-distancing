import json
import logging
import os

from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext

logger = logging.getLogger(__name__)

API_USER_CREDENTIALS_FOLDER = "/repo/data/auth/"
API_USER_PATH = f"{API_USER_CREDENTIALS_FOLDER}/api_user.txt"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

user_cache = dict()


def create_api_user(user: str, password: str):
    if os.path.isfile(API_USER_PATH) and os.path.getsize(API_USER_PATH) != 0:
        # API credential already created
        logger.error("API credentials already created.")
        raise Exception("Error creating user. API credentials already created.")
    os.makedirs(API_USER_CREDENTIALS_FOLDER, exist_ok=True)
    with open(API_USER_PATH, "w+") as api_user_file:
        api_user_credentials = {
            "user": user,
            "password": pwd_context.hash(password)
        }
        json.dump(api_user_credentials, api_user_file)


def validate_user_credentials(user: str, password: str) -> bool:
    if not os.path.isfile(API_USER_PATH) or os.path.getsize(API_USER_PATH) == 0:
        logger.error("API credentials doesn't exit.")
        return False

    with open(API_USER_PATH, "r") as api_user_file:
        stored_credentials = json.load(api_user_file)

    if stored_credentials["user"] != user or not pwd_context.verify(password, stored_credentials["password"]):
        return False

    return True


def create_access_token(user: str):
    # Set a week (60*24*7=10080) as expiration date
    expire_date = datetime.utcnow() + timedelta(minutes=10080)
    data = {"sub": user}
    data.update({"exp": expire_date})
    return jwt.encode(data, os.environ.get("SECRET_ACCESS_KEY"), algorithm="HS256")


def validate_jwt_token(token):
    playload = jwt.decode(token, os.environ.get("SECRET_ACCESS_KEY"), algorithms=["HS256"])
    if not user_cache.get("user"):
        with open(API_USER_PATH, "r") as api_user_file:
            stored_credentials = json.load(api_user_file)
            user_cache["user"] = stored_credentials["user"]
    if playload["sub"] != user_cache["user"]:
        raise Exception("JWT doesn't belong to user.")
