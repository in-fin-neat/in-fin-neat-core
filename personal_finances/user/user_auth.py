import base64
from datetime import datetime, timedelta
from typing import Any, Tuple
import boto3
import bcrypt
import jwt


class AuthorizationNotFound(Exception):
    pass


class UserNotFound(Exception):
    pass


class UserInvalidPassword(Exception):
    pass


def _decode_basic_auth(auth_header: str) -> Tuple[str, str]:
    auth_value = auth_header.replace("Basic ", "")
    decoded_bytes = base64.b64decode(auth_value)
    decoded_str = decoded_bytes.decode("utf-8")
    userId, password = decoded_str.split(":", 1)
    return userId, password


def _get_auth_header(event: dict) -> str:
    auth_header = str(event.get("headers", {}).get("Authorization", ""))

    if not auth_header:
        raise AuthorizationNotFound()

    return auth_header


def _get_user(userId: str) -> dict[Any, Any]:
    dynamodb = boto3.client("dynamodb")

    response = dynamodb.get_item(
        TableName="InFinNeatCdkStack-UserServiceuserTable949F323B-6TDADGI3HR8B",
        Key={"userId": {"S": userId}},
    )

    user: dict = response.get("Item")
    if not user:
        raise UserNotFound(f"User not found: {userId}")

    return user


def _generate_token() -> str:
    return jwt.encode(
        {"exp": datetime.now() + timedelta(hours=1)},
        "03468f8c63a5a4f0dd9fba96b6ba849a4a5092573ec7eeefeff2437e08dc633e",
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
            token = _generate_token()
        else:
            raise UserInvalidPassword()

        return {"statusCode": 200, "body": token}

    except (UserNotFound, UserInvalidPassword):
        return {"statusCode": 401, "body": "User or password incorrect"}
    except AuthorizationNotFound:
        return {
            "statusCode": 400,
            "body": "Error decoding authentication header",
        }
    except Exception as e:
        return {
            "statusCode": 400,
            "body": f"Error on user login procedure: {str(e)}",
        }


def create_user_hash_password(password: str) -> bytes:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt())
