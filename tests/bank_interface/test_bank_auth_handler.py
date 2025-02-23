from unittest.mock import patch, call, Mock
from pytest import fixture
from personal_finances.bank_interface.bank_auth_handler import (
    BankAuthorizationHandler,
    NordigenAuth,
)
from personal_finances.bank_interface.bank_client import BankDetails
from personal_finances.bank_interface.requisition_store import (
    GocardlessRequisitionValidator,
    Requisitions,
)
from personal_finances.bank_interface.token_store import TokenObject
from nordigen.types import RequisitionDto
from typing import Generator


@fixture(autouse=True)
def uuid4_mock() -> Generator[Mock, None, None]:
    with patch("personal_finances.bank_interface.bank_client.uuid.uuid4") as mock:
        mock.side_effect = ["first-uuid", "second-uuid", "third-uuid"]
        yield mock


@fixture(autouse=True)
def localhost_provider_mock() -> Generator[Mock, None, None]:
    with patch(
        "personal_finances.bank_interface.bank_auth_handler.LocalhostValidationProvider"
    ) as mock:
        yield mock


@fixture(autouse=True)
def webbrowser_mock() -> Generator[Mock, None, None]:
    with patch("personal_finances.bank_interface.browser_helper.webbrowser") as mock:
        yield mock


@fixture(autouse=True)
def sleep_mock() -> Generator[Mock, None, None]:
    with patch("personal_finances.bank_interface.bank_auth_handler.sleep") as m:
        yield m


@fixture(autouse=True)
def token_now_mock() -> Generator[Mock, None, None]:
    with patch("personal_finances.bank_interface.token_store.datetime") as m:
        m.now.return_value.timestamp.return_value = 321
        yield m


@fixture(autouse=True)
def bank_client_now_mock() -> Generator[Mock, None, None]:
    with patch("personal_finances.bank_interface.bank_client.datetime") as m:
        m.now.return_value.timestamp.return_value = 3212
        yield m


@fixture(autouse=True)
def nordigen_client_mock() -> Generator[Mock, None, None]:
    with patch(
        "personal_finances.bank_interface.bank_auth_handler.NordigenClient"
    ) as mock:
        mock.return_value.generate_token.__name__ = "generate_token"
        mock.return_value.institution.get_institution_id_by_name.__name__ = (
            "get_institution_id_by_name"
        )
        mock.return_value.institution.get_institution_id_by_name.side_effect = [
            "inst1",
            "inst2",
            "inst3",
            "inst4",
        ]

        mock.return_value.initialize_session.__name__ = "initialize_session"
        mock.return_value.initialize_session.side_effect = [
            RequisitionDto(link="link1", requisition_id="requisition_id1"),
            RequisitionDto(link="link2", requisition_id="requisition_id2"),
            RequisitionDto(link="link3", requisition_id="requisition_id3"),
            RequisitionDto(link="link4", requisition_id="requisition_id4"),
        ]

        yield mock


@fixture(autouse=True)
def disk_token_store_mock() -> Generator[Mock, None, None]:
    with patch(
        "personal_finances.bank_interface.bank_auth_handler.DiskTokenStore"
    ) as mock:
        mock.return_value.get_last_token.return_value = TokenObject(
            AccessToken="fake-last-access-token",
            AccessExpires=10,
            AccessRefreshEpoch=123122,
            RefreshToken="fake-last-refresh-token",
            RefreshExpires=50,
            CreationEpoch=123123,
        )
        yield mock


@fixture(autouse=True)
def disk_requisition_store_mock() -> Generator[Mock, None, None]:
    with patch(
        "personal_finances.bank_interface.bank_auth_handler.DiskRequisitionStore"
    ) as mock:
        mock.return_value.get_last_requisitions.return_value = Requisitions(
            RequisitionIds=[
                "requisition-from-disk",
                "requisition-persisted-from-store",
            ]
        )
        yield mock


def test_bank_auth_handler_initializes_valid_access_token(
    nordigen_client_mock: Mock, disk_token_store_mock: Mock
) -> None:
    disk_token_store_mock.return_value.is_access_token_valid.return_value = True
    BankAuthorizationHandler(
        NordigenAuth(secret_id="mock_secret_id", secret_key="mock_secret_key"),
        [
            BankDetails(name="mock_name1", country="mock_country1"),
            BankDetails(name="mock_name2", country="mock_country2"),
        ],
    )
    disk_token_store_mock.return_value.get_last_token.assert_called_once_with(
        "temporary-user-id"
    )
    nordigen_client_mock.assert_called_with(
        secret_id="mock_secret_id", secret_key="mock_secret_key"
    )
    assert nordigen_client_mock.return_value.token == "fake-last-access-token"


def test_bank_auth_handler_initializes_valid_refresh_token(
    nordigen_client_mock: Mock, disk_token_store_mock: Mock
) -> None:
    disk_token_store_mock.return_value.is_access_token_valid.return_value = False
    disk_token_store_mock.return_value.is_refresh_token_valid.return_value = True
    nordigen_client_mock.return_value.exchange_token.return_value = {
        "access": "newly-generated-token",
        "access_expires": 10,
    }
    BankAuthorizationHandler(
        NordigenAuth(secret_id="mock_secret_id", secret_key="mock_secret_key"),
        [
            BankDetails(name="mock_name1", country="mock_country1"),
            BankDetails(name="mock_name2", country="mock_country2"),
        ],
    )
    disk_token_store_mock.return_value.get_last_token.assert_called_once_with(
        "temporary-user-id"
    )
    disk_token_store_mock.return_value.save_token.assert_called_once_with(
        "temporary-user-id",
        TokenObject(
            AccessToken="newly-generated-token",
            AccessExpires=10,
            AccessRefreshEpoch=3212,
            RefreshToken="fake-last-refresh-token",
            RefreshExpires=50,
            CreationEpoch=123123,
        ),
    )
    nordigen_client_mock.assert_called_with(
        secret_id="mock_secret_id", secret_key="mock_secret_key"
    )
    nordigen_client_mock.return_value.exchange_token.assert_called_once_with(
        "fake-last-refresh-token"
    )


def test_bank_auth_handler_initializes_invalid_token(
    nordigen_client_mock: Mock, disk_token_store_mock: Mock
) -> None:
    disk_token_store_mock.return_value.is_access_token_valid.return_value = False
    disk_token_store_mock.return_value.is_refresh_token_valid.return_value = False

    nordigen_client_mock.return_value.generate_token.return_value = {
        "access": "newly-generated-token",
        "access_expires": 10,
        "refresh": "newly-generated-token",
        "refresh_expires": 50,
    }

    BankAuthorizationHandler(
        NordigenAuth(secret_id="mock_secret_id", secret_key="mock_secret_key"),
        [
            BankDetails(name="mock_name1", country="mock_country1"),
            BankDetails(name="mock_name2", country="mock_country2"),
        ],
    )

    disk_token_store_mock.return_value.get_last_token.assert_not_called()
    disk_token_store_mock.return_value.save_token.assert_called_once_with(
        "temporary-user-id",
        TokenObject(
            AccessToken="newly-generated-token",
            AccessExpires=10,
            AccessRefreshEpoch=321,
            RefreshToken="newly-generated-token",
            RefreshExpires=50,
            CreationEpoch=321,
        ),
    )
    nordigen_client_mock.assert_called_with(
        secret_id="mock_secret_id", secret_key="mock_secret_key"
    )
    nordigen_client_mock.return_value.generate_token.assert_called_once_with()
    assert nordigen_client_mock.return_value.token == "newly-generated-token"


def test_bank_auth_handler_empty_requisition_store(
    nordigen_client_mock: Mock,
    disk_requisition_store_mock: Mock,
    localhost_provider_mock: Mock,
    webbrowser_mock: Mock,
) -> None:
    localhost_mock = localhost_provider_mock.return_value.__enter__.return_value
    localhost_mock.get_validation_url.side_effect = ["url1", "url2"]
    disk_req_store_mock = disk_requisition_store_mock.return_value
    disk_req_store_mock.are_stored_requisitions_valid.return_value = False

    nordigen_client = nordigen_client_mock.return_value
    BankAuthorizationHandler(
        NordigenAuth(secret_id="mock_secret_id", secret_key="mock_secret_key"),
        [
            BankDetails(name="mock_name1", country="mock_country1"),
            BankDetails(name="mock_name2", country="mock_country2"),
        ],
    )

    nordigen_client.initialize_session.assert_has_calls(
        [
            call(
                institution_id="inst1",
                redirect_uri="url1",
                reference_id="first-uuid",
            ),
            call(
                institution_id="inst2",
                redirect_uri="url2",
                reference_id="second-uuid",
            ),
        ]
    )
    assert (
        disk_req_store_mock.are_stored_requisitions_valid.call_args[0][0]
        == "temporary-user-id"
    )
    assert isinstance(
        disk_req_store_mock.are_stored_requisitions_valid.call_args[0][1],
        GocardlessRequisitionValidator,
    )
    disk_req_store_mock.save_requisitions.assert_called_once_with(
        "temporary-user-id",
        Requisitions(RequisitionIds=["requisition_id1", "requisition_id2"]),
    )
    nordigen_client.institution.get_institution_id_by_name.assert_has_calls(
        [
            call(country="mock_country1", institution="mock_name1"),
            call(country="mock_country2", institution="mock_name2"),
        ]
    )

    localhost_mock.is_reference_validated.assert_has_calls(
        [call("first-uuid"), call().__bool__(), call("second-uuid"), call().__bool__()]
    )
    webbrowser_mock.open.assert_has_calls([call("link1"), call("link2")])

    assert webbrowser_mock.open.call_count == 2
    assert localhost_mock.is_reference_validated.call_count == 2
    assert nordigen_client.initialize_session.call_count == 2
    assert nordigen_client.institution.get_institution_id_by_name.call_count == 2


def test_bank_auth_handler_existing_requisition_store(
    nordigen_client_mock: Mock,
    disk_requisition_store_mock: Mock,
    localhost_provider_mock: Mock,
    webbrowser_mock: Mock,
) -> None:
    disk_req_store_mock = disk_requisition_store_mock.return_value
    disk_req_store_mock.are_stored_requisitions_valid.return_value = True

    BankAuthorizationHandler(
        NordigenAuth(secret_id="mock_secret_id", secret_key="mock_secret_key"),
        [
            BankDetails(name="mock_name1", country="mock_country1"),
            BankDetails(name="mock_name2", country="mock_country2"),
        ],
    )

    nordigen_client = nordigen_client_mock.return_value
    nordigen_client.initialize_session.assert_not_called()
    assert (
        disk_req_store_mock.are_stored_requisitions_valid.call_args[0][0]
        == "temporary-user-id"
    )
    assert isinstance(
        disk_req_store_mock.are_stored_requisitions_valid.call_args[0][1],
        GocardlessRequisitionValidator,
    )

    disk_req_store_mock.save_requisitions.assert_not_called()
    nordigen_client.institution.get_institution_id_by_name.assert_not_called()
    localhost_provider_mock.is_reference_validated.assert_not_called()
    webbrowser_mock.open.assert_not_called()
