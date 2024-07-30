import base64
import json
import logging
import boto3
import bcrypt
import os
from typing import Any, Callable, Tuple
from decorator import decorator
from personal_finances.user.jwt_utils import generate_token
from personal_finances.user.user_auth_exceptions import (
    AuthorizationHeaderNotPresent,
    AuthorizationHeaderEmptyContent,
    InvalidAuthorizationHeader,
    InvalidLambdaEventInput,
    UserNotFound,
    PasswordNotMatch,
    InvalidUserPassword,
    InvalidUserName,
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


def _get_auth_header(event: dict) -> str:
    headers = event.get("headers", None)
    if headers is None:
        raise InvalidLambdaEventInput()

    auth_header = headers.get("Authorization", None)
    if auth_header is None:
        raise AuthorizationHeaderNotPresent()

    if auth_header == "":
        raise AuthorizationHeaderEmptyContent()

    return str(auth_header)


def _get_user_password(userId: str) -> str:
    dynamodb = boto3.resource("dynamodb")

    user_table = dynamodb.Table(os.environ["INFINEAT_DYNAMODB_USER_TABLE_NAME"])
    response = user_table.get_item(
        Key={"userId": userId},
    )
    if "Item" not in response:
        raise UserNotFound(f"User not found: {userId}")

    user = response["Item"]
    if "password" not in user or "userId" not in user:
        raise InvalidDynamoResponse

    return str(user["password"])


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
        LOGGER.info(f"New login attempt for user: {userId}")

        stored_password = _get_user_password(userId)
        token = ""

        if _password_match(recv_password, stored_password):
            token = generate_token(userId)
        else:
            LOGGER.info(f"Password does not match for user: {userId}")
            raise PasswordNotMatch()

        LOGGER.info(f"Login sucessfuly for user: {userId}")
        token_json = json.dumps({"token": token})
        return {"statusCode": 200, "body": f"{token_json}"}

    except Exception as e:
        LOGGER.exception(
            f"""
            An error at the user authentication lambda has happened {e}
            """
        )
        fail_response = get_server_response_by_exception(e)
        return fail_response


def create_user_hash_password(password: str) -> bytes:
    _check_user_password_constraints(password)
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt())
