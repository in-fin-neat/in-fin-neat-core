from unittest.mock import mock_open, patch, Mock
from pytest import fixture
from click.testing import CliRunner
from typing import Generator
from personal_finances.fetch_transactions import fetch_transactions


@fixture()
def os_mock() -> Generator[Mock, None, None]:
    with patch("personal_finances.fetch_transactions.os") as mock:
        yield mock


@fixture(autouse=True)
def bank_client_mock() -> Generator[Mock, None, None]:
    with patch("personal_finances.fetch_transactions.BankClient") as mock:
        yield mock


@fixture(autouse=True)
def open_mock() -> Generator[Mock, None, None]:
    m = mock_open()
    with patch("personal_finances.fetch_transactions.open", m):
        yield m


@fixture(autouse=True)
def json_mock() -> Generator[Mock, None, None]:
    with patch("personal_finances.fetch_transactions.json") as mock:
        yield mock


def test_data_path_not_created_if_already_exists(os_mock: Mock) -> None:
    """
    Mock to return like the data path already exists.
    At this way, the function should not try to create a path for it.
    """
    os_mock.path.exists.return_value = True

    runner = CliRunner()
    runner.invoke(fetch_transactions, ["-s dummy_secrets.json"])

    os_mock.path.exists.assert_called_once_with("data")
    os_mock.makedirs.assert_not_called()


def test_data_path_is_created_if_not_exists(os_mock: Mock) -> None:
    """
    Mock to return like the data path has yet to be created.
    In this way, the function should create it.
    """
    os_mock.path.exists.return_value = False

    runner = CliRunner()
    runner.invoke(fetch_transactions, ["-s dummy_secrets.json"])

    os_mock.path.exists.assert_called_once_with("data")
    os_mock.makedirs.assert_called_once_with("data")


def test_json_file_not_found(open_mock: Mock) -> None:
    open_mock = mock_open(read_data=None)
    open_mock.side_effect = FileNotFoundError
    with patch("personal_finances.fetch_transactions.open", open_mock):
        runner = CliRunner()
        result = runner.invoke(fetch_transactions, ["-s dummy_secrets.json"])
        assert result.exit_code != 0
        assert isinstance(
            result.exception, IOError
        ), f"Expected an IOError, but got {type(result.exception).__name__}"


def test_json_file_not_valid(json_mock: Mock) -> None:
    json_mock.loads.side_effect = ValueError
    runner = CliRunner()
    result = runner.invoke(fetch_transactions, ["-s dummy_secrets.json"])
    assert result.exit_code != 0
    assert isinstance(
        result.exception, ValueError
    ), f"Expected an ValueError, but got {type(result.exception).__name__}"


def test_json_missing_key(json_mock: Mock) -> None:
    json_mock.loads.return_value = {"secret_id": "dummy_data"}
    runner = CliRunner()
    result = runner.invoke(fetch_transactions, ["-s dummy_secrets.json"])
    assert result.exit_code != 0
    assert isinstance(
        result.exception, KeyError
    ), f"Expected an KeyError, but got {type(result.exception).__name__}"

    json_mock.loads.return_value = {"secret_key": "dummy_data"}
    runner = CliRunner()
    result = runner.invoke(fetch_transactions, ["-s dummy_secrets.json"])
    assert result.exit_code != 0
    assert isinstance(
        result.exception, KeyError
    ), f"Expected an KeyError, but got {type(result.exception).__name__}"
