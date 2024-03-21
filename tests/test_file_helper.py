from unittest.mock import mock_open, patch, Mock, call
from pytest import fixture, raises
from typing import Generator
from personal_finances.file_helper import write_string


@fixture(autouse=True)
def os_mock() -> Generator[Mock, None, None]:
    with patch("personal_finances.file_helper.os") as mock:
        yield mock


class MockException(Exception):
    pass


@patch("personal_finances.file_helper.open", new_callable=mock_open)
def test_write_string_reraises_open_exception(open_mock: Mock) -> None:
    open_mock.side_effect = MockException
    with raises(MockException):
        write_string("/my/path/file.txt", "test-content")


@patch(
    "personal_finances.file_helper.open",
    new_callable=lambda: mock_open(read_data="previous content"),
)
def test_write_string_returns_previous_content(open_mock: Mock) -> None:
    prev_content = write_string("/my/path/file.txt", "test-content")
    assert prev_content == "previous content"
    assert open_mock.mock_calls[0] == call("/my/path/file.txt", "w+")


@patch("personal_finances.file_helper.open", new_callable=mock_open)
def test_write_string_writes_to_file(open_mock: Mock) -> None:
    write_string("/my/path/file.txt", "test-content")
    file_handle = open_mock()
    file_handle.write.assert_called_once_with("test-content")
    assert open_mock.mock_calls[0] == call("/my/path/file.txt", "w+")


@patch("personal_finances.file_helper.open", new_callable=mock_open)
def test_write_string_writes_creates_path_dirs(open_mock: Mock, os_mock: Mock) -> None:
    write_string("/my/path/file.txt", "test-content")
    os_mock.makedirs.assert_called_once_with("/my/path")
    assert open_mock.mock_calls[0] == call("/my/path/file.txt", "w+")


@patch("personal_finances.file_helper.open", new_callable=mock_open)
def test_write_string_override_existing_file(open_mock: Mock, os_mock: Mock) -> None:
    os_mock.makedirs.side_effect = FileExistsError
    write_string("/my/path/file.txt", "test-content")
    file_handle = open_mock()
    file_handle.write.assert_called_once_with("test-content")
    assert open_mock.mock_calls[0] == call("/my/path/file.txt", "w+")
