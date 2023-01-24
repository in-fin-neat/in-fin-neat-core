import os
import json
from typing import Any


def create_dirs(path: str) -> None:
    if "/" in path:
        try:
            directories = "/".join(path.split("/")[:-1])
            os.makedirs(directories)
        except FileExistsError:
            pass


def write_json(path: str, content: Any) -> None:
    create_dirs(path)
    with open(path, "w") as o_file:
        o_file.write(json.dumps(content, indent=4))
