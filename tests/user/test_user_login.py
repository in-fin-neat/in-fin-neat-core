import base64
import pytest
from unittest.mock import Mock, patch
from typing import Generator, Type
from personal_finances.user.user_login import user_login, create_user_hash_password
from personal_finances.user.user_auth_exceptions import (
    InvalidAuthorizationHeader,
    InvalidUserName,
    InvalidUserPassword,
    PasswordNotMatch,
    UserNotFound,
)


TEST_USER_ID = "testuser"
TEST_USER_PASSWORD = "|SkfzqE9h={!,o9BvQc{"
TEST_USER_PASSWORD_HASH = "$argon2id$v=19$m=65536,t=3,p=4$Z6dp5ZCLb637IaSncEJg2A$" \
    "LZj7vnKtnnC24+82v82KWCjYK6GIn9jC2vatgTLSru0"
TEST_JWT_TOKEN = "jwt_token"


@pytest.fixture(autouse=True)
def get_user_password_mock() -> Generator[Mock, None, None]:
    with patch("personal_finances.user.user_login.get_user_password") as mock:
        mock.return_value = TEST_USER_PASSWORD_HASH
        yield mock


@pytest.fixture(autouse=True)
def generate_token_mock() -> Generator[Mock, None, None]:
    with patch("personal_finances.user.user_login.generate_token") as mock:
        mock.return_value = TEST_JWT_TOKEN
        yield mock


def _encode_basic_auth(user: str, password: str) -> str:
    credentials = f"{user}:{password}"
    credentials_encoded = credentials.encode()
    authorization_encoded = base64.b64encode(credentials_encoded)
    authorization = f"Basic {authorization_encoded.decode()}"
    return authorization


@pytest.mark.parametrize(
    "input_token, expected_exception",
    [
        (
            "invalid authorization header string",
            InvalidAuthorizationHeader,
        ),
        (
            _encode_basic_auth(TEST_USER_ID, "incorrect_password"),
            PasswordNotMatch,
        ),
        (
            _encode_basic_auth("abc", TEST_USER_PASSWORD),
            InvalidUserName,
        ),
        (
            _encode_basic_auth(TEST_USER_ID, "123ab"),
            InvalidUserPassword,
        ),
    ],
)
def test_user_login_general_edge_cases(
    input_token: str,
    expected_exception: Type[Exception],
) -> None:

    with pytest.raises(expected_exception):
        user_login(input_token)


def test_user_not_found(get_user_password_mock: Mock) -> None:
    get_user_password_mock.side_effect = UserNotFound
    with pytest.raises(expected_exception=UserNotFound):
        user_login(_encode_basic_auth("dummy_user", TEST_USER_PASSWORD))


def test_user_password_match(
    get_user_password_mock: Mock, generate_token_mock: Mock
) -> None:
    get_user_password_mock.return_value = TEST_USER_PASSWORD_HASH
    generate_token_mock.return_value = "test_token"
    return_token = user_login(_encode_basic_auth("dummy_user", TEST_USER_PASSWORD))

    get_user_password_mock.assert_called_once_with("dummy_user")
    get_user_password_mock.assert_called_once_with("dummy_user")

    assert return_token == generate_token_mock.return_value


def test_invalid_input_password_creation() -> None:
    with pytest.raises(InvalidUserPassword):
        create_user_hash_password("abc")
