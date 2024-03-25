from unittest.mock import patch, call, Mock
from pytest import fixture
from personal_finances.bank_interface.client import (
    BankClient,
    BankDetails,
    NordigenAuth,
)
import signal
from nordigen.types import RequisitionDto
from typing import Generator


@fixture(autouse=True)
def nordigen_client_mock() -> Generator[Mock, None, None]:
    with patch("personal_finances.bank_interface.client.NordigenClient") as mock:
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

        mock.return_value.requisition.get_requisition_by_id.__name__ = (
            "get_requisition_by_id"
        )
        mock.return_value.requisition.get_requisition_by_id.side_effect = [
            {"accounts": ["account1"]},
            {"accounts": ["account2"]},
            {"accounts": ["account3"]},
            {"accounts": ["account4"]},
        ]

        mock.return_value.account_api.__name__ = "account_api"
        mock.return_value.account_api.return_value.get_transactions.__name__ = (
            "get_transactions"
        )
        mock.return_value.account_api.return_value.get_transactions.side_effect = [
            {
                "transactions": {
                    "booked": ["transaction_b11", "transaction_b12"],
                    "pending": ["transaction_p11"],
                }
            },
            {
                "transactions": {
                    "booked": ["transaction_b21"],
                    "pending": ["transaction_p21", "transaction_p22"],
                }
            },
            {
                "transactions": {
                    "booked": ["transaction_b31"],
                    "pending": ["transaction_p31"],
                }
            },
            {
                "transactions": {
                    "booked": ["transaction_b41", "transaction_b42"],
                    "pending": ["transaction_p41"],
                }
            },
        ]

        yield mock


@fixture(autouse=True)
def subprocess_mock() -> Generator[Mock, None, None]:
    with patch("personal_finances.bank_interface.client.subprocess") as mock:
        yield mock


@fixture(autouse=True)
def os_mock() -> Generator[Mock, None, None]:
    with patch("personal_finances.bank_interface.client.os") as mock:
        yield mock


@fixture(autouse=True)
def requests_mock() -> Generator[Mock, None, None]:
    with patch("personal_finances.bank_interface.client.requests") as mock:
        mock.get.return_value.json.side_effect = [
            [],
            [],
            [],
            [],
            ["auth1"],
            ["auth1", "auth2"],
        ]
        yield mock


@fixture(autouse=True)
def webbrowser_mock() -> Generator[Mock, None, None]:
    with patch("personal_finances.bank_interface.client.webbrowser") as mock:
        yield mock


@fixture(autouse=True)
def time_mock() -> Generator[Mock, None, None]:
    with patch("personal_finances.bank_interface.client.time") as mock:
        mock.time.side_effect = [1, 2, 3, 4]
        yield mock


def test_bank_client_initializes(nordigen_client_mock: Mock) -> None:
    BankClient(
        NordigenAuth(secret_id="mock_secret_id", secret_key="mock_secret_key"),
        [
            BankDetails(name="mock_name1", country="mock_country1"),
            BankDetails(name="mock_name2", country="mock_country2"),
        ],
    )
    nordigen_client_mock.assert_called_with(
        secret_id="mock_secret_id", secret_key="mock_secret_key"
    )


def test_bank_client_scope(subprocess_mock: Mock, os_mock: Mock) -> None:
    with BankClient(
        NordigenAuth(secret_id="mock_secret_id", secret_key="mock_secret_key"),
        [
            BankDetails(name="mock_name1", country="mock_country1"),
            BankDetails(name="mock_name2", country="mock_country2"),
        ],
    ):
        pass

    subprocess_mock.Popen.assert_called_with(
        ["uvicorn", "personal_finances.bank_interface.authorizer:app", "--reload"],
        preexec_fn=os_mock.setpgrp,
    )
    os_mock.getpgid.assert_called_with(subprocess_mock.Popen.return_value.pid)
    os_mock.killpg.assert_called_with(os_mock.getpgid.return_value, signal.SIGTERM)


def test_bank_client_calls_nordigen_client(
    nordigen_client_mock: Mock, requests_mock: Mock, webbrowser_mock: Mock
) -> None:
    nordigen_client = nordigen_client_mock.return_value
    with BankClient(
        NordigenAuth(secret_id="mock_secret_id", secret_key="mock_secret_key"),
        [
            BankDetails(name="mock_name1", country="mock_country1"),
            BankDetails(name="mock_name2", country="mock_country2"),
        ],
    ) as client:
        response = client.get_transactions()

    assert response == {
        "booked": ["transaction_b11", "transaction_b12", "transaction_b21"],
        "pending": ["transaction_p11", "transaction_p21", "transaction_p22"],
    }
    nordigen_client.generate_token.assert_called_once()
    nordigen_client.initialize_session.assert_has_calls(
        [
            call(
                institution_id="inst1",
                redirect_uri="http://127.0.0.1:8000/validations/inst1",
                reference_id="Diego Personal PC 1",
            ),
            call(
                institution_id="inst2",
                redirect_uri="http://127.0.0.1:8000/validations/inst2",
                reference_id="Diego Personal PC 2",
            ),
        ]
    )
    nordigen_client.institution.get_institution_id_by_name.assert_has_calls(
        [
            call(country="mock_country1", institution="mock_name1"),
            call(country="mock_country2", institution="mock_name2"),
        ]
    )
    nordigen_client.requisition.get_requisition_by_id.assert_has_calls(
        [call(requisition_id="requisition_id1"), call(requisition_id="requisition_id2")]
    )
    nordigen_client.account_api.return_value.get_transactions.assert_has_calls(
        [call(), call()]
    )
    requests_mock.get.assert_has_calls(
        [call("http://127.0.0.1:8000/validations/", verify=False), call().json()] * 6
    )

    assert webbrowser_mock.open.call_count == 2
    assert requests_mock.get.call_count == 6
    assert nordigen_client.initialize_session.call_count == 2
    assert nordigen_client.institution.get_institution_id_by_name.call_count == 2
    assert nordigen_client.requisition.get_requisition_by_id.call_count == 2
    assert nordigen_client.account_api.return_value.get_transactions.call_count == 2
