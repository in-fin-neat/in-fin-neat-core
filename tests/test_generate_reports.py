import json
import dateutil.parser
from unittest.mock import Mock, patch, mock_open
import pytest
from pytest import fixture
from click.testing import CliRunner
from personal_finances.generate_reports import (
    generate_reports,
    InvalidDatetimeRange,
    InvalidDatetime,
)
from typing import Generator, Any, List

transactions_file = '{"test" : "teste"}'


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
def fh_open_mock() -> Generator[Mock, None, None]:
    with patch("personal_finances.file_helper.open") as m:
        yield m


@pytest.mark.parametrize(
    "command_params,exception_type",
    [
        (["-aa", "-bb", "-cc", "1970-01-01T00:00:01Z"], SystemExit),
        (
            ["-st", "1971-01-01T00:00:00Z", "-et", "1970-01-01T00:00:01Z"],
            InvalidDatetimeRange,
        ),
        (
            [
                "--start-time",
                "1971-01-01T00:00:00Z",
                "--end-time",
                "1970-01-01T00:00:01Z",
            ],
            InvalidDatetimeRange,
        ),
        (["-st", "123", "-et", "1970-01-01T00:00:01Z"], InvalidDatetime),
        (["-st", "1971-01-01T00:00:00Z", "-et", "123"], InvalidDatetime),
        (["-st", "123", "-et", "123"], InvalidDatetime),
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
    "command_params,user_file_path,transactions_file_path,expected_st,expected_et",
    [
        (
            [],
            "config/user_config.yaml",
            "data/merged_transactions_latest.json",
            "1970-01-01T00:00:00Z",
            "2100-01-01T00:00:00Z",
        ),
        (
            ["-st", "2010-01-01T00:00:00Z", "-et", "2023-01-01T00:00:01Z"],
            "config/user_config.yaml",
            "data/merged_transactions_latest.json",
            "2010-01-01T00:00:00Z",
            "2023-01-01T00:00:01Z",
        ),
        (
            [
                "--start-time",
                "2010-01-01T00:00:00Z",
                "--end-time",
                "2023-01-01T00:00:01Z",
            ],
            "config/user_config.yaml",
            "data/merged_transactions_latest.json",
            "2010-01-01T00:00:00Z",
            "2023-01-01T00:00:01Z",
        ),
        (
            ["-tfp", "/path/to/my/transactions.json"],
            "config/user_config.yaml",
            "/path/to/my/transactions.json",
            "1970-01-01T00:00:00Z",
            "2100-01-01T00:00:00Z",
        ),
        (
            ["--transactions-file-path", "/path/to/my/transactions.json"],
            "config/user_config.yaml",
            "/path/to/my/transactions.json",
            "1970-01-01T00:00:00Z",
            "2100-01-01T00:00:00Z",
        ),
        (
            ["-ucfp", "/path/to/my/user_config.yaml"],
            "/path/to/my/user_config.yaml",
            "data/merged_transactions_latest.json",
            "1970-01-01T00:00:00Z",
            "2100-01-01T00:00:00Z",
        ),
        (
            ["--user-config-file-path", "/path/to/my/user_config.yaml"],
            "/path/to/my/user_config.yaml",
            "data/merged_transactions_latest.json",
            "1970-01-01T00:00:00Z",
            "2100-01-01T00:00:00Z",
        ),
        (
            ["-st", "2010-01-01", "-et", "2023-01-01T00:00:01Z"],
            "config/user_config.yaml",
            "data/merged_transactions_latest.json",
            "2010-01-01T00:00:00Z",
            "2023-01-01T00:00:01Z",
        ),
        (
            ["-st", "2010-01-01T00:00:00Z", "-et", "2023-01-01"],
            "config/user_config.yaml",
            "data/merged_transactions_latest.json",
            "2010-01-01T00:00:00Z",
            "2023-01-01T00:00:00Z",
        ),
        (
            ["-st", "2010-01-01", "-et", "2023-01-01"],
            "config/user_config.yaml",
            "data/merged_transactions_latest.json",
            "2010-01-01T00:00:00Z",
            "2023-01-01T00:00:00Z",
        ),
        (
            [
                "--start-time",
                "2010-01-01",
                "--end-time",
                "2023-01-01T00:00:01Z",
            ],
            "config/user_config.yaml",
            "data/merged_transactions_latest.json",
            "2010-01-01T00:00:00Z",
            "2023-01-01T00:00:01Z",
        ),
        (
            [
                "--start-time",
                "2010-01-01T00:00:00Z",
                "--end-time",
                "2023-01-01",
            ],
            "config/user_config.yaml",
            "data/merged_transactions_latest.json",
            "2010-01-01T00:00:00Z",
            "2023-01-01T00:00:00Z",
        ),
        (
            [
                "--start-time",
                "2010-01-01",
                "--end-time",
                "2023-01-01",
            ],
            "config/user_config.yaml",
            "data/merged_transactions_latest.json",
            "2010-01-01T00:00:00Z",
            "2023-01-01T00:00:00Z",
        ),
    ],
)
def test_correct_cli_params(
    command_params: List[str],
    user_file_path: str,
    transactions_file_path: str,
    expected_st: str,
    expected_et: str,
    cache_user_configuration_mock: Mock,
    open_mock: Mock,
    json_mock: Mock,
) -> None:
    with patch(
        "personal_finances.generate_reports._write_reports"
    ) as write_reports_mock:
        runner = CliRunner()
        result = runner.invoke(generate_reports, command_params)
        assert result.exit_code == 0
        cache_user_configuration_mock.assert_called_once_with(user_file_path)
        open_mock.assert_called_once_with(transactions_file_path, "r")
        write_reports_mock.assert_called_once_with(
            list(),
            dateutil.parser.isoparse(expected_st),
            dateutil.parser.isoparse(expected_et),
        )


def assert_file_content_json(file_path: str, result: str) -> None:
    with open(file_path, "r") as expected_result:
        json_result = json.loads(expected_result.read())
        assert json_result == json.loads(result)


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


def test_generate_reports_output(fh_open_mock: Mock) -> None:

    transactions_test_file_path = "tests/test_data/transactions/test_transaction.json"
    configuration_test_file_path = "tests/test_data/config/test_config_file.yaml"

    expected_result_path_prefix = (
        "reports/1970-01-01T00:00:00+00:00_2100-01-01T00:00:00+00:00/"
    )
    expected_content_path_prefix = "tests/test_data/expected/"
    expected_file_name_list = (
        "balance.json",
        "income_per_group.json",
        "income_per_category.json",
        "income_categorized_transactions.json",
        "expense_per_group.json",
        "expense_per_category.json",
        "expense_categorized_transactions.json",
    )

    exit_code = _run_generate_reports(
        transactions_test_file_path, configuration_test_file_path
    )
    assert exit_code == 0

    open_paths = fh_open_mock.call_args_list
    write_content_list = fh_open_mock.return_value.__enter__.return_value.write

    result_calls = {
        result_call.args[0].removeprefix(expected_result_path_prefix): {
            "file_path": result_call.args[0],
            "file_content": write_content_list.call_args_list[idx].args[0],
        }
        for idx, result_call in enumerate(open_paths)
    }

    for expected_file_name in expected_file_name_list:
        result_file_path = result_calls[expected_file_name]["file_path"]
        result_file_content = result_calls[expected_file_name]["file_content"]

        assert result_file_path == expected_result_path_prefix + expected_file_name
        assert_file_content_json(
            expected_content_path_prefix + expected_file_name, result_file_content
        )
