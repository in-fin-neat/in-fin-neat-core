from unittest.mock import patch, Mock
from pydantic import ValidationError
from pytest import raises, fixture
from personal_finances.bank_interface.disk_token_store import (
    DiskTokenStore,
    TokenAbsolutePathNotConfigured,
)
from personal_finances.bank_interface.key_value_disk_store import ValueNotFound
from personal_finances.bank_interface.token_store import TokenObject, TokenNotFound
from typing import Generator


class SomeBizarreError(Exception):
    pass


@fixture(autouse=True)
def key_value_disk_mock() -> Generator[Mock, None, None]:
    with patch(
        "personal_finances.bank_interface.disk_token_store.KeyValueDiskStore",
    ) as m:
        yield m


@fixture(autouse=True)
def env_mock() -> Generator[Mock, None, None]:
    with patch("personal_finances.bank_interface.disk_token_store.os.environ") as m:
        m.__getitem__.side_effect = {
            "TOKEN_DISK_PATH_PREFIX": "/test-token/path"
        }.__getitem__
        yield m


@fixture(autouse=True)
def mock_file_os() -> Generator[Mock, None, None]:
    with patch("personal_finances.file_helper.os") as env_mock:
        yield env_mock


def test_rejects_missing_token_path(env_mock: Mock) -> None:
    env_mock.__getitem__.side_effect = KeyError
    with raises(TokenAbsolutePathNotConfigured):
        disk_store = DiskTokenStore()
        disk_store.get_last_token("my-user-id")


def test_save_token_returns_previous_token(key_value_disk_mock: Mock) -> None:
    new_token = TokenObject(
        AccessToken="fake-access-token",
        AccessExpires=10,
        AccessRefreshEpoch=123122,
        RefreshToken="fake-refresh-token",
        RefreshExpires=50,
        CreationEpoch=123123,
    )
    previous_token = TokenObject(
        AccessToken="previous-fake-access-token",
        AccessExpires=11,
        AccessRefreshEpoch=123122,
        RefreshToken="previous-fake-refresh-token",
        RefreshExpires=51,
        CreationEpoch=123124,
    )

    key_value_disk_mock.return_value.write_to_disk.return_value = (
        previous_token.model_dump_json()
    )

    disk_store = DiskTokenStore()
    disk_store.save_token("my-user-id", new_token)
    key_value_disk_mock.return_value.write_to_disk.assert_called_once_with(
        "my-user-id.json", new_token.model_dump_json()
    )

    disk_store = DiskTokenStore()
    retrieved_previous_token = disk_store.save_token("my-user-id", new_token)
    assert retrieved_previous_token == previous_token


def test_save_token_returns_none_json_error(key_value_disk_mock: Mock) -> None:
    new_token = TokenObject(
        AccessToken="fake-access-token",
        AccessExpires=10,
        AccessRefreshEpoch=123122,
        RefreshToken="fake-refresh-token",
        RefreshExpires=50,
        CreationEpoch=123123,
    )

    key_value_disk_mock.return_value.write_to_disk.return_value = "{malformed-json["

    disk_store = DiskTokenStore()
    retrieved_previous_token = disk_store.save_token("my-user-id", new_token)
    assert retrieved_previous_token is None


def test_save_token_reraises_write_error(key_value_disk_mock: Mock) -> None:
    new_token = TokenObject(
        AccessToken="fake-access-token",
        AccessExpires=10,
        AccessRefreshEpoch=123122,
        RefreshToken="fake-refresh-token",
        RefreshExpires=50,
        CreationEpoch=123123,
    )

    key_value_disk_mock.return_value.write_to_disk.side_effect = SomeBizarreError

    disk_store = DiskTokenStore()

    with raises(SomeBizarreError):
        disk_store.save_token("my-user-id", new_token)


def test_get_last_token_not_found_error(key_value_disk_mock: Mock) -> None:
    key_value_disk_mock.return_value.read_from_disk.side_effect = ValueNotFound
    disk_store = DiskTokenStore()

    with raises(TokenNotFound):
        disk_store.get_last_token("my-user-id")


def test_get_last_token_reraises_file_error(key_value_disk_mock: Mock) -> None:
    key_value_disk_mock.return_value.read_from_disk.side_effect = SomeBizarreError
    disk_store = DiskTokenStore()

    with raises(SomeBizarreError):
        disk_store.get_last_token("my-user-id")


def test_get_last_token_raises_json_error(key_value_disk_mock: Mock) -> None:
    disk_store = DiskTokenStore()

    key_value_disk_mock.return_value.read_from_disk.return_value = "{malformed[json:"
    with raises(ValidationError):
        disk_store.get_last_token("my-user-id")


def test_get_last_token_succeeds(key_value_disk_mock: Mock) -> None:
    last_token = TokenObject(
        AccessToken="fake-access-token",
        AccessExpires=10,
        AccessRefreshEpoch=123122,
        RefreshToken="fake-refresh-token",
        RefreshExpires=50,
        CreationEpoch=123123,
    )
    disk_store = DiskTokenStore()

    key_value_disk_mock.return_value.read_from_disk.return_value = (
        last_token.model_dump_json()
    )
    returned_last_token = disk_store.get_last_token("my-user-id")
    assert returned_last_token == last_token
