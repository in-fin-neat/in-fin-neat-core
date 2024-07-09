import base64
import json
import logging
import boto3
import jwt
import os

LOGGER = logging.getLogger(__name__)


class InvalidInput(Exception):
    def __str__(self) -> str:
        return "InvalidInput"


class AuthHeaderNotFound(Exception):
    def __str__(self) -> str:
        return "AuthHeaderNotFound"


class UserNotFound(Exception):
    def __str__(self) -> str:
        return "UserNotFound"


class EmptyUserID(Exception):
    def __str__(self) -> str:
        return "EmptyUserID"


class TokenNotFound(Exception):
    def __str__(self) -> str:
        return "TokenNotFound"


def _get_token_from_event(event: dict):
    if "authorizationToken" not in event:
        raise(AuthHeaderNotFound)
    
    token = event.get("authorizationToken", None)
    if token is None or token == "":
        raise(TokenNotFound)
    
    return token


def _get_jwt_secret() -> str:
    jwt_session = boto3.client("secretsmanager")

    get_secret_value_response = jwt_session.get_secret_value(
        SecretId=os.environ["INFINEAT_JWT_SECRET_NAME"]
    )

    return str(get_secret_value_response["SecretString"])


def decode_token(token):
    return jwt.decode(
        jwt=token,
        key=_get_jwt_secret(),
        algorithms="HS256",
    )


def _generatePolicy(principalId, effect, resource):
    authResponse = {}
    authResponse["principalId"] = principalId
    if effect and resource:
        policyDocument = {}
        policyDocument["Statement"] = []
        statementOne = {}
        statementOne["Action"] = "execute-api:Invoke"
        statementOne["Effect"] = effect
        statementOne["Resource"] = resource
        policyDocument["Statement"] = [statementOne]
        authResponse["policyDocument"] = policyDocument
    authResponse_JSON = json.dumps(authResponse)
    return authResponse_JSON

def _get_user_from_decoded_token(token:dict) -> str:
    if "userId" not in token:
        raise(UserNotFound)
    
    user_id = token.get("userId", None)
    if user_id is None or user_id == "":
        raise(EmptyUserID)
    
    return user_id

def token_validation(event, context):
    if event is None or event == "":
        raise(InvalidInput)
    
    token = _get_token_from_event(event)
    decoded_token = jwt.decode(jwt=token, key=_get_jwt_secret(), algorithms="HS256", options={"require": ["exp", "userId"]})
    user_id = _get_user_from_decoded_token(decoded_token)
    response = _generatePolicy(user_id, "Allow", event["methodArn"])

    return json.loads(response)
