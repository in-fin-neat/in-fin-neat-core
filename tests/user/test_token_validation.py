from datetime import datetime, timedelta, timezone
import os
import jwt
import pytest
from unittest.mock import Mock, patch
from typing import Generator, Type, Union
from personal_finances.user.token_validation import (
    token_validation,
    InvalidLambdaEventInput,
    AuthHeaderNotFound,
    EmptyUserID,
    AuthorizationHeaderEmptyContent,
)


TEST_USER_ID = "testuser"
TEST_USER_PASSWORD = "123"
TEST_JWT_SECRET = "jwt_secret"
TEST_ENVAR_DICT = {
    "INFINEAT_JWT_SECRET_NAME": TEST_JWT_SECRET,
}

TEST_RESULT_OK = {
    "policyDocument": {
        "Statement": [
            {
                "Action": "execute-api:Invoke",
                "Effect": "Allow",
                "Resource": "arn:httpVerb/[resource/[child-resources]]",
            }
        ]
    },
    "principalId": TEST_USER_ID,
}


def _get_input_without_auth_token() -> dict:
    return {
        "type": "TOKEN",
        "methodArn": "arn:httpVerb/[resource/[child-resources]]",
    }


def _get_input_event(token: str) -> dict:
    response = _get_input_without_auth_token()
    response["authorizationToken"] = token
    return response


@pytest.fixture(autouse=True)
def boto3_mock() -> Generator[Mock, None, None]:
    with patch("personal_finances.user.token_validation.boto3.client") as mock:
        yield mock


def _gen_jwt_without_name(exp_date: datetime, secret: str) -> str:
    return jwt.encode(
        {"exp": exp_date},
        secret,
        algorithm="HS256",
    )


def _gen_jwt_without_exp_date(user_id: str, secret: str) -> str:
    return jwt.encode(
        {"userId": user_id},
        secret,
        algorithm="HS256",
    )


def _generate_jwt_token(
    exp_date: Union[datetime, str], secret: str, user_id: str
) -> str:
    return jwt.encode(
        {"exp": exp_date, "userId": user_id},
        secret,
        algorithm="HS256",
    )


@pytest.mark.parametrize(
    "environment_variables, request_input, expected_exception_r",
    [
        (TEST_ENVAR_DICT, {}, InvalidLambdaEventInput),
        (TEST_ENVAR_DICT, None, InvalidLambdaEventInput),
        (TEST_ENVAR_DICT, _get_input_without_auth_token(), AuthHeaderNotFound),
        (TEST_ENVAR_DICT, _get_input_event(token=""), AuthorizationHeaderEmptyContent),
        (
            TEST_ENVAR_DICT,
            _get_input_event("invalid_token"),
            jwt.exceptions.DecodeError,
        ),
        (
            TEST_ENVAR_DICT,
            _get_input_event(
                _gen_jwt_without_exp_date(secret=TEST_JWT_SECRET, user_id=TEST_USER_ID)
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
            {},
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
def test_token_validation_errors(
    environment_variables: dict,
    request_input: dict,
    expected_exception_r: Type[Exception],
    boto3_mock: Mock,
) -> None:

    aws_client_mock = boto3_mock.return_value
    aws_client_mock.get_secret_value.return_value = {"SecretString": TEST_JWT_SECRET}

    with pytest.raises(expected_exception_r), patch.dict(
        os.environ, environment_variables
    ):
        token_validation(request_input, "")


@pytest.mark.parametrize(
    "environment_variables, request_input, expected_result",
    [
        (
            TEST_ENVAR_DICT,
            _get_input_event(
                _generate_jwt_token(
                    exp_date=datetime.now(timezone.utc) + timedelta(hours=1),
                    secret=TEST_JWT_SECRET,
                    user_id=TEST_USER_ID,
                )
            ),
            TEST_RESULT_OK,
        ),
    ],
)
def test_token_validation(
    environment_variables: dict,
    request_input: dict,
    expected_result: dict,
    boto3_mock: Mock,
) -> None:

    aws_client_mock = boto3_mock.return_value
    aws_client_mock.get_secret_value.return_value = {"SecretString": TEST_JWT_SECRET}

    with patch.dict(os.environ, environment_variables):
        result = token_validation(request_input, "")

    assert expected_result == result
