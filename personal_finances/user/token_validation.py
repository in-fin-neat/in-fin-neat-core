import json
import logging
from typing import Any

import jwt
from personal_finances.user.jwt_utils import decode_token

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

    token = event["authorizationToken"]
    if token == "":
        raise (AuthorizationHeaderEmptyContent)

    return str(token).replace("Bearer ", "")


def _generate_policy(principalId: str, effect: str, resource: str) -> str:
    return json.dumps(
        {
            "principalId": principalId,
            "policyDocument": {
                "Statement": [
                    {
                        "Action": "execute-api:Invoke",
                        "Effect": effect,
                        "Resource": resource,
                    }
                ]
            },
        }
    )


def _get_user_from_decoded_token(token: dict) -> str:
    user_id: str = token["userId"]
    if user_id == "":
        raise (EmptyUserID)

    return user_id


def token_validation(event: dict, context: str) -> Any:
    if event is None or event == {}:
        raise (InvalidLambdaEventInput)

    try:
        token = _get_token_from_event(event)
        logging.info("New token validation check request")
        logging.debug(f"Event input keys: {event.keys()}")
        decoded_token = decode_token(token)
        user_id = _get_user_from_decoded_token(decoded_token)
        logging.info(f"{user_id} token is still valid")
        response = _generate_policy(user_id, "Allow", event["methodArn"])
        return json.loads(response)
    except (
        AuthHeaderNotFound,
        AuthorizationHeaderEmptyContent,
        EmptyUserID,
        jwt.exceptions.InvalidTokenError,
    ) as e:
        logging.info(f"Invalid token:{str(e)}")
        raise Exception("Unauthorized")  # Return a 401 Unauthorized response
