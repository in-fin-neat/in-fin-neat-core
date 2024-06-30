import base64
import json
import logging
import boto3
import bcrypt
import jwt
import os
from datetime import datetime, timedelta
from typing import Any, Tuple

LOGGER = logging.getLogger(__name__)


class AuthorizationNotFound(Exception):
    def __str__(self) -> str:
        return "AuthorizationNotFoundException"


class UserNotFound(Exception):
    def __str__(self) -> str:
        return "UserNotFoundException"


class UserInvalidPassword(Exception):
    def __str__(self) -> str:
        return "UserInvalidPasswordException"


def _decode_basic_auth(auth_header: str) -> Tuple[str, str]:
    try:
        auth_value = auth_header.replace("Basic ", "")
        decoded_bytes = base64.b64decode(auth_value)
        decoded_str = decoded_bytes.decode("utf-8")
        userId, password = decoded_str.split(":", 1)
        return userId, password
    except Exception:
        raise AuthorizationNotFound()


def _get_auth_header(event: dict) -> str:
    auth_header = str(event.get("headers", {}).get("Authorization", ""))

    if not auth_header:
        raise AuthorizationNotFound()

    return auth_header


def _get_user(userId: str) -> dict[Any, Any]:
    dynamodb = boto3.client("dynamodb")
    response = dynamodb.get_item(
        TableName=os.environ["INFINEAT_DYNAMODB_USER_TABLE_NAME"],
        Key={"userId": {"S": userId}},
    )

    user: dict = response.get("Item")
    if not user:
        raise UserNotFound(f"User not found: {userId}")

    return user


def _get_jwt_secret() -> str:
    jwt_session = boto3.client("secretsmanager")

    get_secret_value_response = jwt_session.get_secret_value(
        SecretId=os.environ["INFINEAT_JWT_SECRET_ID"]
    )

    return str(get_secret_value_response["SecretString"])


def _generate_token(user: dict) -> str:
    return jwt.encode(
        {"exp": datetime.now() + timedelta(hours=1), "userId": user["userId"]["S"]},
        _get_jwt_secret(),
        algorithm="HS256",
    )


def _password_match(recv_password: str, user: dict) -> bool:
    stored_password = user["password"]["S"].encode("utf-8")
    if bcrypt.checkpw(recv_password.encode("utf-8"), stored_password):
        return True
    else:
        return False


def user_handler(event: dict, context: str) -> dict:
    try:
        auth_header = _get_auth_header(event)
        userId, recv_password = _decode_basic_auth(auth_header)
        user = _get_user(userId)
        token = ""
        if _password_match(recv_password, user):
            token = _generate_token(user)
        else:
            raise UserInvalidPassword()

        token_json = json.dumps({"token": token})
        return {"statusCode": 200, "body": f"{token_json}"}

    except Exception as e:
        LOGGER.exception(
            f"""
            An error at the user authentication lambda has happened {e}
            """
        )
        fail_response = None

        if isinstance(e, UserNotFound) or isinstance(e, UserInvalidPassword):
            fail_response = {"statusCode": 401, "body": "User or password incorrect"}
        elif isinstance(e, AuthorizationNotFound):
            fail_response = {
                "statusCode": 400,
                "body": "Malformed authentication header",
            }
        else:
            fail_response = {"statusCode": 500, "body": "Internal Server Error"}
        return fail_response


def create_user_hash_password(password: str) -> bytes:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt())
