from unittest.mock import patch, Mock
from pytest import fixture, raises
from typing import Generator, Optional, cast
from pydantic import ValidationError
import personal_finances.bank_interface.token_store as ts


class MockTokenStore(ts.TokenStore):
    def __init__(self, test_mock: Mock):
        self.test_mock = test_mock

    def save_token(
        self, user_id: str, token: ts.TokenObject
    ) -> Optional[ts.TokenObject]:
        return cast(Optional[ts.TokenObject], self.test_mock.save_token(user_id, token))

    def get_last_token(self, user_id: str) -> ts.TokenObject:
        return cast(ts.TokenObject, self.test_mock.get_last_token(user_id))


@fixture(autouse=True)
def datetime_mock() -> Generator[Mock, None, None]:
    with patch("personal_finances.bank_interface.token_store.datetime") as mock:
        mock.now.return_value.timestamp.return_value = 123123
        yield mock


def test_token_adapter_raises_missing_keys() -> None:
    with raises(KeyError):
        ts.gocardless_token_adapter(
            {
                "access": "fake-access",
                "access_expires": 10,
                "refresh": "fake-refresh",
                # Missing refresh_expires
                # "refresh_expires": 10,
            }
        )


def test_token_adapter_raises_wrong_type() -> None:
    with raises(ValidationError):
        ts.gocardless_token_adapter(
            {
                "access": "fake-access",
                "access_expires": 10,
                "refresh": "fake-refresh",
                "refresh_expires": "wrong-type-here",
            }
        )


def test_token_adapter_ignores_extra_keys() -> None:
    token_object = ts.gocardless_token_adapter(
        {
            "access": "fake-access",
            "access_expires": 10,
            "refresh": "fake-refresh",
            "refresh_expires": 50,
            "should-ignore-this-key": "also-this vlaue",
        }
    )
    assert token_object.AccessToken == "fake-access"
    assert token_object.AccessExpires == 10
    assert token_object.RefreshToken == "fake-refresh"
    assert token_object.RefreshExpires == 50
    assert token_object.CreationEpoch == 123123


def test_token_store_valid_access_token() -> None:
    last_token = ts.TokenObject(
        AccessToken="fake-access-token",
        AccessExpires=10,
        AccessRefreshEpoch=123122,
        RefreshToken="fake-refresh-token",
        RefreshExpires=50,
        # making AccessExpires + CreationEpoch bigger than mocked now (123123)
        CreationEpoch=123123 - 10 + 1,
    )

    token_store_mock = Mock()
    token_store_mock.get_last_token.return_value = last_token
    test_store = MockTokenStore(token_store_mock)
    assert test_store.is_access_token_valid("my-user-id") is True
    token_store_mock.get_last_token.assert_called_once_with("my-user-id")


def test_token_store_expired_access_token() -> None:
    last_token = ts.TokenObject(
        AccessToken="fake-access-token",
        AccessExpires=10,
        # making AccessExpires + AccessRefreshEpoch equal than mocked now (123123)
        AccessRefreshEpoch=123122 - 10,
        RefreshToken="fake-refresh-token",
        RefreshExpires=50,
        CreationEpoch=123123,
    )

    token_store_mock = Mock()
    token_store_mock.get_last_token.return_value = last_token
    test_store = MockTokenStore(token_store_mock)
    assert test_store.is_access_token_valid("my-user-id") is False
    token_store_mock.get_last_token.assert_called_once_with("my-user-id")


def test_token_store_not_found_access_token() -> None:
    token_store_mock = Mock()
    token_store_mock.get_last_token.side_effect = ts.TokenNotFound
    test_store = MockTokenStore(token_store_mock)
    assert test_store.is_access_token_valid("my-user-id") is False
    token_store_mock.get_last_token.assert_called_once_with("my-user-id")


def test_token_store_valid_refresh_token() -> None:
    last_token = ts.TokenObject(
        AccessToken="fake-access-token",
        AccessExpires=10,
        AccessRefreshEpoch=123122,
        RefreshToken="fake-refresh-token",
        RefreshExpires=50,
        # making RefreshExpires + CreationEpoch bigger than mocked now (123123)
        CreationEpoch=123123 - 50 + 1,
    )

    token_store_mock = Mock()
    token_store_mock.get_last_token.return_value = last_token
    test_store = MockTokenStore(token_store_mock)
    assert test_store.is_refresh_token_valid("my-user-id") is True
    token_store_mock.get_last_token.assert_called_once_with("my-user-id")


def test_token_store_invalid_refresh_token() -> None:
    last_token = ts.TokenObject(
        AccessToken="fake-access-token",
        AccessExpires=10,
        AccessRefreshEpoch=123122,
        RefreshToken="fake-refresh-token",
        RefreshExpires=50,
        # making RefreshExpires + CreationEpoch bigger than mocked now (123123)
        CreationEpoch=123123 - 50,
    )

    token_store_mock = Mock()
    token_store_mock.get_last_token.return_value = last_token
    test_store = MockTokenStore(token_store_mock)
    assert test_store.is_refresh_token_valid("my-user-id") is False
    token_store_mock.get_last_token.assert_called_once_with("my-user-id")


def test_token_store_not_found_refresh_token() -> None:
    token_store_mock = Mock()
    token_store_mock.get_last_token.side_effect = ts.TokenNotFound
    test_store = MockTokenStore(token_store_mock)
    assert test_store.is_refresh_token_valid("my-user-id") is False
    token_store_mock.get_last_token.assert_called_once_with("my-user-id")


def test_token_store_child_save_token() -> None:
    previous_token = ts.TokenObject(
        AccessToken="previous-fake-access-token",
        AccessExpires=11,
        AccessRefreshEpoch=123122,
        RefreshToken="previous-fake-refresh-token",
        RefreshExpires=51,
        CreationEpoch=123124,
    )
    token_to_be_saved = ts.TokenObject(
        AccessToken="fake-access-token",
        AccessExpires=10,
        AccessRefreshEpoch=123122,
        RefreshToken="fake-refresh-token",
        RefreshExpires=50,
        CreationEpoch=123123,
    )

    token_store_mock = Mock()
    token_store_mock.save_token.return_value = previous_token
    test_store = MockTokenStore(token_store_mock)
    retured_token = test_store.save_token("my-user-id", token_to_be_saved)
    assert retured_token == previous_token
    token_store_mock.save_token.assert_called_once_with("my-user-id", token_to_be_saved)
