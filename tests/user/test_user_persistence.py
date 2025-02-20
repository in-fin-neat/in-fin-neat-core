from typing import Generator, List
import pytest
from unittest.mock import Mock, patch, MagicMock
from schwifty.exceptions import SchwiftyException
from personal_finances.user.user_persistence import (
    get_user_password,
    get_user_ibans,
    update_user_iban,
    _get_user_table,
)

from personal_finances.user.user_auth_exceptions import (
    UserNotFound,
    InvalidIban,
    InvalidDynamoResponse,
)


@pytest.fixture(autouse=True)
def set_env_variables(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("INFINEAT_DYNAMODB_USER_TABLE_NAME", "mock_table_name")


@pytest.fixture(autouse=True, scope="function")
def mock_dynamodb_table() -> Generator[Mock, None, None]:
    with patch(
        "personal_finances.user.user_persistence.boto3.resource"
    ) as mock_resource:
        _get_user_table.cache_clear()
        mock_table = MagicMock()
        mock_resource.return_value.Table.return_value = mock_table
        yield mock_table


@pytest.fixture
def mock_iban() -> Generator[Mock, None, None]:
    with patch("personal_finances.user.user_persistence.IBAN") as mock_iban_class:
        yield mock_iban_class


@pytest.mark.parametrize(
    "userId, get_item_response, expected_result, expected_exception",
    [
        # Successful retrieval
        (
            "testuser",
            {
                "Item": {
                    "userId": "testuser",
                    "password": "securepassword",
                    "ibanList": [],
                }
            },
            "securepassword",
            None,
        ),
        # User not found
        (
            "unknownuser",
            {},
            None,
            UserNotFound,
        ),
        # Invalid DynamoDB response (missing 'password')
        (
            "testuser",
            {"Item": {"userId": "testuser", "ibanList": []}},
            None,
            InvalidDynamoResponse,
        ),
        # Invalid DynamoDB response (incorrect data types)
        (
            "testuser",
            {
                "Item": {"userId": "testuser", "password": 123, "ibanList": []}
            },  # password should be str
            None,
            InvalidDynamoResponse,
        ),
        # Invalid DynamoDB response (missing 'ibanList')
        (
            "testuser",
            {"Item": {"userId": "testuser", "password": "securepassword"}},
            None,
            InvalidDynamoResponse,
        ),
    ],
)
def test_get_user_password(
    userId: str,
    get_item_response: str,
    expected_result: str,
    expected_exception: type[Exception],
    mock_dynamodb_table: Mock,
) -> None:
    mock_dynamodb_table.get_item.return_value = get_item_response

    if expected_exception:
        with pytest.raises(expected_exception):
            get_user_password(userId)
    else:
        result = get_user_password(userId)
        assert result == expected_result

    mock_dynamodb_table.get_item.assert_called_with(Key={"userId": userId})


@pytest.mark.parametrize(
    "userId, get_item_response, expected_result, expected_exception",
    [
        # User with IBANs
        (
            "testuser",
            {
                "Item": {
                    "userId": "testuser",
                    "password": "password",
                    "ibanList": ["DE89370400440532013000", "GB82WEST12345698765432"],
                }
            },
            ["DE89370400440532013000", "GB82WEST12345698765432"],
            None,
        ),
        # User with no IBANs
        (
            "user_with_no_ibans",
            {
                "Item": {
                    "userId": "user_with_no_ibans",
                    "password": "password",
                    "ibanList": [],
                }
            },
            [],
            None,
        ),
        # User not found
        (
            "testuser",
            {},
            None,
            UserNotFound,
        ),
        # Invalid DynamoDB response (missing 'password')
        (
            "testuser",
            {"Item": {"userId": "testuser", "ibanList": ["DE89370400440532013000"]}},
            None,
            InvalidDynamoResponse,
        ),
        # Invalid DynamoDB response (missing 'ibanList')
        (
            "testuser",
            {"Item": {"userId": "testuser", "password": "password"}},
            None,
            InvalidDynamoResponse,
        ),
    ],
)
def test_get_user_ibans(
    userId: str,
    get_item_response: str,
    expected_result: List[str],
    expected_exception: type[Exception],
    mock_dynamodb_table: Mock,
) -> None:
    if isinstance(get_item_response, Exception):
        mock_dynamodb_table.get_item.side_effect = get_item_response
    else:
        mock_dynamodb_table.get_item.return_value = get_item_response

    if expected_exception:
        with pytest.raises(expected_exception):
            get_user_ibans(userId)
    else:
        result = get_user_ibans(userId)
        assert result == expected_result

    mock_dynamodb_table.get_item.assert_called_with(Key={"userId": userId})


@pytest.mark.parametrize(
    "userId, newIban, get_item_response, expected_exception, iban_validation_exception",
    [
        # IBAN already exists
        (
            "testuser",
            "DE89370400440532013000",
            {
                "Item": {
                    "userId": "testuser",
                    "password": "password",
                    "ibanList": ["DE89370400440532013000", "GB82WEST12345698765432"],
                }
            },
            None,
            None,
        ),
        # User not found
        (
            "unknownuser",
            "DE89370400440532013000",
            {},
            UserNotFound,
            None,
        ),
        # Invalid DynamoDB response (missing 'password')
        (
            "testuser",
            "DE89370400440532013000",
            {"Item": {"userId": "testuser", "ibanList": ["GB82WEST12345698765432"]}},
            InvalidDynamoResponse,
            None,
        ),
        # Invalid DynamoDB response (missing 'ibanList')
        (
            "testuser",
            "DE89370400440532013000",
            {"Item": {"userId": "testuser", "password": "password"}},
            InvalidDynamoResponse,
            None,
        ),
        # invalid IBAN
        (
            "testuser",
            "INVALID_IBAN",
            {
                "Item": {
                    "userId": "testuser",
                    "password": "password",
                    "ibanList": ["DE89370400440532013000", "GB82WEST12345698765432"],
                }
            },
            InvalidIban,
            SchwiftyException,
        ),
    ],
)
def test_update_user_iban_edge_cases(
    userId: str,
    newIban: str,
    get_item_response: str,
    expected_exception: type[Exception],
    iban_validation_exception: type[SchwiftyException],
    mock_dynamodb_table: Mock,
    mock_iban: Mock,
) -> None:

    mock_dynamodb_table.get_item.return_value = get_item_response

    if iban_validation_exception is not None:
        mock_iban.side_effect = iban_validation_exception
    else:
        mock_iban.return_value = iban_validation_exception

    if expected_exception:
        with pytest.raises(expected_exception):
            update_user_iban(userId, newIban)
    else:
        update_user_iban(userId, newIban)

    mock_dynamodb_table.update_item.assert_not_called()


def test_sucessfull_iban_adding(mock_dynamodb_table: Mock) -> None:

    get_item_response = {
        "Item": {
            "userId": "testuser",
            "password": "password",
            "ibanList": ["GB82WEST12345698765432"],
        }
    }
    mock_dynamodb_table.get_item.return_value = get_item_response
    userId = "testuser"
    newIban = "DE89370400440532013000"

    update_user_iban(userId, newIban)

    expected_ibans = list(get_item_response["Item"].get("ibanList", [])) + [newIban]
    mock_dynamodb_table.update_item.assert_called_with(
        Key={"userId": userId},
        UpdateExpression="SET ibanList = :updated_list",
        ExpressionAttributeValues={":updated_list": expected_ibans},
        ReturnValues="UPDATED_NEW",
    )
