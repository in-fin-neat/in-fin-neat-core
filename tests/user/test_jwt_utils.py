import os
from typing import Generator
from unittest.mock import Mock, patch
import pytest
from personal_finances.user.jwt_utils import generate_token, decode_token

TEST_JWT_SECRET = "jwt_secret"
TEST_ENVAR_DICT = {
    "INFINEAT_JWT_SECRET_NAME": TEST_JWT_SECRET,
}


@pytest.fixture(autouse=True)
def boto3_mock() -> Generator[Mock, None, None]:
    with patch("personal_finances.user.jwt_utils.boto3.client") as mock:
        yield mock


def test_cache_get_secrets(boto3_mock: Mock) -> None:
    aws_client_mock = boto3_mock.return_value
    aws_client_mock.get_secret_value.return_value = {"SecretString": TEST_JWT_SECRET}

    with patch.dict(os.environ, TEST_ENVAR_DICT):
        token = generate_token("user")
        decode_token(token)

    aws_client_mock.get_secret_value.assert_called_once()
