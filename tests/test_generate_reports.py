from unittest.mock import Mock, patch, mock_open
import pytest
from pytest import fixture
from click.testing import CliRunner
from personal_finances.generate_reports import generate_reports

transactions_file = '{"test" : "teste" }'


@fixture(autouse=True)
def open_mock() -> Generator[Mock, None, None]:
    m = mock_open(read_data = transactions_file)()
    with patch("personal_finances.fetch_transactions.open", m):
        yield m


def test_malformed_time_interval_is_rejected() -> None:
    # TODO:: invalid string format test
    runner = CliRunner()
    result = runner.invoke(generate_reports, ['--st 1971-01-01T00:00:00Z --et 1970-01-01T00:00:00Z'])
    assert result.exception == ValueError
    pass


def test_reads_correct_input_transaction_file() -> None:
    # TODO: test default and custom file
    # TODO: test file path extension is json
    # TODO: test malformed json content is rejected
    with patch("personal_finances.generate_reports.open") as open_mock:
        runner = CliRunner()
        result = runner.invoke(generate_reports, [])
        open_mock.path.exists.assert_called_once_with("config/user_config.yaml")
        assert result.exit_code == 0
    
    with patch("personal_finances.generate_reports.open") as open_mock:
        runner = CliRunner()
        result = runner.invoke(generate_reports, ['-tfp test_file_path'])
        open_mock.path.exists.assert_called_once_with("test_file_path")
        assert result.exit_code == 0
    
    open_mock = mock_open(read_data = "this is not a json file")()
    with patch("personal_finances.generate_reports.open", open_mock):
        runner = CliRunner()
        result = runner.invoke(generate_reports, [])
        open_mock.path.exists.assert_called_once_with("test_file_path")
        assert result.exception
        
        open_mock = mock_open(read_data = '{ "malformed": json }')()
    with patch("personal_finances.generate_reports.open", open_mock):
        runner = CliRunner()
        result = runner.invoke(generate_reports, [])
        open_mock.path.exists.assert_called_once_with("test_file_path")
        assert result.exception
        

def test_reads_correct_input_user_config_file() -> None:
    # TODO: test default and custom file
    # TODO: test filepath extensions is yaml
    # TODO: test malformed yaml thows downstream exception
    #       UserConfigurationParseError
    pass


def test_dummy_output_reports_have_correct_format() -> None:
    # TODO: check if 7 files are written:
    # 1. balance.json,
    # 2. expense_categorized_transaction.json
    # 3. expense_per_category.json
    # 4. expense_per_group.json
    # 5. income_categorized_transaction.json
    # 6. income_per_category.json
    # 7. income_per_group.json
    pass


def test_long_list_of_transactions() -> None:
    # TODO: 
    pass