import os
from personal_finances.file_helper import write_string


class InvalidAbsolutePath(Exception):
    pass


class ValueNotFound(Exception):
    pass


class KeyValueDiskStore:
    path_prefix: str

    def __init__(self, store_path_prefix: str) -> None:
        self.path_prefix = self._get_disk_path_prefix(store_path_prefix)

    def _remove_trailing_char(self, input_string: str, trailing_char: str) -> str:
        return input_string[:-1] if input_string[-1] == trailing_char else input_string

    def _contains_empty_path_part(self, absolute_path: str) -> bool:
        return any(map(lambda path_part: path_part == "", absolute_path[1:].split("/")))

    def _get_disk_path_prefix(self, configured_path_prefix: str) -> str:
        if not os.path.isabs(configured_path_prefix):
            raise InvalidAbsolutePath(f"is not absolute path: {configured_path_prefix}")

        path_without_trailing_slash = self._remove_trailing_char(
            configured_path_prefix, "/"
        )

        if self._contains_empty_path_part(path_without_trailing_slash):
            raise InvalidAbsolutePath(
                f"contains empty path parts: {configured_path_prefix}"
            )

        return path_without_trailing_slash

    def write_to_disk(self, key: str, value: str) -> str:
        return write_string(
            f"{self.path_prefix}/{key}",
            value,
        )

    def read_from_disk(self, key: str) -> str:
        try:
            with open(f"{self.path_prefix}/{key}", "r") as value_file:
                return value_file.read()
        except Exception as e:
            raise ValueNotFound(e)
