import base64
from datetime import datetime, timedelta, timezone
import json
import jwt
import pytest
from unittest.mock import Mock, patch
from typing import Generator, Union
from personal_finances.user.token_validation import (
    token_validation,
    InvalidInput,
    AuthHeaderNotFound,
    UserNotFound,
    EmptyUserID,
    TokenNotFound,
)


TEST_USER_ID = "testuser"
TEST_USER_PASSWORD = "123"
TEST_JWT_SECRET = "jwt_secret"
TEST_ENVAR_DICT = {
    "INFINEAT_JWT_SECRET_NAME": "jwt_secret",
}


def _get_input_without_auth_token() -> dict:
    return {
        "type": "TOKEN",
        "methodArn": "arn:aws:execute-api:regionId:accountId:apiId/stage/httpVerb/[resource/[child-resources]]",
    }


def _get_input_event(token: str):
    response = _get_input_without_auth_token()
    response["authorizationToken"] = token
    return response


def _encode_basic_auth(user: str, password: str) -> str:
    credentials = f"{user}:{password}"
    credentials_encoded = credentials.encode()
    authorization_encoded = base64.b64encode(credentials_encoded)
    authorization = f"Basic {authorization_encoded.decode()}"
    return authorization


@pytest.fixture(autouse=True)
def os_mock() -> Generator[Mock, None, None]:
    with patch("personal_finances.user.token_validation.os") as mock:
        yield mock


@pytest.fixture(autouse=True)
def boto3_mock() -> Generator[Mock, None, None]:
    with patch("personal_finances.user.token_validation.boto3.client") as mock:
        yield mock


def _generate_jwt_token(exp_date: datetime, secret: str, user_name: str) -> str:
    return jwt.encode(
        {"exp": exp_date, "userId": user_name},
        secret,
        algorithm="HS256",
    )


def _gen_jwt_without_name(exp_date: datetime, secret: str):
    return jwt.encode(
        {"exp": exp_date},
        secret,
        algorithm="HS256",
    )


def _gen_jwt_without_exp_date(user_name: str, secret: str):
    return jwt.encode(
        {"userId": user_name},
        secret,
        algorithm="HS256",
    )


def _generate_jwt_token(exp_date: datetime, secret: str, user_id: str) -> str:
    return jwt.encode(
        {"exp": exp_date, "userId": user_id},
        secret,
        algorithm="HS256",
    )


@pytest.mark.parametrize(
    "environment_variables, request_input, expected_exception",
    [
        (TEST_ENVAR_DICT, "", InvalidInput),
        (TEST_ENVAR_DICT, None, InvalidInput),
        (TEST_ENVAR_DICT, _get_input_without_auth_token(), AuthHeaderNotFound),
        (TEST_ENVAR_DICT, _get_input_event(token=""), TokenNotFound),
        (
            TEST_ENVAR_DICT,
            _get_input_event("invalid_token"),
            jwt.exceptions.DecodeError,
        ),
        (
            TEST_ENVAR_DICT,
            _get_input_event(
                _gen_jwt_without_exp_date(
                    secret=TEST_JWT_SECRET, user_name=TEST_USER_ID
                )
            ),
            jwt.exceptions.MissingRequiredClaimError,
        ),
        (
            TEST_ENVAR_DICT,
            _get_input_event(
                _gen_jwt_without_name(exp_date=datetime.now(), secret=TEST_JWT_SECRET)
            ),
            jwt.exceptions.MissingRequiredClaimError,
        ),
        (
            TEST_ENVAR_DICT,
            _get_input_event(
                _generate_jwt_token(
                    exp_date="", secret=TEST_JWT_SECRET, user_id=TEST_USER_ID
                )
            ),
            jwt.exceptions.DecodeError,
        ),
        (
            TEST_ENVAR_DICT,
            _get_input_event(
                _generate_jwt_token(
                    exp_date=datetime.now(), secret=TEST_JWT_SECRET, user_id=""
                )
            ),
            EmptyUserID,
        ),
        (
            TEST_ENVAR_DICT,
            _get_input_event(
                _generate_jwt_token(
                    exp_date=datetime.now(),
                    secret="invalid_secret",
                    user_id=TEST_USER_ID,
                )
            ),
            jwt.exceptions.InvalidSignatureError,
        ),
        (
            TEST_ENVAR_DICT,
            _get_input_event(
                _generate_jwt_token(
                    exp_date=datetime.now(timezone.utc) - timedelta(seconds=1),
                    secret=TEST_JWT_SECRET,
                    user_id=TEST_USER_ID,
                )
            ),
            jwt.exceptions.ExpiredSignatureError,
        ),
        (
            KeyError,
            _get_input_event(
                _generate_jwt_token(
                    exp_date=datetime.now(),
                    secret=TEST_JWT_SECRET,
                    user_id=TEST_USER_ID,
                )
            ),
            KeyError,
        ),
    ],
)
def test_token_validation_erros(
    environment_variables: Union[dict, Exception],
    request_input: str,
    expected_exception: Exception,
    os_mock: Mock,
    boto3_mock: Mock,
) -> None:
    if isinstance(environment_variables, dict):
        os_mock.environ.__getitem__.side_effect = environment_variables.get
    else:
        os_mock.environ.__getitem__.side_effect = environment_variables

    aws_client_mock = boto3_mock.return_value
    aws_client_mock.get_secret_value.return_value = {"SecretString": TEST_JWT_SECRET}

    with pytest.raises(expected_exception=expected_exception):
        token_validation(request_input, "")
