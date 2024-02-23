from unittest.mock import Mock, patch
import pytest
from click.testing import CliRunner
from personal_finances.generate_reports import generate_reports


def test_malformed_time_interval_is_rejected() -> None:
    # TODO: test start and end times
    pass


def test_reads_correct_input_transaction_file() -> None:
    # TODO: test default and custom file
    # TODO: test file path extension is json
    # TODO: test malformed json content is rejected
    pass


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
