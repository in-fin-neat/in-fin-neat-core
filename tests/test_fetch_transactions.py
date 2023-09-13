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
    with patch("__main__.open", m):
        yield m


def test_data_path_not_created_if_already_exists(os_mock: Mock) -> None:
    """ 
    Mock to return like the data path already exists.
    At this way, the function should not try to create a path for it.
    """
    os_mock.path.exists.return_value = True

    runner = CliRunner()
    runner.invoke(fetch_transactions, [])

    os_mock.path.exists.assert_called_once_with("data")
    os_mock.makedirs.assert_not_called()


def test_data_path_is_created_if_not_exists(os_mock: Mock) -> None:
    """ 
    Mock to return like the data path has yet to be created. 
    In this way, the function should create it.
    """
    os_mock.path.exists.return_value = False

    runner = CliRunner()
    runner.invoke(fetch_transactions, [])

    os_mock.path.exists.assert_called_once_with("data")
    os_mock.makedirs.assert_called_once_with("data")
