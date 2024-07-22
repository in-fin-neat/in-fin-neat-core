import json
import logging
from typing import Any
import boto3
import jwt
import os

LOGGER = logging.getLogger(__name__)


class InvalidLambdaEventInput(Exception):
    pass


class AuthHeaderNotFound(Exception):
    pass


class EmptyUserID(Exception):
    pass


class AuthorizationHeaderEmptyContent(Exception):
    pass


def _get_token_from_event(event: dict) -> Any:
    if "authorizationToken" not in event:
        raise (AuthHeaderNotFound)

    token = event.get("authorizationToken", None)
    if token is None or token == "":
        raise (AuthorizationHeaderEmptyContent)

    return token


def _get_jwt_secret() -> str:
    secret_id = os.environ["INFINEAT_JWT_SECRET_NAME"]

    jwt_session = boto3.client("secretsmanager")
    get_secret_value_response = jwt_session.get_secret_value(SecretId=secret_id)

    return str(get_secret_value_response["SecretString"])


def _generatePolicy(principalId: str, effect: str, resource: str) -> str:
    authResponse: dict = {}
    authResponse["principalId"] = principalId
    if effect and resource:
        policyDocument: dict = {}
        policyDocument["Statement"] = []
        statementOne = {}
        statementOne["Action"] = "execute-api:Invoke"
        statementOne["Effect"] = effect
        statementOne["Resource"] = resource
        policyDocument["Statement"] = [statementOne]
        authResponse["policyDocument"] = policyDocument
    authResponse_JSON = json.dumps(authResponse)
    return authResponse_JSON


def _get_user_from_decoded_token(token: dict) -> str:
    user_id: str = token["userId"]
    if user_id == "":
        raise (EmptyUserID)

    return user_id


def _decode_token(token: str) -> Any:
    return jwt.decode(
        jwt=token,
        key=_get_jwt_secret(),
        algorithms=["HS256"],
        options={"require": ["exp", "userId"]},
    )


def token_validation(event: dict, context: str) -> Any:
    if event is None or event == {}:
        raise (InvalidLambdaEventInput)

    token = _get_token_from_event(event)
    logging.info("New token validation check request")
    decoded_token = _decode_token(token)
    user_id = _get_user_from_decoded_token(decoded_token)
    logging.info(f"{user_id} token is still valid")
    response = _generatePolicy(user_id, "Allow", event["methodArn"])

    return json.loads(response)
