import os
import json
from typing import Any, Callable, Optional


def create_dirs(path: str) -> None:
    if "/" in path:
        try:
            directories = "/".join(path.split("/")[:-1])
            os.makedirs(directories)
        except FileExistsError:
            pass


def write_json(
    path: str, content: Any, json_converter: Optional[Callable] = str
) -> None:
    create_dirs(path)
    with open(path, "w") as o_file:
        o_file.write(json.dumps(content, indent=4, default=json_converter))


def write_string(
    path: str, content: str, json_converter: Optional[Callable] = str
) -> str:
    create_dirs(path)
    with open(path, "w+") as o_file:
        previous_content = o_file.read()
        o_file.write(content)
        return previous_content
