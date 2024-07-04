from personal_finances.bank_interface.key_value_disk_store import (
    KeyValueDiskStore,
    ValueNotFound,
)
from .token_store import TokenStore, TokenObject
from typing import Optional
import json
import logging
from .token_store import TokenNotFound
from pydantic import ValidationError
import os


LOGGER = logging.getLogger(__name__)


class TokenAbsolutePathNotConfigured(Exception):
    pass


def _get_path_from_env() -> str:
    try:
        return os.environ["TOKEN_DISK_PATH_PREFIX"]
    except KeyError as e:
        raise TokenAbsolutePathNotConfigured(e)


class DiskTokenStore(TokenStore):
    disk_store: KeyValueDiskStore

    def __init__(self) -> None:
        self.disk_store = KeyValueDiskStore(_get_path_from_env())

    def save_token(self, user_id: str, token: TokenObject) -> Optional[TokenObject]:
        previous_content = self.disk_store.write_to_disk(
            f"{user_id}.json", token.model_dump_json()
        )
        try:
            previous_token = TokenObject.model_validate_json(previous_content)
        except (json.JSONDecodeError, ValidationError) as e:
            LOGGER.warning("error decoding json from token: " + str(e))
            previous_token = None

        return previous_token

    def get_last_token(self, user_id: str) -> TokenObject:
        try:
            return TokenObject.model_validate_json(
                self.disk_store.read_from_disk(f"{user_id}.json")
            )
        except ValueNotFound as e:
            raise TokenNotFound from e
