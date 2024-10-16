from unittest.mock import Mock
from personal_finances.bank_interface.bank_client import AuthorizationUrl
from personal_finances.bank_interface.requisition_store import (
    gocardless_requisition_adapter,
    GocardlessRequisitionValidator,
    Requisitions,
    RequisitionStore,
    EMPTY_REQUISITIONS,
)
from typing import cast


class MockRequisitionStore(RequisitionStore):
    def __init__(self, test_mock: Mock):
        self.test_mock = test_mock

    def save_requisitions(
        self, user_id: str, requisition: Requisitions
    ) -> Requisitions:
        return cast(Requisitions, self.test_mock.save_requisition(user_id, requisition))

    def get_last_requisitions(self, user_id: str) -> Requisitions:
        return cast(Requisitions, self.test_mock.get_last_requisition(user_id))


def test_requisition_adapter_empty_requisitions() -> None:
    assert gocardless_requisition_adapter([]) == EMPTY_REQUISITIONS


def test_requisition_adapter() -> None:
    assert gocardless_requisition_adapter(
        [
            AuthorizationUrl(
                payload="1", validation_reference="1", authorization_url="l1"
            ),
            AuthorizationUrl(
                payload="2", validation_reference="2", authorization_url="l2"
            ),
        ]
    ) == Requisitions(RequisitionIds=["1", "2"])


def test_requisition_store_valid_access_requisition() -> None:
    last_requisition = Requisitions(RequisitionIds=["1", "2"])

    requisition_store_mock = Mock()
    requisition_store_mock.get_last_requisition.return_value = last_requisition
    test_store = MockRequisitionStore(requisition_store_mock)
    gocardless_api_mock = Mock()
    gocardless_api_mock.get_requisition_by_id.return_value = {"status": "LN"}
    validator = GocardlessRequisitionValidator(gocardless_api_mock)
    assert test_store.are_stored_requisitions_valid("my-user-id", validator) is True
    requisition_store_mock.get_last_requisition.assert_called_once_with("my-user-id")


def test_requisition_store_one_invalid() -> None:
    last_requisition = Requisitions(RequisitionIds=["1", "2"])

    requisition_store_mock = Mock()
    requisition_store_mock.get_last_requisition.return_value = last_requisition
    test_store = MockRequisitionStore(requisition_store_mock)
    gocardless_api_mock = Mock()
    gocardless_api_mock.get_requisition_by_id.side_effect = [
        {"status": "LN"},  # <-- valid one
        {"status": "INVALID"},
    ]
    validator = GocardlessRequisitionValidator(gocardless_api_mock)
    assert test_store.are_stored_requisitions_valid("my-user-id", validator) is False
    requisition_store_mock.get_last_requisition.assert_called_once_with("my-user-id")


def test_requisition_store_empty_is_invalid() -> None:
    requisition_store_mock = Mock()
    requisition_store_mock.get_last_requisition.return_value = EMPTY_REQUISITIONS
    test_store = MockRequisitionStore(requisition_store_mock)
    validator = GocardlessRequisitionValidator(Mock())
    assert test_store.are_stored_requisitions_valid("my-user-id", validator) is False
    requisition_store_mock.get_last_requisition.assert_called_once_with("my-user-id")
