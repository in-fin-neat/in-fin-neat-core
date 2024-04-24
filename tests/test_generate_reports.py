from copy import deepcopy
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
from personal_finances.config import (
    cache_user_configuration,
    clear_user_configuration_cache,
)
from typing import Dict, Generator, Any, List
from personal_finances.transaction.categorizing import get_category
from personal_finances.transaction.grouping import (
    GroupedTransaction,
    TransactionGroupingType,
    group_transactions,
)
from personal_finances.transaction.type import (
    get_income_transactions,
    get_expense_transactions,
    get_unknown_type_transactions,
)
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


@fixture()
def json_mock() -> Generator[Mock, None, None]:
    with patch("personal_finances.generate_reports.json") as m:
        yield m


@fixture()
def write_json_mock() -> Generator[Mock, None, None]:
    with patch("personal_finances.generate_reports.write_json") as m:
        yield m


def assert_is_list_equal(
    return_list: List[Any],
    expected_list: List[Any],
) -> None:
    for expected_item in expected_list:
        assert expected_item in return_list
    assert len(expected_list) == len(return_list)


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


def _open_transaction_test_file(transactions_file_path: str) -> List[SimpleTransaction]:
    with open(transactions_file_path, "r") as transactions_file:
        return list(
            map(
                as_simple_transaction,
                json.loads(transactions_file.read()),
            )
        )


def _split_transactions(
    transactions: List[SimpleTransaction],
) -> tuple[List[SimpleTransaction], List[SimpleTransaction]]:

    keys_to_filter = [
        "f8ca9991a65f4230d108d47514696580",
        "4dd99d3dd2a66105f441459561e5abcc",
    ]
    transactions = [
        transaction
        for transaction in transactions
        if transaction["transactionId"] not in keys_to_filter
    ]

    income_transactions = get_income_transactions(transactions)
    expense_transactions = get_expense_transactions(
        transactions
    ) + get_unknown_type_transactions(transactions)
    return (income_transactions, expense_transactions)


def _sum_amount_transactions(transactions: List[SimpleTransaction]) -> float:
    total_amount = 0.0
    for transaction in transactions:
        total_amount += transaction["amount"]
    return total_amount


def _run_generate_reports(transactions_path: str, configuration_path: str) -> int:
    runner = CliRunner()
    return runner.invoke(
        generate_reports,
        [
            "-ucfp",
            configuration_path,
            "-tfp",
            transactions_path,
        ],
    ).exit_code


def _expected_balance(
    incomes: List[SimpleTransaction], expenses: List[SimpleTransaction]
) -> dict:
    total_income = _sum_amount_transactions(incomes)
    total_expense = _sum_amount_transactions(expenses)
    total_balance = total_income + total_expense

    expected_balance_dict = {
        "start_time": datetime(1970, 1, 1, 0, 0, tzinfo=tzutc()),
        "end_time": datetime(2100, 1, 1, 0, 0, tzinfo=tzutc()),
        "total_income": total_income,
        "total_expense": total_expense,
        "total_balance": total_balance,
    }

    return expected_balance_dict


def _expected_group_by_ref(grouped_transactions: List[GroupedTransaction]) -> List[Any]:
    grouped_by_ref: Dict[Any, Any] = {}

    for transaction in grouped_transactions:
        group_number = transaction["groupNumber"]
        grouped = grouped_by_ref.get(group_number)
        if grouped is None:
            grouped_by_ref[group_number] = {
                "key": group_number,
                "amount": transaction["amount"],
                "references": [transaction["referenceText"]],
                "groupName": transaction["groupName"],
            }
        else:
            grouped["amount"] += transaction["amount"]
            grouped["references"] += [transaction["referenceText"]]

    grouped_by_ref_list = list(grouped_by_ref.values())
    return grouped_by_ref_list


def _expected_categ_group(
    grouped_transactions: List[GroupedTransaction],
    group_references: List[set[str]],
) -> List[Any]:
    transactions = deepcopy(grouped_transactions)
    transactions_ref = deepcopy(group_references)
    categories_group: Dict[Any, Any] = {}

    for transaction in transactions:
        key_category = get_category(
            transaction["referenceText"],
            transactions_ref[transaction["groupNumber"]],
            fallback_reference=transaction["groupName"],
        )
        category_group = categories_group.get(key_category)
        if category_group is None:
            categories_group[key_category] = {
                "key": key_category,
                "amount": transaction["amount"],
                "references": [transaction["referenceText"]],
            }
        else:
            category_group["amount"] += transaction["amount"]
            category_group["references"] += [transaction["referenceText"]]

    categories_group_list = list(categories_group.values())
    return categories_group_list


def _expected_categ_transactions(
    grouped_transactions: List[GroupedTransaction],
    group_references: List[set[str]],
) -> List[Any]:

    categorized_transactions: List[Any] = deepcopy(grouped_transactions)
    categorized_transactions_ref = deepcopy(group_references)

    for transaction in categorized_transactions:
        key_category = get_category(
            transaction["referenceText"],
            categorized_transactions_ref[transaction["groupNumber"]],
            fallback_reference=transaction["groupName"],
        )
        transaction["customCategory"] = key_category

    return categorized_transactions


def test_generate_reports_output(write_json_mock: Mock) -> None:

    transactions_test_file_path = "tests/test_data/transactions/test_transaction.json"
    configuration_test_file_path = "tests/test_data/config/test_config_file.yaml"
    cache_user_configuration(configuration_test_file_path)

    transactions_raw = _open_transaction_test_file(transactions_test_file_path)
    incomes, expenses = _split_transactions(transactions_raw)
    grouped_income, grouped_income_ref = group_transactions(
        incomes, TransactionGroupingType.ReferenceSimilarity
    )
    grouped_expense, grouped_expense_ref = group_transactions(
        expenses, TransactionGroupingType.ReferenceSimilarity
    )

    clear_user_configuration_cache()

    exit_code = _run_generate_reports(
        transactions_test_file_path, configuration_test_file_path
    )
    assert exit_code == 0

    result_calls = write_json_mock.call_args_list

    expected_path_name = "reports/1970-01-01T00:00:00+00:00_2100-01-01T00:00:00+00:00/"

    expected_balance_dict = _expected_balance(incomes, expenses)

    ei_group_by_ref = _expected_group_by_ref(grouped_income)
    ei_categories_group = _expected_categ_group(grouped_income, grouped_income_ref)
    ei_categorized = _expected_categ_transactions(grouped_income, grouped_income_ref)

    ee_group_by_ref = _expected_group_by_ref(grouped_expense)
    ee_categories_group = _expected_categ_group(grouped_expense, grouped_expense_ref)
    ee_categorized = _expected_categ_transactions(grouped_expense, grouped_expense_ref)

    assert result_calls[0].args[0] == expected_path_name + "balance.json"
    assert result_calls[0].args[1] == expected_balance_dict

    assert result_calls[1].args[0] == expected_path_name + "income_per_group.json"
    assert_is_list_equal(result_calls[1].args[1], ei_group_by_ref)

    assert result_calls[2].args[0] == expected_path_name + "income_per_category.json"
    assert_is_list_equal(result_calls[2].args[1], ei_categories_group)

    assert (
        result_calls[3].args[0]
        == expected_path_name + "income_categorized_transactions.json"
    )
    assert_is_list_equal(result_calls[3].args[1], ei_categorized)

    assert result_calls[4].args[0] == expected_path_name + "expense_per_group.json"
    assert_is_list_equal(result_calls[4].args[1], ee_group_by_ref)

    assert result_calls[5].args[0] == expected_path_name + "expense_per_category.json"
    assert_is_list_equal(result_calls[5].args[1], ee_categories_group)

    assert (
        result_calls[6].args[0]
        == expected_path_name + "expense_categorized_transactions.json"
    )
    assert_is_list_equal(result_calls[6].args[1], ee_categorized)
