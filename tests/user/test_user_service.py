import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Any, Dict, Generator, Optional

from personal_finances.user.user_service import (
    user_service_handler,
)
from personal_finances.user.user_auth_exceptions import (
    InvalidIban,
    UserNotFound,
)
import os


@pytest.fixture
def env_var_patch() -> Generator[Mock, None, None]:
    environment_variables = {"ALLOWED_ORIGIN_DOMAINS": "https://some-test-domain"}
    with patch.dict(os.environ, environment_variables) as mock:
        yield mock


@pytest.fixture
def mock_user_login() -> Any:
    with patch("personal_finances.user.user_service.user_login") as mock_func:
        yield mock_func


@pytest.fixture
def mock_get_user_ibans() -> Any:
    with patch("personal_finances.user.user_service.get_user_ibans") as mock_func:
        yield mock_func


@pytest.fixture
def mock_update_user_iban() -> Any:
    with patch("personal_finances.user.user_service.update_user_iban") as mock_func:
        yield mock_func


@pytest.mark.parametrize(
    "event, expected_response",
    [
        (
            # No header
            {
                "resource": "/users/{userId}/login",
                "httpMethod": "POST",
            },
            {
                "statusCode": 500,
                "body": "Internal Server Error",
                "headers": {"Access-Control-Allow-Origin": "*"},
            },
        ),
        (
            # No Authorization header
            {"resource": "/users/{userId}/login", "httpMethod": "POST", "headers": {}},
            {
                "statusCode": 400,
                "body": "Invalid authentication input",
                "headers": {"Access-Control-Allow-Origin": "*"},
            },
        ),
        (
            # Empty Authorization header
            {
                "resource": "/users/{userId}/login",
                "httpMethod": "POST",
                "headers": {"Authorization": ""},
            },
            {
                "statusCode": 400,
                "body": "Invalid authentication input",
                "headers": {"Access-Control-Allow-Origin": "*"},
            },
        ),
    ],
)
def test_get_auth_header_exceptions(
    event: Dict[str, Any],
    expected_response: Dict[str, Any],
) -> None:

    response = user_service_handler(event, "")

    assert response["statusCode"] == expected_response["statusCode"]
    assert response["body"] == expected_response["body"]
    assert response["headers"]["Access-Control-Allow-Origin"] == "*"


@pytest.mark.parametrize(
    "event, mock_login_return_value, expected_response",
    [
        (
            # Test case: Successful login
            {
                "resource": "/users/{userId}/login",
                "httpMethod": "POST",
                "headers": {"Authorization": "Bearer testtoken"},
            },
            '{"token": "abc123"}',
            {
                "statusCode": 200,
                "body": '{"token": "abc123"}',
                "headers": {"Access-Control-Allow-Origin": "*"},
            },
        ),
        (
            # Test case: User not found
            {
                "resource": "/users/{userId}/login",
                "httpMethod": "POST",
                "headers": {"Authorization": "Bearer testtoken"},
            },
            UserNotFound(),
            {
                "statusCode": 401,
                "body": "User or password incorrect",
                "headers": {"Access-Control-Allow-Origin": "*"},
            },
        ),
    ],
)
def test_user_service_handler_login(
    event: Dict[str, Any],
    mock_login_return_value: Optional[Any],
    expected_response: Dict[str, Any],
    mock_user_login: MagicMock,
) -> None:

    if not isinstance(mock_login_return_value, Exception):
        mock_user_login.return_value = mock_login_return_value
    else:
        mock_user_login.side_effect = mock_login_return_value

    response = user_service_handler(event, "")

    assert response["statusCode"] == expected_response["statusCode"]
    assert response["body"] == expected_response["body"]
    assert response["headers"]["Access-Control-Allow-Origin"] == "*"

    mock_user_login.assert_called_once_with(event["headers"]["Authorization"])


@pytest.mark.parametrize(
    "event, mock_get_ibans_return_value, expected_response",
    [
        (
            # Test case: Successful retrieval of IBANs
            {
                "resource": "/users/{userId}/bank-accounts",
                "httpMethod": "GET",
                "pathParameters": {"userId": "testuser"},
            },
            ["DE1234567890", "GB0987654321"],
            {
                "statusCode": 200,
                "body": 'ibanList:["DE1234567890", "GB0987654321"]',
                "headers": {"Access-Control-Allow-Origin": "*"},
            },
        ),
        (
            # Test case: UserNotFound exception
            {
                "resource": "/users/{userId}/bank-accounts",
                "httpMethod": "GET",
                "pathParameters": {"userId": "unknownuser"},
            },
            UserNotFound(),
            {
                "statusCode": 401,
                "body": "User or password incorrect",
                "headers": {"Access-Control-Allow-Origin": "*"},
            },
        ),
    ],
)
def test_user_service_handler_get_ibans(
    event: Dict[str, Any],
    mock_get_ibans_return_value: Optional[Any],
    expected_response: Dict[str, Any],
    mock_get_user_ibans: MagicMock,
) -> None:
    if not isinstance(mock_get_ibans_return_value, Exception):
        mock_get_user_ibans.return_value = mock_get_ibans_return_value
    else:
        mock_get_user_ibans.side_effect = mock_get_ibans_return_value

    response = user_service_handler(event, "")

    assert response == expected_response
    mock_get_user_ibans.assert_called_once_with(event["pathParameters"]["userId"])


@pytest.mark.parametrize(
    "event, context, mock_update_side_effect, expected_response",
    [
        (
            # Test case: Successful IBAN update
            {
                "resource": "/users/{userId}/bank-accounts/{iban}",
                "httpMethod": "PUT",
                "pathParameters": {"userId": "testuser", "iban": "DE1234567890"},
            },
            "",
            None,
            {
                "statusCode": 200,
                "body": "IBAN added successfully",
                "headers": {"Access-Control-Allow-Origin": "*"},
            },
        ),
        (
            # Test case: Invalid IBAN exception
            {
                "resource": "/users/{userId}/bank-accounts/{iban}",
                "httpMethod": "PUT",
                "pathParameters": {"userId": "testuser", "iban": "INVALID_IBAN"},
            },
            "",
            InvalidIban(),
            {
                "statusCode": 400,
                "body": "Invalid IBAN format",
                "headers": {"Access-Control-Allow-Origin": "*"},
            },
        ),
    ],
)
def test_user_service_handler_update_iban(
    event: Dict[str, Any],
    context: str,
    mock_update_side_effect: Optional[Exception],
    expected_response: Dict[str, Any],
    mock_update_user_iban: MagicMock,
) -> None:
    if mock_update_side_effect:
        mock_update_user_iban.side_effect = mock_update_side_effect

    response = user_service_handler(event, context)

    assert response == expected_response
    mock_update_user_iban.assert_called_once_with(
        event["pathParameters"]["userId"], event["pathParameters"]["iban"]
    )


@pytest.mark.parametrize(
    "event, expected_response",
    [
        (
            # Test case: Unknown resource
            {
                "resource": "/unknown/resource",
                "httpMethod": "GET",
            },
            {
                "statusCode": 404,
                "body": "Not Found",
                "headers": {"Access-Control-Allow-Origin": "https://some-test-domain"},
            },
        ),
        (
            # Test case: Invalid http method
            {
                "resource": "/users/{userId}/login",
                "httpMethod": "GET",
            },
            {
                "statusCode": 404,
                "body": "Not Found",
                "headers": {"Access-Control-Allow-Origin": "https://some-test-domain"},
            },
        ),
        (
            # Test case: Invalid http method
            {
                "resource": "/users/{userId}/login",
                "httpMethod": "PUT",
            },
            {
                "statusCode": 404,
                "body": "Not Found",
                "headers": {"Access-Control-Allow-Origin": "https://some-test-domain"},
            },
        ),
        (
            # Test case: Invalid http method
            {
                "resource": "/users/{userId}/bank-accounts/{iban}",
                "httpMethod": "GET",
            },
            {
                "statusCode": 404,
                "body": "Not Found",
                "headers": {"Access-Control-Allow-Origin": "https://some-test-domain"},
            },
        ),
        (
            # Test case: Invalid http method
            {
                "resource": "/users/{userId}/bank-accounts",
                "httpMethod": "POST",
            },
            {
                "statusCode": 404,
                "body": "Not Found",
                "headers": {"Access-Control-Allow-Origin": "https://some-test-domain"},
            },
        ),
        (
            # Test case: Invalid http method
            {
                "resource": "/users/{userId}/bank-accounts",
                "httpMethod": "PUT",
            },
            {
                "statusCode": 404,
                "body": "Not Found",
                "headers": {"Access-Control-Allow-Origin": "https://some-test-domain"},
            },
        ),
        (
            # Test case: Invalid http method
            {
                "resource": "/users/{userId}/bank-accounts/{iban}",
                "httpMethod": "POST",
            },
            {
                "statusCode": 404,
                "body": "Not Found",
                "headers": {"Access-Control-Allow-Origin": "https://some-test-domain"},
            },
        ),
        (
            # Test case: Invalid http method
            {
                "resource": "/users/{userId}/bank-accounts/{iban}",
                "httpMethod": "GET",
            },
            {
                "statusCode": 404,
                "body": "Not Found",
                "headers": {"Access-Control-Allow-Origin": "https://some-test-domain"},
            },
        ),
    ],
)
def test_user_service_handler_not_found(
    env_var_patch: Mock,
    event: Dict[str, Any],
    expected_response: Dict[str, Any],
) -> None:
    response = user_service_handler(event, "")
    assert response == expected_response
