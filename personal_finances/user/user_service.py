import json
import logging
import os
from typing import Any, Callable
from decorator import decorator
from personal_finances.user.user_login import user_login
from personal_finances.user.user_auth_exceptions import (
    InvalidLambdaEventInput,
    AuthorizationHeaderNotPresent,
    AuthorizationHeaderEmptyContent,
    get_server_response_by_exception,
)
from personal_finances.user.user_persistence import get_user_ibans, update_user_iban

LOGGER = logging.getLogger(__name__)


def _get_auth_header(event: dict) -> str:
    headers = event.get("headers", None)
    if headers is None:
        raise InvalidLambdaEventInput()

    auth_header = headers.get("Authorization", None)
    if auth_header is None:
        raise AuthorizationHeaderNotPresent()

    if auth_header == "":
        raise AuthorizationHeaderEmptyContent()

    return str(auth_header)


def get_allowed_domain() -> str:
    # TODO: allow for multiple origins
    # fetching only the first origin
    try:
        allowed_domain = os.environ["ALLOWED_ORIGIN_DOMAINS"].split(",")[0]
    except Exception as e:
        LOGGER.info(f"falling 'ALLOWED_ORIGIN_DOMAINS' back to * due to: {e}")
        return "*"
    return allowed_domain if allowed_domain else "*"


def add_cors_to_dict(input_dict: dict) -> dict:
    return {
        **input_dict,
        "headers": {"Access-Control-Allow-Origin": get_allowed_domain()},
    }


@decorator
def add_cors_decorator(handler: Callable, *args: Any, **kwargs: Any) -> dict:
    return add_cors_to_dict(handler(*args, **kwargs))


@add_cors_decorator
def user_service_handler(event: dict, context: str) -> dict:
    resource = event["resource"]
    http_method = event["httpMethod"]
    response = {}
    logging.info(f"info_event:{event}")
    logging.info(f"info_context:{context}")

    try:
        if resource == "/users/{userId}/login" and http_method == "POST":
            auth_header = _get_auth_header(event)
            token_json = user_login(auth_header)
            response["token"] = token_json
            return {"statusCode": 200, "body": f"{json.dumps(response)}"}

        elif resource == "/users/{userId}/bank-accounts" and http_method == "GET":
            user_id = event["pathParameters"].get("userId")
            iban_list = get_user_ibans(user_id)
            response_iban = {}
            response_iban["ibanList"] = iban_list
            return {"statusCode": 200, "body": f"{json.dumps(response_iban)}"}

        elif (
            resource == "/users/{userId}/bank-accounts/{iban}" and http_method == "PUT"
        ):
            iban = event["pathParameters"].get("iban")
            user_id = event["pathParameters"].get("userId")
            update_user_iban(user_id, iban)
            response["message"] = "IBAN added successfully"
            return {"statusCode": 200, "body": f"{json.dumps(response)}"}

        # Default response for unknown paths/methods
        response["message"] = "Not Found"
        return {"statusCode": 404, "body": f"{json.dumps(response)}"}

    except Exception as e:
        LOGGER.exception(
            f"""
            An error at the user authentication lambda has happened {e}
            """
        )
        fail_response = get_server_response_by_exception(e)
        return fail_response
