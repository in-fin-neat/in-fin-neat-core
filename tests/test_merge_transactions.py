from pytest import fixture
from unittest.mock import patch, Mock, mock_open
from typing import Generator, List
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


@fixture(autouse=True)
def datetime_mock() -> Generator[Mock, None, None]:
    with patch("personal_finances.merge_transactions.datetime") as mock:
        yield mock


def new_transaction(
    amount: float,
    transactionId: str,
    internalTransactionId: str,
    currency: str,
) -> NordigenTransaction:
    return NordigenTransaction(
        bookingDate="2021-01-01T10:00:00.00000",
        bookingDatetime="2021-01-01T10:00:00.00000",
        transactionAmount=TransactionAmount(currency=currency, amount=amount),
        transactionId=transactionId,
        internalTransactionId=internalTransactionId,
    )


def new_transaction_only_with_id(
    amount: float,
    transactionId: str,
    currency: str,
) -> NordigenTransaction:
    return NordigenTransaction(
        bookingDate="2021-01-01T10:00:00.00000",
        bookingDatetime="2021-01-01T10:00:00.00000",
        transactionAmount=TransactionAmount(currency=currency, amount=amount),
        transactionId=transactionId,
    )


def new_transaction_without_id(amount: float, currency: str) -> NordigenTransaction:
    return NordigenTransaction(
        bookingDate="2021-01-01T10:00:00.00000",
        bookingDatetime="2021-01-01T10:00:00.00000",
        transactionAmount=TransactionAmount(currency=currency, amount=amount),
    )


def new_transaction_only_with_internal_id(
    amount: float, internalTransactionId: str, currency: str
) -> NordigenTransaction:
    return NordigenTransaction(
        bookingDate="2021-01-01T10:00:00.00000",
        bookingDatetime="2021-01-01T10:00:00.00000",
        transactionAmount=TransactionAmount(currency=currency, amount=amount),
        internalTransactionId=internalTransactionId,
    )


def create_nordigen_tranctions(transaction_list: List[NordigenTransaction]) -> str:
    return json.dumps(
        NordigenTransactions(
            booked=transaction_list,
            pending=[new_transaction_only_with_id(5.0, "noise", "EUR")],
        )
    )


SAME_ID_TRANSACTIONS = [
    # An identical transactionId represents the same
    # transaction regardless of any other parameter.
    new_transaction_only_with_id(15.0, "same_id", "EUR"),
    new_transaction_only_with_id(45.0, "same_id", "EUR"),
    new_transaction(45.0, "same_id", "inter_id", "EUR"),
    new_transaction_only_with_id(45.0, "same_id", "EUR"),
]

SAME_INTERNAL_ID_TRANSACTIONS = [
    new_transaction_only_with_internal_id(45.0, "same_id", "EUR"),
    new_transaction_only_with_internal_id(40.0, "inter_id", "EUR"),
    new_transaction_only_with_internal_id(40.0, "inter_id", "USD"),
    new_transaction_only_with_internal_id(40.0, "inter_id", "BRL"),
    new_transaction_only_with_internal_id(10.0, "inter_id", "EUR"),
    new_transaction_only_with_internal_id(10.0, "inter_id", "EUR"),
    new_transaction_only_with_internal_id(10.0, "inter_id", "EUR"),
    new_transaction_only_with_internal_id(-10.0, "inter_id", "EUR"),
]


EXPECTED_SAME_ID_MERGED = [
    # The sorting prioritizes the transaction with more information available
    new_transaction(45.0, "same_id", "inter_id", "EUR"),
    new_transaction_only_with_internal_id(45.0, "same_id", "EUR"),
    new_transaction_only_with_internal_id(40.0, "inter_id", "EUR"),
    new_transaction_only_with_internal_id(10.0, "inter_id", "EUR"),
    new_transaction_only_with_internal_id(-10.0, "inter_id", "EUR"),
    new_transaction_only_with_internal_id(40.0, "inter_id", "BRL"),
    new_transaction_only_with_internal_id(40.0, "inter_id", "USD"),
]

WITHOUT_ID_TRANSACTIONS = [
    [
        new_transaction_without_id(45.0, "USD"),
        new_transaction_without_id(40.0, "USD"),
    ],
    [
        new_transaction_without_id(45.0, "USD"),
        new_transaction_without_id(-40.0, "USD"),
    ],
]

EXPECTED_WITHOUT_ID_MERGED = [
    new_transaction_without_id(45.0, "USD"),
    new_transaction_without_id(40.0, "USD"),
    new_transaction_without_id(45.0, "USD"),
    new_transaction_without_id(-40.0, "USD"),
]


def assert_is_list_equal(
    return_list: List[NordigenTransaction],
    expected_list: List[NordigenTransaction],
) -> None:
    for expected_item in expected_list:
        assert expected_item in return_list
    assert len(expected_list) == len(return_list)


@pytest.mark.parametrize(
    "transactions_file_names, valid_files_number, transactions_list, merged_expected",
    [
        ([], 0, [], []),
        (
            ["transactions_a.json", "transnoise1.bmp", "transactions_b.json"],
            2,
            [
                create_nordigen_tranctions(SAME_ID_TRANSACTIONS),
                create_nordigen_tranctions(SAME_INTERNAL_ID_TRANSACTIONS),
            ],
            EXPECTED_SAME_ID_MERGED,
        ),
        (
            ["transactions_a.json", "transnoise2.jpg", "transactions_b.json"],
            2,
            [
                create_nordigen_tranctions(list(reversed(SAME_ID_TRANSACTIONS))),
                create_nordigen_tranctions(
                    list(reversed(SAME_INTERNAL_ID_TRANSACTIONS))
                ),
            ],
            EXPECTED_SAME_ID_MERGED,
        ),
        (
            ["transactions_a.json", "transnoise3.json", "transactions_b.json"],
            2,
            [
                create_nordigen_tranctions(WITHOUT_ID_TRANSACTIONS[0]),
                create_nordigen_tranctions(WITHOUT_ID_TRANSACTIONS[1]),
            ],
            EXPECTED_WITHOUT_ID_MERGED,
        ),
    ],
)
def test_merge_transaction(
    transactions_file_names: List[str],
    valid_files_number: int,
    transactions_list: List[str],
    merged_expected: List[NordigenTransaction],
    open_mock: Mock,
    listdir_mock: Mock,
    write_json_mock: Mock,
    datetime_mock: Mock,
) -> None:
    listdir_mock.return_value = transactions_file_names
    open_mock.return_value.read.side_effect = transactions_list
    mock_dummy_datetime = "2024-01-01T10:00:00.00000"
    datetime_mock.now.return_value.isoformat.return_value = mock_dummy_datetime

    runner = CliRunner()
    result = runner.invoke(merge_transactions, [])

    assert result.exit_code == 0
    assert (
        write_json_mock.call_args.args[0]
        == f"data/merged_transactions-{mock_dummy_datetime}.json"
    )

    assert_is_list_equal(
        return_list=write_json_mock.call_args.args[1], expected_list=merged_expected
    )
    assert open_mock.return_value.read.call_count == valid_files_number


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


def test_non_existing_data_folder(listdir_mock: Mock, write_json_mock: Mock) -> None:
    listdir_mock.side_effect = FileNotFoundError

    runner = CliRunner()
    result = runner.invoke(merge_transactions, [])

    assert result.exit_code != 0
    assert isinstance(result.exception, FileNotFoundError)
    write_json_mock.assert_not_called()


def test_empty_data_folder_should_create_empty_output(
    open_mock: Mock,
    listdir_mock: Mock,
    write_json_mock: Mock,
    datetime_mock: Mock,
) -> None:
    listdir_mock.return_value = []
    mock_dummy_datetime = "2024-01-01T10:00:00.00000"
    datetime_mock.now.return_value.isoformat.return_value = mock_dummy_datetime

    runner = CliRunner()
    result = runner.invoke(merge_transactions, [])

    open_mock.return_value.read.assert_not_called()
    assert result.exit_code == 0
    assert write_json_mock.call_args.args[1] == []
    assert (
        write_json_mock.call_args.args[0]
        == f"data/merged_transactions-{mock_dummy_datetime}.json"
    )
