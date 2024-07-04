from unittest.mock import patch, Mock
from pydantic import ValidationError
from pytest import raises, fixture
from personal_finances.bank_interface.disk_requisition_store import (
    DiskRequisitionStore,
    RequisitionAbsolutePathNotConfigured,
)
from personal_finances.bank_interface.key_value_disk_store import ValueNotFound
from personal_finances.bank_interface.requisition_store import (
    EMPTY_REQUISITIONS,
    Requisitions,
)
from typing import Generator


class SomeBizarreError(Exception):
    pass


@fixture(autouse=True)
def key_value_disk_mock() -> Generator[Mock, None, None]:
    with patch(
        "personal_finances.bank_interface.disk_requisition_store.KeyValueDiskStore",
    ) as m:
        yield m


@fixture(autouse=True)
def env_mock() -> Generator[Mock, None, None]:
    with patch(
        "personal_finances.bank_interface.disk_requisition_store.os.environ"
    ) as m:
        m.__getitem__.side_effect = {
            "REQUISITION_DISK_PATH_PREFIX": "/test-requisition/path"
        }.__getitem__
        yield m


@fixture(autouse=True)
def mock_file_os() -> Generator[Mock, None, None]:
    with patch("personal_finances.file_helper.os") as env_mock:
        yield env_mock


def test_rejects_missing_requisition_path(env_mock: Mock) -> None:
    env_mock.__getitem__.side_effect = KeyError
    with raises(RequisitionAbsolutePathNotConfigured):
        disk_store = DiskRequisitionStore()
        disk_store.get_last_requisitions("my-user-id")


def test_save_requisitions_returns_previous_requisition(
    key_value_disk_mock: Mock,
) -> None:
    new_requisition = Requisitions(RequisitionIds=["req1", "req2"])
    previous_requisition = Requisitions(RequisitionIds=["req3", "req4"])

    key_value_disk_mock.return_value.write_to_disk.return_value = (
        previous_requisition.model_dump_json()
    )

    disk_store = DiskRequisitionStore()
    disk_store.save_requisitions("my-user-id", new_requisition)
    key_value_disk_mock.return_value.write_to_disk.assert_called_once_with(
        "my-user-id.json", new_requisition.model_dump_json()
    )

    disk_store = DiskRequisitionStore()
    retrieved_previous_requisition = disk_store.save_requisitions(
        "my-user-id", new_requisition
    )
    assert retrieved_previous_requisition == previous_requisition


def test_save_requisitions_returns_none_json_error(key_value_disk_mock: Mock) -> None:
    new_requisition = Requisitions(RequisitionIds=["req1", "req2"])

    key_value_disk_mock.return_value.write_to_disk.return_value = "{malformed-json["

    disk_store = DiskRequisitionStore()
    retrieved_previous_requisition = disk_store.save_requisitions(
        "my-user-id", new_requisition
    )
    assert retrieved_previous_requisition == EMPTY_REQUISITIONS


def test_save_requisitions_reraises_write_error(key_value_disk_mock: Mock) -> None:
    new_requisition = Requisitions(RequisitionIds=["req1", "req2"])

    key_value_disk_mock.return_value.write_to_disk.side_effect = SomeBizarreError

    disk_store = DiskRequisitionStore()

    with raises(SomeBizarreError):
        disk_store.save_requisitions("my-user-id", new_requisition)


def test_get_last_requisitions_not_found_error(key_value_disk_mock: Mock) -> None:
    key_value_disk_mock.return_value.read_from_disk.side_effect = ValueNotFound
    disk_store = DiskRequisitionStore()

    assert disk_store.get_last_requisitions("my-user-id") == EMPTY_REQUISITIONS


def test_get_last_requisitions_reraises_file_error(key_value_disk_mock: Mock) -> None:
    key_value_disk_mock.return_value.read_from_disk.side_effect = SomeBizarreError
    disk_store = DiskRequisitionStore()

    with raises(SomeBizarreError):
        disk_store.get_last_requisitions("my-user-id")


def test_get_last_requisitions_raises_json_error(key_value_disk_mock: Mock) -> None:
    disk_store = DiskRequisitionStore()

    key_value_disk_mock.return_value.read_from_disk.return_value = "{malformed[json:"
    with raises(ValidationError):
        disk_store.get_last_requisitions("my-user-id")


def test_get_last_requisitions_succeeds(key_value_disk_mock: Mock) -> None:
    last_requisition = Requisitions(RequisitionIds=["req1", "req2"])
    disk_store = DiskRequisitionStore()

    key_value_disk_mock.return_value.read_from_disk.return_value = (
        last_requisition.model_dump_json()
    )
    returned_last_requisition = disk_store.get_last_requisitions("my-user-id")
    assert returned_last_requisition == last_requisition
