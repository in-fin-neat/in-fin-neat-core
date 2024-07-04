from typing import Generator
from unittest.mock import patch, Mock, mock_open

from pytest import fixture, raises

from personal_finances.bank_interface.key_value_disk_store import (
    KeyValueDiskStore,
    InvalidAbsolutePath,
    ValueNotFound,
)


class TestKeyValueDiskStore:
    @fixture
    def mock_write_string(self) -> Generator[Mock, None, None]:
        with patch(
            "personal_finances.bank_interface.key_value_disk_store.write_string"
        ) as m:
            yield m

    def test_init_with_non_absolute_path(self) -> None:
        with raises(InvalidAbsolutePath):
            KeyValueDiskStore("relative/path")

    def test_init_with_empty_path_parts(self) -> None:
        with raises(InvalidAbsolutePath):
            KeyValueDiskStore("/valid//path/with/empty/part")

    def test_init_valid(self) -> None:
        store = KeyValueDiskStore("/valid/path")
        assert store.path_prefix == "/valid/path"

    def test_remove_trailing_char(self) -> None:
        store = KeyValueDiskStore("/valid/path/")
        assert store.path_prefix == "/valid/path"

    def test_write_to_disk_with_forward_slash(self, mock_write_string: Mock) -> None:
        """Test writing data to disk."""
        store = KeyValueDiskStore("/valid/path/")
        mock_write_string.return_value = "Success"
        result = store.write_to_disk("file.txt", "write-data")
        mock_write_string.assert_called_with("/valid/path/file.txt", "write-data")
        assert result == "Success"

    def test_write_to_disk_without_forward_slash(self, mock_write_string: Mock) -> None:
        """Test writing data to disk."""
        store = KeyValueDiskStore("/valid/path")
        mock_write_string.return_value = "Success"
        result = store.write_to_disk("file.txt", "write-data")
        mock_write_string.assert_called_with("/valid/path/file.txt", "write-data")
        assert result == "Success"

    @patch("builtins.open", new_callable=mock_open, read_data="read-data")
    def test_read_from_disk(self, mock_open: Mock) -> None:
        """Test reading data from disk."""
        store = KeyValueDiskStore("/valid/path")
        result = store.read_from_disk("file.txt")
        mock_open.assert_called_with("/valid/path/file.txt", "r")
        assert result == "read-data"

    @patch("builtins.open", new_callable=mock_open)
    def test_read_from_disk_fail(self, mock_open: Mock) -> None:
        """Test exception handling when reading from disk fails."""
        mock_open.side_effect = Exception("File not found")
        store = KeyValueDiskStore("/valid/path")
        with raises(ValueNotFound):
            store.read_from_disk("nonexistent.txt")
