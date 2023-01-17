import os
import json


def create_dirs(path):
    if "/" in path:
        try:
            directories = "/".join(path.split("/")[:-1])
            os.makedirs(directories)
        except FileExistsError:
            pass


def write_json(path, content):
    create_dirs(path)
    with open(path, "w") as o_file:
        o_file.write(json.dumps(content, indent=4))
