from personal_finances.bank_interface.key_value_disk_store import (
    KeyValueDiskStore,
    ValueNotFound,
)
from .requisition_store import EMPTY_REQUISITIONS, RequisitionStore, Requisitions
import json
import logging
from pydantic import ValidationError
import os


LOGGER = logging.getLogger(__name__)


class RequisitionAbsolutePathNotConfigured(Exception):
    pass


def _get_path_from_env() -> str:
    try:
        return os.environ["REQUISITION_DISK_PATH_PREFIX"]
    except KeyError as e:
        raise RequisitionAbsolutePathNotConfigured(e)


class DiskRequisitionStore(RequisitionStore):
    disk_store: KeyValueDiskStore

    def __init__(self) -> None:
        self.disk_store = KeyValueDiskStore(_get_path_from_env())

    def save_requisitions(
        self, user_id: str, requisition: Requisitions
    ) -> Requisitions:
        previous_content = self.disk_store.write_to_disk(
            f"{user_id}.json", requisition.model_dump_json()
        )
        try:
            return Requisitions.model_validate_json(previous_content)
        except (json.JSONDecodeError, ValidationError) as e:
            LOGGER.warning("error decoding json from requisition: " + str(e))
            return EMPTY_REQUISITIONS

    def get_last_requisitions(self, user_id: str) -> Requisitions:
        try:
            return Requisitions.model_validate_json(
                self.disk_store.read_from_disk(f"{user_id}.json")
            )
        except ValueNotFound:
            return EMPTY_REQUISITIONS
