from typing import Dict, Tuple, Type
import logging

LOGGER = logging.getLogger(__name__)


class AuthorizationHeaderNotPresent(Exception):
    pass


class AuthorizationHeaderEmptyContent(Exception):
    pass


class InvalidAuthorizationHeader(Exception):
    pass


class InvalidLambdaEventInput(Exception):
    pass


class UserNotFound(Exception):
    pass


class PasswordNotMatch(Exception):
    pass


class InvalidUserPassword(Exception):
    pass


class InvalidUserName(Exception):
    pass


class InvalidDynamoResponse(Exception):
    pass


class InconsistentExceptionDictionary(Exception):
    pass


"""
    This dicts contains the map between the exceptions generated in
    the user login api and the http response. No exception should be
    duplicated, otherwise the 'InconsistentExceptionDictionary' exception
    will be raised in the '_get_exception_type_index' function
"""
_EXCEPTION_TO_HTTP_RESPONSE: Dict[Tuple, Dict] = {
    (UserNotFound, PasswordNotMatch): {
        "statusCode": 401,
        "body": "User or password incorrect",
    },
    (
        AuthorizationHeaderNotPresent,
        AuthorizationHeaderEmptyContent,
        InvalidAuthorizationHeader,
    ): {
        "statusCode": 400,
        "body": "Invalid authentication input",
    },
    (
        InvalidUserPassword,
        InvalidUserName,
    ): {
        "statusCode": 400,
        "body": "Username or password does not match the minimal security requirements",
    },
    (
        InvalidLambdaEventInput,
        InvalidDynamoResponse,
        KeyError,
    ): {
        "statusCode": 500,
        "body": "Internal Server Error",
    },
}

_UNKNOWN_EXCEPTION_RESPONSE: Dict = {
    "statusCode": 500,
    "body": "Internal Server Error",
}


def _get_exception_type_index(
    exception_to_http_response: Dict[Tuple, Dict]
) -> Dict[Type[Exception], Dict]:
    exception_type_index: Dict[Type[Exception], Dict] = {}
    for exception_types, http_response in exception_to_http_response.items():
        if any(
            exception_type in exception_type_index for exception_type in exception_types
        ):
            LOGGER.warning(
                f"""overriding response for one
                     or more of the exception type {exception_types}"""
            )
            # There should be tests ensuring this is never reached in a shipped code.
            raise InconsistentExceptionDictionary
        exception_type_index = {
            **exception_type_index,
            **{exception_type: http_response for exception_type in exception_types},
        }
    return exception_type_index


def get_server_response_by_exception(
    exception: Exception,
    exception_list: Dict[Tuple, Dict] = _EXCEPTION_TO_HTTP_RESPONSE,
) -> dict:
    exception_type_index = _get_exception_type_index(exception_list)
    try:
        return exception_type_index[type(exception)]
    except KeyError:
        return _UNKNOWN_EXCEPTION_RESPONSE
