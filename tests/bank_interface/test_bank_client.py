from typing import cast
from unittest.mock import Mock, call

from personal_finances.bank_interface.bank_client import GocardlessClient
from personal_finances.bank_interface.nordigen_adapter import NordigenTransactions


def get_nordigen_mock() -> Mock:
    nordigen_mock = Mock()

    nordigen_mock.requisition.get_requisition_by_id.__name__ = "get_requisition_by_id"
    nordigen_mock.requisition.get_requisition_by_id.side_effect = [
        {"accounts": ["account11", "account12"]},
        {"accounts": ["account21", "account22"]},
    ]

    nordigen_mock.account_api.__name__ = "account_api"
    nordigen_mock.account_api.return_value.get_transactions.__name__ = (
        "get_transactions"
    )
    nordigen_mock.account_api.return_value.get_transactions.side_effect = [
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
    return nordigen_mock


def test_get_transactions() -> None:
    nordigen_mock = get_nordigen_mock()
    test_client = GocardlessClient(nordigen_mock)
    result_transactions = test_client.get_transactions(["requisition1", "requisition2"])

    nordigen_mock.requisition.get_requisition_by_id.assert_has_calls(
        [call(requisition_id="requisition1"), call(requisition_id="requisition2")]
    )
    nordigen_mock.account_api.assert_has_calls(
        [
            call(id="account11"),
            call().get_transactions(),
            call(id="account12"),
            call().get_transactions(),
            call(id="account21"),
            call().get_transactions(),
            call(id="account22"),
            call().get_transactions(),
        ]
    )
    nordigen_mock.account_api.return_value.get_transactions.assert_has_calls(
        [call(), call(), call(), call()]
    )
    assert result_transactions == cast(
        NordigenTransactions,
        {
            "booked": [
                "transaction_b11",
                "transaction_b12",
                "transaction_b21",
                "transaction_b31",
                "transaction_b41",
                "transaction_b42",
            ],
            "pending": [
                "transaction_p11",
                "transaction_p21",
                "transaction_p22",
                "transaction_p31",
                "transaction_p41",
            ],
        },
    )
