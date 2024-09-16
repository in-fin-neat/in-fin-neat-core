from datetime import datetime, timedelta
from functools import cache
import os
from typing import Any
import boto3
import jwt

import logging

LOGGER = logging.getLogger()


@cache
def _get_jwt_secret() -> str:
    secret_name = os.environ["INFINEAT_JWT_SECRET_NAME"]
    jwt_session = boto3.client("secretsmanager")
    get_secret_value_response = jwt_session.get_secret_value(SecretId=secret_name)
    LOGGER.debug(f"Secret {secret_name} got from SecretManager with success")
    return str(get_secret_value_response["SecretString"])


def generate_token(user_id: str) -> str:
    return jwt.encode(
        {"exp": datetime.now() + timedelta(hours=1), "userId": user_id},
        _get_jwt_secret(),
        algorithm="HS256",
    )


def decode_token(token: str) -> Any:
    return jwt.decode(
        jwt=token,
        key=_get_jwt_secret(),
        algorithms=["HS256"],
        options={"require": ["exp", "userId"]},
    )
