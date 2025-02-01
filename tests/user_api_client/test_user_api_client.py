import base64
from typing import Generator
import pytest
import requests
from unittest.mock import Mock, patch, MagicMock
from personal_finances.user_api_client.user_api_client import (
    UserApiClient,
    ApiClientError,
)

TEST_INVALID_ARGUMENT_MSG = "Arguments cannot be None or an empty string."


@pytest.fixture
def client() -> Generator[UserApiClient, None, None]:
    """
    Returns a UserApiClient instance pointed to a testing URL.
    """
    yield UserApiClient(base_url="https://api.test")


@pytest.fixture
def logged_in_client(client: UserApiClient) -> Generator[UserApiClient, None, None]:
    """
    Returns a UserApiClient that is already logged.
    """
    with patch("requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.json.return_value = {"token": "mocked_token_123"}
        mock_post.return_value = mock_response

        client.login(user_id="fixture_user", password="fixture_pass")
    yield client


@pytest.fixture
def mock_post() -> Generator[Mock, None, None]:
    with patch(
        "personal_finances.user_api_client.user_api_client.requests.post"
    ) as mock_post:
        yield mock_post


@pytest.fixture
def mock_get() -> Generator[Mock, None, None]:
    with patch(
        "personal_finances.user_api_client.user_api_client.requests.get"
    ) as mock_get:
        yield mock_get


@pytest.fixture
def mock_put() -> Generator[Mock, None, None]:
    with patch(
        "personal_finances.user_api_client.user_api_client.requests.put"
    ) as mock_get:
        yield mock_get


# ------------------------------------------------------------------------------
# 1) LOGIN TESTS
# ------------------------------------------------------------------------------


def test_login_success(mock_post: MagicMock, client: UserApiClient) -> None:
    """
    Test that login() succeeds and stores the token internally.
    """
    mock_response = MagicMock()
    mock_response.json.return_value = {"token": "test_token_123"}
    mock_post.return_value = mock_response

    token = client.login(user_id="user123", password="supersecret")
    assert token == "test_token_123"

    creds = "user123:supersecret"
    encoded_creds = base64.b64encode(creds.encode("ascii")).decode("ascii")
    mock_post.assert_called_once_with(
        "https://api.test/users/user123/login",
        headers={"Authorization": f"Basic {encoded_creds}"},
    )


@pytest.mark.parametrize(
    "user_id, password, expected_error_msg",
    [
        ("", "secret", TEST_INVALID_ARGUMENT_MSG),
        (None, "secret", TEST_INVALID_ARGUMENT_MSG),
        ("user123", "", TEST_INVALID_ARGUMENT_MSG),
        ("user123", None, TEST_INVALID_ARGUMENT_MSG),
    ],
)
def test_login_invalid_input(
    client: UserApiClient, user_id: str, password: str, expected_error_msg: str
) -> None:
    """
    Test login() with invalid user_id/password using parametrization.
    """
    with pytest.raises(ValueError) as exc_info:
        client.login(user_id, password)
    assert expected_error_msg in str(exc_info.value)


def test_login_failure_no_token(mock_post: MagicMock, client: UserApiClient) -> None:
    """
    Test that login() raises an error if 'token' field is missing in the response.
    """
    mock_response = MagicMock()
    mock_response.json.return_value = {}  # No 'token' field
    mock_post.return_value = mock_response

    with pytest.raises(KeyError):
        client.login(user_id="user123", password="supersecret")


def test_login_invalid_password(mock_post: MagicMock, client: UserApiClient) -> None:
    """
    Test that login() raises ApiClientError if the API returns an HTTP error.
    """
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
        "401 Unauthorized"
    )
    mock_post.return_value = mock_response

    with pytest.raises(ApiClientError) as exc_info:
        client.login(user_id="user123", password="wrongpassword")

    assert "User API request failed" in str(exc_info.value)


def test_login_request_exception(mock_post: MagicMock, client: UserApiClient) -> None:
    """
    Test that login() raises an ApiClientError if the HTTP request fails.
    """
    mock_post.side_effect = requests.RequestException("Network issue")
    with pytest.raises(ApiClientError) as exc_info:
        client.login(user_id="user123", password="supersecret")

    assert "User API request failed" in str(exc_info.value)


# ------------------------------------------------------------------------------
# 2) GET BANK ACCOUNTS TESTS
# ------------------------------------------------------------------------------


def test_get_bank_accounts_success(
    mock_get: MagicMock, logged_in_client: UserApiClient
) -> None:
    """
    Test that get_bank_accounts() returns a list of IBANs on success.
    """

    mock_response = MagicMock()
    mock_response.json.return_value = {"ibanList": ["IBAN1", "IBAN2"]}
    mock_get.return_value = mock_response

    ibans = logged_in_client.get_bank_accounts("user123")
    mock_get.assert_called_once_with(
        "https://api.test/users/user123/bank-accounts/",
        headers={"Authorization": "Bearer mocked_token_123"},
    )
    assert ibans == ["IBAN1", "IBAN2"]


def test_get_bank_accounts_not_logged_in(client: UserApiClient) -> None:
    """
    Test that get_bank_accounts() raises ApiClientError if no auth token is present.
    """
    with pytest.raises(ApiClientError) as exc_info:
        client.get_bank_accounts("user123")
    assert "Cannot make request before logging in" in str(exc_info.value)


def test_get_bank_accounts_invalid_token(
    mock_get: MagicMock, logged_in_client: UserApiClient
) -> None:
    """
    Test that get_bank_accounts()  raises ApiClientError if the API
    returns an HTTP error (e.g., invalid token).
    """
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
        "401 Unauthorized"
    )
    mock_get.return_value = mock_response

    with pytest.raises(ApiClientError) as exc_info:
        logged_in_client.get_bank_accounts("user123")

    assert "User API request failed" in str(exc_info.value)


@pytest.mark.parametrize(
    "user_id, expected_error_msg",
    [
        ("", TEST_INVALID_ARGUMENT_MSG),
        (None, TEST_INVALID_ARGUMENT_MSG),
    ],
)
def test_get_bank_accounts_invalid_userid(
    logged_in_client: UserApiClient, user_id: str, expected_error_msg: str
) -> None:
    """
    Test get_bank_accounts() with invalid user_id using parametrization.
    """
    with pytest.raises(ValueError) as exc_info:
        logged_in_client.get_bank_accounts(user_id)
    assert expected_error_msg in str(exc_info.value)


# ------------------------------------------------------------------------------
# 3) UPDATE BANK ACCOUNT TESTS
# ------------------------------------------------------------------------------


def test_update_bank_account_success(
    mock_put: MagicMock, logged_in_client: UserApiClient
) -> None:
    """
    Test updating a valid bank account with PUT /users/{userId}/bank-accounts/{iban}.
    """
    mock_response = MagicMock()
    mock_response.json.return_value = {"message": "IBAN added successfully"}
    mock_put.return_value = mock_response

    updated_data = logged_in_client.update_bank_account(
        user_id="user123",
        iban="DE89370400440532013000",
    )

    mock_put.assert_called_once_with(
        "https://api.test/users/user123/bank-accounts/DE89370400440532013000",
        headers={"Authorization": "Bearer mocked_token_123"},
    )
    assert updated_data == mock_response.json.return_value


def test_update_bank_account_not_logged_in(client: UserApiClient) -> None:
    """
    Test that update_bank_account() raises an error if not logged in.
    """
    with pytest.raises(ApiClientError) as exc_info:
        client.update_bank_account("user123", "DE89370400440532013000")
    assert "Cannot make request before logging in" in str(exc_info.value)


@pytest.mark.parametrize(
    "user_id, iban, expected_error_msg",
    [
        ("", "DE89370400440532013000", TEST_INVALID_ARGUMENT_MSG),
        (None, "DE89370400440532013000", TEST_INVALID_ARGUMENT_MSG),
        ("user123", "", TEST_INVALID_ARGUMENT_MSG),
        ("user123", None, TEST_INVALID_ARGUMENT_MSG),
        (
            "user123",
            "THIS_IS_NOT_VALID_IBAN",
            "Invalid characters in IBAN THIS_IS_NOT_VALID_IBAN",
        ),
    ],
)
def test_update_bank_account_invalid_input(
    logged_in_client: UserApiClient, user_id: str, iban: str, expected_error_msg: str
) -> None:
    """
    Test update_bank_account() with invalid user_id/iban using parametrization.
    Ensures ValueError is raised for empty or invalid inputs.
    """
    with pytest.raises(ValueError) as exc_info:
        logged_in_client.update_bank_account(user_id, iban)
    assert expected_error_msg in str(exc_info.value)
