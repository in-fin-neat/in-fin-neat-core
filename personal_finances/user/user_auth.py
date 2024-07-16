import base64
import json
import logging
import boto3
import bcrypt
import jwt
import os
from datetime import datetime, timedelta
from typing import Any, Callable, Tuple
from decorator import decorator
from personal_finances.user.user_auth_exceptions import (
    AuthorizationHeaderNotPresent,
    AuthorizationHeaderEmptyContent,
    InvalidAuthorizationHeader,
    InvalidLambdaEventInput,
    UserNotFound,
    PasswordNotMatch,
    InvalidUserPassword,
    InvalidUserName,
    ServerSecretNotFound,
    InvalidDynamoResponse,
    get_server_response_by_exception,
)

LOGGER = logging.getLogger(__name__)
USER_ID_MIN_LEN = 6
USER_PASSWORD_MIN_LEN = 6


def _decode_basic_auth(auth_header: str) -> Tuple[str, str]:
    try:
        auth_value = auth_header.replace("Basic ", "")
        decoded_bytes = base64.b64decode(auth_value)
        decoded_str = decoded_bytes.decode("utf-8")
        userId, password = decoded_str.split(":", 1)
        return userId, password
    except Exception:
        raise InvalidAuthorizationHeader()


def _get_auth_header(event: dict) -> Any:
    headers = event.get("headers", None)
    if headers is None:
        raise InvalidLambdaEventInput()

    auth_header = headers.get("Authorization", None)
    if auth_header is None:
        raise AuthorizationHeaderNotPresent()

    if auth_header == "":
        raise AuthorizationHeaderEmptyContent()

    return auth_header


def _get_user_password(userId: str) -> str:
    dynamodb = boto3.resource("dynamodb")

    user_table = dynamodb.Table(os.environ["INFINEAT_DYNAMODB_USER_TABLE_NAME"])
    response = user_table.get_item(
        Key={"userId": userId},
    )
    print(response)
    if "Item" not in response:
        raise UserNotFound(f"User not found: {userId}")

    user = response["Item"]
    if "password" not in user or "userId" not in user:
        raise InvalidDynamoResponse

    return str(user["password"])


def _get_jwt_secret() -> str:
    jwt_session = boto3.client("secretsmanager")

    try:
        get_secret_value_response = jwt_session.get_secret_value(
            SecretId=os.environ["INFINEAT_JWT_SECRET_NAME"]
        )
    except Exception:
        raise ServerSecretNotFound

    return str(get_secret_value_response["SecretString"])


def _generate_token(user_id: str) -> str:
    return jwt.encode(
        {"exp": datetime.now() + timedelta(hours=1), "userId": user_id},
        _get_jwt_secret(),
        algorithm="HS256",
    )


def _password_match(recv_password: str, stored_password: str) -> bool:
    if bcrypt.checkpw(recv_password.encode("utf-8"), stored_password.encode("utf-8")):
        return True
    else:
        return False


def add_cors_to_dict(input_dict: dict) -> dict:
    return {**input_dict, "headers": {"Access-Control-Allow-Origin": "*"}}


def _check_user_id_constraints(user: str) -> None:
    if len(user) < USER_ID_MIN_LEN:
        raise InvalidUserName


def _check_user_password_constraints(password: str) -> None:
    if len(password) < USER_PASSWORD_MIN_LEN:
        raise InvalidUserPassword


@decorator
def add_cors_decorator(handler: Callable, *args: Any, **kwargs: Any) -> dict:
    return add_cors_to_dict(handler(*args, **kwargs))


@add_cors_decorator
def user_handler(event: dict, context: str) -> dict:
    try:
        auth_header = _get_auth_header(event)
        userId, recv_password = _decode_basic_auth(auth_header)
        _check_user_id_constraints(userId)
        _check_user_password_constraints(recv_password)
        stored_password = _get_user_password(userId)
        token = ""

        if _password_match(recv_password, stored_password):
            token = _generate_token(userId)
        else:
            raise PasswordNotMatch()

        token_json = json.dumps({"token": token})
        return {"statusCode": 200, "body": f"{token_json}"}

    except Exception as e:
        LOGGER.exception(
            f"""
            An error at the user authentication lambda has happened {e}
            """
        )
        fail_response = get_server_response_by_exception(e)
        if fail_response == {}:
            fail_response = {"statusCode": 500, "body": "Internal Server Error"}
        return fail_response


def create_user_hash_password(password: str) -> bytes:
    _check_user_password_constraints(password)
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt())
