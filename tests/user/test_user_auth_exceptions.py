import pytest
from typing import Any, Dict, Tuple, Type
from personal_finances.user.user_auth_exceptions import (
    get_server_response_by_exception,
    AuthorizationHeaderNotPresent,
    AuthorizationHeaderEmptyContent,
    InvalidAuthorizationHeader,
    InvalidLambdaEventInput,
    UserNotFound,
    PasswordNotMatch,
    InvalidUserPassword,
    InvalidUserName,
    InvalidDynamoResponse,
    InconsistentExceptionDictionary,
)

_TEST_DUPLICATED_EXCEPTION_TO_HTTP_RESPONSE: Dict[Tuple, Dict] = {
    (UserNotFound, PasswordNotMatch): {
        "statusCode": 401,
        "body": '{"message": "User or password incorrect"}',
    },
    (
        AuthorizationHeaderNotPresent,
        UserNotFound,
        InvalidAuthorizationHeader,
    ): {
        "statusCode": 400,
        "body": '{"message": "Invalid authentication input"}',
    },
}

_TEST_EMPTY_EXCEPTION_LIST_RESPONSE: Dict = {
    "statusCode": 500,
    "body": '{"message": "Internal Server Error"}',
}


@pytest.mark.parametrize(
    "exception_type, expected_response",
    [
        (
            UserNotFound,
            {"statusCode": 401, "body": '{"message": "User or password incorrect"}'},
        ),
        (
            PasswordNotMatch,
            {"statusCode": 401, "body": '{"message": "User or password incorrect"}'},
        ),
        (
            AuthorizationHeaderNotPresent,
            {"statusCode": 400, "body": '{"message": "Invalid authentication input"}'},
        ),
        (
            AuthorizationHeaderEmptyContent,
            {"statusCode": 400, "body": '{"message": "Invalid authentication input"}'},
        ),
        (
            InvalidAuthorizationHeader,
            {"statusCode": 400, "body": '{"message": "Invalid authentication input"}'},
        ),
        (
            InvalidUserPassword,
            {
                "statusCode": 400,
                "body": (
                    '{"message": "Username or password does not '
                    + 'match the minimal security requirements"}'
                ),
            },
        ),
        (
            InvalidUserName,
            {
                "statusCode": 400,
                "body": (
                    '{"message": "Username or password does not '
                    + 'match the minimal security requirements"}'
                ),
            },
        ),
        (
            InvalidLambdaEventInput,
            {"statusCode": 500, "body": '{"message": "Internal Server Error"}'},
        ),
        (
            InvalidDynamoResponse,
            {"statusCode": 500, "body": '{"message": "Internal Server Error"}'},
        ),
        (
            KeyError,
            {"statusCode": 500, "body": '{"message": "Internal Server Error"}'},
        ),
        (
            Exception,
            {"statusCode": 500, "body": '{"message": "Internal Server Error"}'},
        ),
    ],
)
def test_get_server_response_by_exception(
    exception_type: Type[Exception], expected_response: dict[str, Any]
) -> None:
    assert expected_response == get_server_response_by_exception(exception_type())


def test_get_server_response_duplicated_exception_list() -> None:
    with pytest.raises(InconsistentExceptionDictionary):
        get_server_response_by_exception(
            UserNotFound(), _TEST_DUPLICATED_EXCEPTION_TO_HTTP_RESPONSE
        )


def test_get_server_response_empty_exception_list_input() -> None:
    assert _TEST_EMPTY_EXCEPTION_LIST_RESPONSE == get_server_response_by_exception(
        UserNotFound(), {}
    )
