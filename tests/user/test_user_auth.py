import base64
from datetime import datetime, timedelta
import json
import os
import jwt
import pytest
from unittest.mock import Mock, patch
from typing import Generator, Union
from personal_finances.user.user_auth import (
    add_cors_to_dict,
    user_handler,
    create_user_hash_password,
)


TEST_USER_ID = "testuser"
TEST_USER_PASSWORD = "|SkfzqE9h={!,o9BvQc{"
TEST_USER_DYNAMO_RESPONSE = {
    "Item": {
        "userId": TEST_USER_ID,
        "password": "$2b$12$tBzFe5aHXtLmOPWSQWcy2ekjqxf4R5p9C99oWDxv/EJz7bYHE2Ez2",
    }
}


TEST_JWT_SECRETS = "jwt_secret"
TEST_DATE_TIME_NOW = datetime(2060, 1, 1, 10, 00, 00)
TEST_ENVAR_DICT = {
    "INFINEAT_DYNAMODB_USER_TABLE_NAME": "table_name",
    "INFINEAT_JWT_SECRET_NAME": "jwt_secret",
}


def _encode_basic_auth(user: str, password: str) -> str:
    credentials = f"{user}:{password}"
    credentials_encoded = credentials.encode()
    authorization_encoded = base64.b64encode(credentials_encoded)
    authorization = f"Basic {authorization_encoded.decode()}"
    return authorization


@pytest.fixture(autouse=True)
def boto3_client_mock() -> Generator[Mock, None, None]:
    with patch("personal_finances.user.user_auth.boto3.client") as mock:
        yield mock


@pytest.fixture(autouse=True)
def boto3_resource_mock() -> Generator[Mock, None, None]:
    with patch("personal_finances.user.user_auth.boto3.resource") as mock:
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
    "event_input, expected_response, dynamo_response_dict_or_exception, env_var_dict",
    [
        (
            {
                "headers": {
                    "Authorization": _encode_basic_auth(
                        TEST_USER_ID, "incorrect_password"
                    )
                }
            },
            {"statusCode": 401, "body": "User or password incorrect"},
            TEST_USER_DYNAMO_RESPONSE,
            TEST_ENVAR_DICT,
        ),
        (
            {
                "headers": {
                    "Authorization": _encode_basic_auth(
                        "incorrect_user", "incorrect_password"
                    )
                }
            },
            {"statusCode": 401, "body": "User or password incorrect"},
            {},
            TEST_ENVAR_DICT,
        ),
        (
            {"headers": {"Authorization": "incorrect_header"}},
            {"statusCode": 400, "body": "Invalid authentication input"},
            TEST_USER_DYNAMO_RESPONSE,
            TEST_ENVAR_DICT,
        ),
        (
            {"headers": {"Authorization": ""}},
            {"statusCode": 400, "body": "Invalid authentication input"},
            TEST_USER_DYNAMO_RESPONSE,
            TEST_ENVAR_DICT,
        ),
        (
            {"headers": {}},
            {"statusCode": 400, "body": "Invalid authentication input"},
            TEST_USER_DYNAMO_RESPONSE,
            TEST_ENVAR_DICT,
        ),
        (
            {
                "headers": {
                    "Authorization": _encode_basic_auth("user", "dummy_password")
                }
            },
            {
                "statusCode": 400,
                "body": (
                    "Username or password does not match the minimal "
                    + "security requirements"
                ),
            },
            {},
            {},
        ),
        (
            {"headers": {"Authorization": _encode_basic_auth("dummy_user", "pass")}},
            {
                "statusCode": 400,
                "body": (
                    "Username or password does not match the minimal "
                    + "security requirements"
                ),
            },
            {},
            {},
        ),
        (
            {},
            {"statusCode": 500, "body": "Internal Server Error"},
            TEST_USER_DYNAMO_RESPONSE,
            TEST_ENVAR_DICT,
        ),
        (
            {
                "headers": {
                    "Authorization": _encode_basic_auth(
                        TEST_USER_ID, TEST_USER_PASSWORD
                    )
                }
            },
            {"statusCode": 500, "body": "Internal Server Error"},
            {"Item": {"dummyKey": "dummyValue"}},
            TEST_ENVAR_DICT,
        ),
        (
            {
                "headers": {
                    "Authorization": _encode_basic_auth(
                        TEST_USER_ID, TEST_USER_PASSWORD
                    )
                }
            },
            {
                "statusCode": 500,
                "body": "Internal Server Error",
            },
            Exception,
            TEST_ENVAR_DICT,
        ),
        (
            {
                "headers": {
                    "Authorization": _encode_basic_auth(
                        TEST_USER_ID, TEST_USER_PASSWORD
                    )
                }
            },
            {
                "statusCode": 500,
                "body": "Internal Server Error",
            },
            TEST_USER_DYNAMO_RESPONSE,
            {},
        ),
        (
            {
                "headers": {
                    "Authorization": _encode_basic_auth(
                        TEST_USER_ID, TEST_USER_PASSWORD
                    )
                }
            },
            {
                "statusCode": 200,
                "body": json.dumps({"token": _generate_test_jwt_token()}),
            },
            TEST_USER_DYNAMO_RESPONSE,
            TEST_ENVAR_DICT,
        ),
    ],
)
def test_user_auth(
    event_input: str,
    expected_response: dict,
    dynamo_response_dict_or_exception: Union[dict, Exception],
    env_var_dict: dict,
    boto3_resource_mock: Mock,
    boto3_client_mock: Mock,
) -> None:

    aws_resource_mock = boto3_resource_mock.return_value
    aws_dynamo_table = aws_resource_mock.Table.return_value
    aws_dynamo_table.get_item.return_value = dynamo_response_dict_or_exception
    aws_client_mock = boto3_client_mock.return_value
    aws_client_mock.get_secret_value.return_value = {"SecretString": TEST_JWT_SECRETS}

    test_event_input = event_input

    with patch.dict(os.environ, env_var_dict):
        response = user_handler(test_event_input, "")

    assert response == add_cors_to_dict(expected_response)
    if expected_response["statusCode"] == 200:
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
    response = create_user_hash_password(TEST_USER_PASSWORD)
    assert response == b"$2b$12$tBzFe5aHXtLmOPWSQWcy2ekjqxf4R5p9C99oWDxv/EJz7bYHE2Ez2"
