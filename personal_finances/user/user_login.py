import base64
import logging
from personal_finances.bank_interface.password_handler import (
    password_match,
    create_hash_password,
)
from typing import Tuple
from personal_finances.user.jwt_utils import generate_token
from personal_finances.user.user_auth_exceptions import (
    InvalidAuthorizationHeader,
    PasswordNotMatch,
    InvalidUserPassword,
    InvalidUserName,
)
from personal_finances.user.user_persistence import get_user_password

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


def _check_user_id_constraints(user: str) -> None:
    if len(user) < USER_ID_MIN_LEN:
        raise InvalidUserName


def _check_user_password_constraints(password: str) -> None:
    if len(password) < USER_PASSWORD_MIN_LEN:
        raise InvalidUserPassword


def user_login(auth_str_value: str) -> str:

    userId, recv_password = _decode_basic_auth(auth_str_value)

    _check_user_id_constraints(userId)
    _check_user_password_constraints(recv_password)
    LOGGER.info(f"New login attempt for user: {userId}")

    stored_password = get_user_password(userId)
    token = ""

    if password_match(recv_password, stored_password):
        token = generate_token(userId)
    else:
        LOGGER.info(f"Password does not match for user: {userId}")
        raise PasswordNotMatch()

    LOGGER.info(f"Login sucessfuly for user: {userId}")
    return token


def create_user_hash_password(password: str) -> bytes:
    _check_user_password_constraints(password)
    return create_hash_password(password)
