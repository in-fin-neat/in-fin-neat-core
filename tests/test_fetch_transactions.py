import pytest
import re
import io
import os
from typing import List

from personal_finances.fetch_transactions import _ensure_data_path_exist


def test_if_data_path_gets_created() -> None:
    """
    Change current execution folder to tests to not consider the 'data'
    folder from the application execution, what could lead to a false positive
    in the test result
    """
    os.chdir("tests")
    _ensure_data_path_exist()

    data_path_get_created = os.path.exists("data")
    assert data_path_get_created

    """
    Cleaning path after testing execution
    """
    if data_path_get_created:
        os.rmdir("data")
