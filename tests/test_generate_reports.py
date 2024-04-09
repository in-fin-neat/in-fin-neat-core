from unittest.mock import Mock, patch, mock_open
import pytest
from pytest import fixture
from click.testing import CliRunner
from personal_finances.generate_reports import (
    generate_reports,
    InvalidDatatimeRange,
    InvalidDatatime,
)
from typing import Generator, Any, List

transactions_file = '{"test" : "teste" }'


@fixture(autouse=True)
def open_mock() -> Generator[Mock, None, None]:
    m = mock_open(read_data=transactions_file)()
    with patch("personal_finances.generate_reports.open", m):
        yield m


@fixture(autouse=True)
def cache_user_configuration_mock() -> Generator[Mock, None, None]:
    with patch("personal_finances.generate_reports.cache_user_configuration") as m:
        yield m


@fixture()
def json_mock() -> Generator[Mock, None, None]:
    with patch("personal_finances.generate_reports.json") as m:
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


# def test_dummy_output_reports_have_correct_format() -> None:
#     # TODO: check if 7 files are written:
#     # 1. balance.json,
#     # 2. expense_categorized_transaction.json
#     # 3. expense_per_category.json
#     # 4. expense_per_group.json
#     # 5. income_categorized_transaction.json
#     # 6. income_per_category.json
#     # 7. income_per_group.json
#     pass


# def test_long_list_of_transactions() -> None:
#     # TODO:
#     pass
