from pytest import fixture
from unittest.mock import patch, Mock, mock_open
from typing import Generator, List, Optional, Union
from click.testing import CliRunner
import pytest
from personal_finances.bank_interface.nordigen_adapter import (
    TransactionAmount,
    NordigenTransaction,
    NordigenTransactions,
)
import json
from personal_finances.merge_transactions import merge_transactions


@fixture(autouse=True)
def write_json_mock() -> Generator[Mock, None, None]:
    with patch("personal_finances.merge_transactions.write_json") as mock:
        yield mock


@fixture(autouse=True)
def listdir_mock() -> Generator[Mock, None, None]:
    with patch("personal_finances.merge_transactions.os.listdir") as mock:
        yield mock


@fixture(autouse=True)
def open_mock() -> Generator[Mock, None, None]:
    m = mock_open()
    with patch("personal_finances.merge_transactions.open", m):
        yield m


def create_nordigen_transaction(
    amount: float, id: Optional[str] = None, internal_id: Optional[str] = None
) -> NordigenTransaction:
    params: dict = {
        "bookingDate": "dummy_data",
        "bookingDatetime": "dummy_data",
        "transactionAmount": TransactionAmount(currency="EUR", amount=amount),
    }

    if internal_id is not None:
        params["internalTransactionId"] = internal_id  # Adjust the key if provided

    if id is not None:
        params["transactionId"] = id  # Adjust the key if provided

    return NordigenTransaction(**params)


TEST_SAME_ID_TRANSACTIONS = [
    json.dumps(
        NordigenTransactions(
            booked=[
                create_nordigen_transaction(amount=45.00, id="same_id"),
                create_nordigen_transaction(amount=40.00, internal_id="inter_id"),
                create_nordigen_transaction(amount=15.00, id="same_id"),
                create_nordigen_transaction(amount=10.00, internal_id="inter_id"),
            ],
            pending=[create_nordigen_transaction(amount=5.00, id="noise")],
        )
    ),
    json.dumps(
        NordigenTransactions(
            booked=[
                create_nordigen_transaction(amount=45.00, id="same_id"),
                create_nordigen_transaction(amount=40.00, internal_id="inter_id"),
                create_nordigen_transaction(amount=-15.00, id="same_id"),
                create_nordigen_transaction(amount=-10.00, internal_id="inter_id"),
            ],
            pending=[create_nordigen_transaction(amount=5.00, id="noise")],
        )
    ),
]
TEST_SAME_ID_MERGED = [
    # Only the first same_id entry will be considered. 
    # According to the Go cardless API, transactionId should not be repeated
    create_nordigen_transaction(amount=45.00, id="same_id"),
    create_nordigen_transaction(amount=40.00, internal_id="inter_id"),
    create_nordigen_transaction(amount=10.00, internal_id="inter_id"),
    create_nordigen_transaction(amount=-10.00, internal_id="inter_id"),
]

TEST_WITHOUT_ID_TRANSACTIONS = [
    json.dumps(
        NordigenTransactions(
            booked=[
                create_nordigen_transaction(amount=45.00),
                create_nordigen_transaction(amount=40.00),
            ],
            pending=[create_nordigen_transaction(amount=5.00, id="noise")],
        )
    ),
    json.dumps(
        NordigenTransactions(
            booked=[
                create_nordigen_transaction(amount=-45.00),
                create_nordigen_transaction(amount=-40.00),
            ],
            pending=[create_nordigen_transaction(amount=5.00, id="noise")],
        )
    ),
]
TEST_WITHOUT_ID_MERGED = [
    create_nordigen_transaction(amount=45.00),
    create_nordigen_transaction(amount=40.00),
    create_nordigen_transaction(amount=-45.00),
    create_nordigen_transaction(amount=-40.00),
]

@pytest.mark.parametrize(
    "transactions_name_list, transactions_list, merged_expected",
    [
        ([], [], []),
        (
            ["transactions_a.json", "noise.jpg", "transactions_b.json"],
            TEST_SAME_ID_TRANSACTIONS,
            TEST_SAME_ID_MERGED,
        ),
        (
            ["transactions_a.json", "transnoise.json", "transactions_b.json"],
            TEST_WITHOUT_ID_TRANSACTIONS,
            TEST_WITHOUT_ID_MERGED,
        ),
    ],
)
def test_merge_transaction(
    transactions_name_list: List[str],
    transactions_list: List[str],
    merged_expected: Union[str, None],
    open_mock: Mock,
    listdir_mock: Mock,
    write_json_mock: Mock,
) -> None:

    listdir_mock.return_value = transactions_name_list
    open_mock.return_value.read.side_effect = transactions_list

    runner = CliRunner()
    result = runner.invoke(merge_transactions, [])

    assert result.exit_code == 0
    assert write_json_mock.call_args.args[1] == merged_expected


def test_invalid_transaction_json_input(
    open_mock: Mock, listdir_mock: Mock, write_json_mock: Mock
) -> None:

    mocked_files_names = [
        "transactions-2024-04-07.json",
    ]
    listdir_mock.return_value = mocked_files_names
    open_mock.return_value.read.return_value = "{json:invalid{test"

    runner = CliRunner()
    result = runner.invoke(merge_transactions, [])

    assert result.exit_code != 0
    assert isinstance(result.exception, json.decoder.JSONDecodeError)
    write_json_mock.assert_not_called()


def test_data_path_not_found(listdir_mock: Mock, write_json_mock: Mock) -> None:
    listdir_mock.side_effect = FileNotFoundError

    runner = CliRunner()
    result = runner.invoke(merge_transactions, [])

    assert result.exit_code != 0
    assert isinstance(result.exception, FileNotFoundError)
    write_json_mock.assert_not_called()


def test_empty_data_folder_should_create_empty_output(
    open_mock: Mock, listdir_mock: Mock, write_json_mock: Mock
) -> None:

    listdir_mock.return_value = []

    runner = CliRunner()
    result = runner.invoke(merge_transactions, [])

    open_mock.return_value.read.assert_not_called()
    assert result.exit_code == 0
    assert write_json_mock.call_args.args[1] == []
