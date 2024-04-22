from datetime import datetime
import json
from dateutil.tz import tzutc
from unittest.mock import Mock, patch, mock_open
import pytest
from pytest import fixture
from click.testing import CliRunner
from personal_finances.bank_interface.nordigen_adapter import as_simple_transaction
from personal_finances.generate_reports import (
    generate_reports,
    InvalidDatatimeRange,
    InvalidDatatime,
)
from personal_finances.config import clear_user_configuration_cache
from typing import Generator, Any, List
from personal_finances.transaction.type import get_income_transactions, get_expense_transactions, get_unknown_type_transactions
from personal_finances.transaction.definition import SimpleTransaction

transactions_file = '{"test" : "teste" }'


@fixture()
def open_mock() -> Generator[Mock, None, None]:
    m = mock_open(read_data=transactions_file)()
    with patch("personal_finances.generate_reports.open", m):
        yield m


@fixture()
def cache_user_configuration_mock() -> Generator[Mock, None, None]:
    with patch("personal_finances.generate_reports.cache_user_configuration") as m:
        
        yield m
        
        
@pytest.fixture()
def user_config_mock() -> Generator[Mock, None, None]:
    with patch(
        "personal_finances.transaction.categorizing.get_user_configuration"
    ) as u_mock:
        _get_expense_category_references.cache_clear(),
        _get_expense_category_tags.cache_clear()
        _get_income_category_references.cache_clear()
        u_mock.return_value.ExpenseCategoryDefinition = [
            CategoryDefinition(
                CategoryName="house",
                CategoryReferences=["ikea", "dealz"],
                CategoryTags=[],
            ),
            CategoryDefinition(
                CategoryName="restaurants/pubs",
                CategoryReferences=["some-fancy-pub"],
                CategoryTags=["#coffee", "#restaurant"],
            ),
            CategoryDefinition(
                CategoryName="entertainment",
                CategoryReferences=["odeon"],
                CategoryTags=[],
            ),
        ]

        u_mock.return_value.IncomeCategoryDefinition = []
        yield u_mock



@fixture()
def json_mock() -> Generator[Mock, None, None]:
    with patch("personal_finances.generate_reports.json") as m:
        yield m


@fixture()
def write_json_mock() -> Generator[Mock, None, None]:
    with patch("personal_finances.generate_reports.write_json") as m:
        yield m

        
@pytest.mark.parametrize(
    "command_params,exception_type",
    [
        (["-aa", "-bb", "-cc", "1970-01-01T00:00:01Z"], SystemExit),
        (
            ["-st", "1971-01-01T00:00:00Z", "-et", "1970-01-01T00:00:01Z"],
            InvalidDatatimeRange,
        ),
        (
            [
                "--start-time",
                "1971-01-01T00:00:00Z",
                "--end-time",
                "1970-01-01T00:00:01Z",
            ],
            InvalidDatatimeRange,
        ),
        (["-st", "123", "-et", "1970-01-01T00:00:01Z"], InvalidDatatime),
        (["-st", "1971-01-01T00:00:00Z", "-et", "123"], InvalidDatatime),
        (["-st", "123", "-et", "123"], InvalidDatatime),
    ],
)
def test_malformed_cli_params_rejected(
    command_params: str, exception_type: Any
) -> None:
    runner = CliRunner()
    result = runner.invoke(generate_reports, command_params)
    assert result.exit_code != 0
    assert isinstance(result.exception, exception_type)


@pytest.mark.parametrize(
    "command_params,user_file_path,transactions_file_path",
    [
        ([], "config/user_config.yaml", "data/merged_transactions.json"),
        (
            ["-st", "2010-01-01T00:00:00Z", "-et", "2023-01-01T00:00:01Z"],
            "config/user_config.yaml",
            "data/merged_transactions.json",
        ),
        (
            [
                "--start-time",
                "2010-01-01T00:00:00Z",
                "--end-time",
                "2023-01-01T00:00:01Z",
            ],
            "config/user_config.yaml",
            "data/merged_transactions.json",
        ),
        (
            ["-tfp", "/path/to/my/transactions.json"],
            "config/user_config.yaml",
            "/path/to/my/transactions.json",
        ),
        (
            ["--transactions-file-path", "/path/to/my/transactions.json"],
            "config/user_config.yaml",
            "/path/to/my/transactions.json",
        ),
        (
            ["-ucfp", "/path/to/my/user_config.yaml"],
            "/path/to/my/user_config.yaml",
            "data/merged_transactions.json",
        ),
        (
            ["--user-config-file-path", "/path/to/my/user_config.yaml"],
            "/path/to/my/user_config.yaml",
            "data/merged_transactions.json",
        ),
    ],
)
def test_correct_cli_params(
    command_params: List[str],
    user_file_path: str,
    transactions_file_path: str,
    cache_user_configuration_mock: Mock,
    open_mock: Mock,
    json_mock: Mock,
) -> None:
    with patch("personal_finances.generate_reports._write_reports"):
        runner = CliRunner()
        result = runner.invoke(generate_reports, command_params)
        assert result.exit_code == 0
        cache_user_configuration_mock.assert_called_once_with(user_file_path)
        open_mock.assert_called_once_with(transactions_file_path, "r")
'''
@patch("personal_finances.generate_reports.remove_internal_transfers")
@patch("personal_finances.generate_reports.transaction_datetime_filter")
@patch("personal_finances.generate_reports.get_income_transactions")
@patch("personal_finances.generate_reports.get_expense_transactions")
@patch("personal_finances.generate_reports.get_unknown_type_transactions")
def test_dummy_output_reports_have_correct_format(
    get_unknown_type_transactions:Mock,
    get_expense_transactions:Mock,
    get_income_transactions:Mock,
    write_json_mock: Mock) -> None: 
'''

def _open_transaction_test_file(transactions_file_path) -> List[SimpleTransaction]:
    with open(transactions_file_path, "r") as transactions_file:
        return list(
            map(
                as_simple_transaction,
                json.loads(transactions_file.read()),
            )
        )
        
        
def _split_transactions(transactions: List[SimpleTransaction]):
    
    keys_to_filter = ['f8ca9991a65f4230d108d47514696580', '4dd99d3dd2a66105f441459561e5abcc']
    transactions = [
        transaction 
        for transaction in transactions 
        if transaction['transactionId'] not in keys_to_filter
    ]
    
    income_transactions = get_income_transactions(transactions)
    expense_transactions = get_expense_transactions(transactions) + get_unknown_type_transactions(transactions)
    return (income_transactions, expense_transactions)
    
    
def _sum_amount_transactions(transactions: List[SimpleTransaction]) -> int:
    total_amount = 0
    for transaction in transactions:
        total_amount += transaction["amount"]    
    return total_amount


def test_balance_output_is_correct(write_json_mock: Mock) -> None:    

    transactions_test_file_path = "tests/test_data/transactions/test_transaction.json"
    runner = CliRunner()
    result = runner.invoke(generate_reports, ["-ucfp", 
                                              "tests/test_data/config/test_config_file.yaml", 
                                              "-tfp", 
                                              transactions_test_file_path])
    

    transactions_raw = _open_transaction_test_file(transactions_test_file_path)
    income_transactions, expense_transactions = _split_transactions(transactions_raw)
    
    total_income = _sum_amount_transactions(income_transactions)
    total_expense = _sum_amount_transactions(expense_transactions)
    total_balance = total_income + total_expense
    
    expected_balance_dict = {
        "start_time": datetime(1970, 1, 1, 0, 0, tzinfo=tzutc()),
        "end_time": datetime(2100, 1, 1, 0, 0, tzinfo=tzutc()),
        "total_income": total_income,
        "total_expense": total_expense,
        "total_balance": total_balance
    }
    assert write_json_mock.call_args_list[0].args[0] == 'reports/1970-01-01T00:00:00+00:00_2100-01-01T00:00:00+00:00/balance.json'
    assert write_json_mock.call_args_list[0].args[1] == expected_balance_dict

