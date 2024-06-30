import base64
from datetime import datetime, timedelta
import json
import jwt
import pytest
from unittest.mock import Mock, patch
from typing import Generator, Union
from personal_finances.user.user_auth import user_handler, create_user_hash_password


TEST_USER_ID = "testuser"
TEST_USER_PASSWORD = "123"
TEST_USER_DYNAMO_RESPONSE = {
    "Item": {
        "userId": {"S": TEST_USER_ID},
        "password": {
            # password "123" hashed by bcrypt
            "S": "$2b$12$735jLXvW38meOqPXIwhsSO1bNP6AcFY7K4K3WuPiDsdD7wajOrhp2"
        },
    }
}
TEST_JWT_SECRETS = "jwt_secret"
TEST_DATE_TIME_NOW = datetime(2060, 1, 1, 10, 00, 00)
TEST_ENVAR_DICT = {
    "INFINEAT_DYNAMODB_USER_TABLE_NAME": "table_name",
    "INFINEAT_JWT_SECRET_ID": "jwt_secret",
}


def _encode_basic_auth(user: str, password: str) -> str:
    credentials = f"{user}:{password}"
    credentials_encoded = credentials.encode()
    authorization_encoded = base64.b64encode(credentials_encoded)
    authorization = f"Basic {authorization_encoded.decode()}"
    return authorization


@pytest.fixture(autouse=True)
def os_mock() -> Generator[Mock, None, None]:
    with patch("personal_finances.user.user_auth.os") as mock:
        yield mock


@pytest.fixture(autouse=True)
def boto3_mock() -> Generator[Mock, None, None]:
    with patch("personal_finances.user.user_auth.boto3.client") as mock:
        yield mock


@pytest.fixture(autouse=True)
def datetime_mock() -> Generator[Mock, None, None]:
    with patch("personal_finances.user.user_auth.datetime") as mock:
        mock.now.return_value = TEST_DATE_TIME_NOW
        yield mock


def _generate_test_jwt_token() -> str:
    return jwt.encode(
        {"exp": TEST_DATE_TIME_NOW + timedelta(hours=1), "userId": TEST_USER_ID},
        TEST_JWT_SECRETS,
        algorithm="HS256",
    )


@pytest.mark.parametrize(
    "authorization_header, expected_response, dynamo_response_dict, env_var_dict",
    [
        (
            _encode_basic_auth(TEST_USER_ID, "incorrect_password"),
            {"statusCode": 401, "body": "User or password incorrect"},
            TEST_USER_DYNAMO_RESPONSE,
            TEST_ENVAR_DICT,
        ),
        (
            _encode_basic_auth("incorrect_user", "incorrect_password"),
            {"statusCode": 401, "body": "User or password incorrect"},
            {"usernot": "found"},
            TEST_ENVAR_DICT,
        ),
        (
            "incorrect_header",
            {"statusCode": 400, "body": "Malformed authentication header"},
            TEST_USER_DYNAMO_RESPONSE,
            TEST_ENVAR_DICT,
        ),
        (
            _encode_basic_auth(TEST_USER_ID, TEST_USER_PASSWORD),
            {
                "statusCode": 200,
                "body": json.dumps({"token": _generate_test_jwt_token()}),
            },
            TEST_USER_DYNAMO_RESPONSE,
            TEST_ENVAR_DICT,
        ),
        (
            _encode_basic_auth(TEST_USER_ID, TEST_USER_PASSWORD),
            {
                "statusCode": 500,
                "body": "Internal Server Error",
            },
            Exception,
            TEST_ENVAR_DICT,
        ),
        (
            _encode_basic_auth(TEST_USER_ID, TEST_USER_PASSWORD),
            {
                "statusCode": 500,
                "body": "Internal Server Error",
            },
            TEST_USER_DYNAMO_RESPONSE,
            Exception,
        ),
    ],
)
def test_user_auth(
    authorization_header: str,
    expected_response: dict,
    dynamo_response_dict: Union[dict, Exception],
    env_var_dict: Union[dict, Exception],
    os_mock: Mock,
    boto3_mock: Mock,
) -> None:
    if isinstance(env_var_dict, dict):
        os_mock.environ.__getitem__.side_effect = env_var_dict.get
    else:
        os_mock.environ.__getitem__.side_effect = env_var_dict

    aws_client_mock = boto3_mock.return_value
    aws_client_mock.get_item.return_value = dynamo_response_dict
    aws_client_mock.get_secret_value.return_value = {"SecretString": TEST_JWT_SECRETS}

    TEST_EVENT_INPUT = {"headers": {"Authorization": authorization_header}}

    response = user_handler(TEST_EVENT_INPUT, "")

    assert response == expected_response
    if response["statusCode"] == 200:
        token = json.loads(response["body"])["token"]
        try:
            jwt.decode(token, TEST_JWT_SECRETS, algorithms=["HS256"])
            assert True
        except Exception as e:
            print(e)
            assert False


@patch("personal_finances.user.user_auth.bcrypt.gensalt")
def test_password_creation(gensalt: Mock) -> None:
    gensalt.return_value = b"$2b$12$tBzFe5aHXtLmOPWSQWcy2e"
    response = create_user_hash_password("123")
    assert response == b"$2b$12$tBzFe5aHXtLmOPWSQWcy2ehgK4U2m2uZwvDIW1BXsoCnUVKNwzkdm"
