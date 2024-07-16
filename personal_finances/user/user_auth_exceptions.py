from typing import List


class AuthorizationHeaderNotPresent(Exception):
    def __str__(self) -> str:
        return "AuthorizationHeaderNotPresent"


class AuthorizationHeaderEmptyContent(Exception):
    def __str__(self) -> str:
        return "AuthorizationHeaderEmptyContent"


class InvalidAuthorizationHeader(Exception):
    def __str__(self) -> str:
        return "InvalidAuthorizationHeader"


class InvalidLambdaEventInput(Exception):
    def __str__(self) -> str:
        return "InvalidLambdaEventInput"


class UserNotFound(Exception):
    def __str__(self) -> str:
        return "UserNotFoundException"


class PasswordNotMatch(Exception):
    def __str__(self) -> str:
        return "PasswordNotMatch"


class InvalidUserPassword(Exception):
    def __str__(self) -> str:
        return "InvalidUserPassword"


class InvalidUserName(Exception):
    def __str__(self) -> str:
        return "InvalidUserName"


class ServerSecretNotFound(Exception):
    def __str__(self) -> str:
        return "InvalidUserName"


class InvalidDynamoResponse(Exception):
    def __str__(self) -> str:
        return "InvalidUserName"


_EXPCEPTION_TO_HTTP_RESPONSE_DICT: List[dict] = [
    {
        "statusCode": 401,
        "body": "User or password incorrect",
        "exceptions": [
            UserNotFound,
            PasswordNotMatch,
        ],
    },
    {
        "statusCode": 400,
        "body": "Invalid authentication input",
        "exceptions": [
            AuthorizationHeaderNotPresent,
            AuthorizationHeaderEmptyContent,
            InvalidAuthorizationHeader,
        ],
    },
    {
        "statusCode": 400,
        "body": "Username or password does not match the minimal security requirements",
        "exceptions": [
            InvalidUserPassword,
            InvalidUserName,
        ],
    },
    {
        "statusCode": 500,
        "body": "Internal Server Error",
        "exceptions": [
            InvalidLambdaEventInput,
            ServerSecretNotFound,
            InvalidDynamoResponse,
        ],
    },
]


def get_server_response_by_exception(exception: Exception) -> dict:
    for http_response in _EXPCEPTION_TO_HTTP_RESPONSE_DICT:
        exception_list = http_response["exceptions"]
        if type(exception) in exception_list:
            return {
                "statusCode": http_response["statusCode"],
                "body": http_response["body"],
            }
    return {}
