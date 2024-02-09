from unittest.mock import Mock, patch
import pytest
from typing import List, Generator
from personal_finances.transaction.cleaning import remove_internal_transfers
from personal_finances.transaction.definition import SimpleTransaction
from datetime import datetime


@pytest.fixture(autouse=True)
def user_config_mock() -> Generator[Mock, None, None]:
    with patch(
        "personal_finances.transaction.cleaning.get_user_configuration"
    ) as u_mock:
        u_mock.return_value.InternalTransferReferences = ["internal_reference_1"]
        u_mock.return_value.BankProcessingTimeInDays = 5
        yield u_mock


@pytest.mark.parametrize(
    "raw_transactions,clean_transactions",
    [
        ([], []),
        (
            [
                SimpleTransaction(
                    transactionId="transaction_1",
                    datetime=datetime(2022, 2, 1),
                    amount=0.1,
                    referenceText="reference_transaction_1",
                    bankTransactionCode="dummy_transaction_code",
                ),
                SimpleTransaction(
                    transactionId="transaction_2",
                    datetime=datetime(2022, 2, 1),
                    amount=0.2,
                    referenceText="reference_transaction_2",
                    bankTransactionCode="dummy_transaction_code",
                ),
            ],
            [
                SimpleTransaction(
                    transactionId="transaction_1",
                    datetime=datetime(2022, 2, 1),
                    amount=0.1,
                    referenceText="reference_transaction_1",
                    bankTransactionCode="dummy_transaction_code",
                ),
                SimpleTransaction(
                    transactionId="transaction_2",
                    datetime=datetime(2022, 2, 1),
                    amount=0.2,
                    referenceText="reference_transaction_2",
                    bankTransactionCode="dummy_transaction_code",
                ),
            ],
        ),
        (
            [
                SimpleTransaction(
                    transactionId="transaction_1",
                    datetime=datetime(2022, 2, 1),
                    amount=0.1,
                    referenceText="reference_transaction_1",
                    bankTransactionCode="dummy_transaction_code",
                ),
                SimpleTransaction(
                    transactionId="transaction_2",
                    datetime=datetime(2022, 2, 1),
                    amount=0.3,
                    referenceText="internal_reference_1",
                    bankTransactionCode="dummy_transaction_code",
                ),
                SimpleTransaction(
                    transactionId="transaction_3",
                    datetime=datetime(2022, 2, 1),
                    amount=-0.3,
                    referenceText="internal_reference_1",
                    bankTransactionCode="dummy_transaction_code",
                ),
            ],
            [
                SimpleTransaction(
                    transactionId="transaction_1",
                    datetime=datetime(2022, 2, 1),
                    amount=0.1,
                    referenceText="reference_transaction_1",
                    bankTransactionCode="dummy_transaction_code",
                ),
            ],
        ),
        (
            [
                SimpleTransaction(
                    transactionId="transaction_1",
                    datetime=datetime(2022, 2, 1),
                    amount=0.1,
                    referenceText="reference_transaction_1",
                    bankTransactionCode="dummy_transaction_code",
                ),
                SimpleTransaction(
                    transactionId="transaction_2",
                    datetime=datetime(2022, 2, 1),
                    amount=0.3,
                    referenceText="internal_reference_1",
                    bankTransactionCode="dummy_transaction_code",
                ),
                SimpleTransaction(
                    transactionId="transaction_3",
                    datetime=datetime(2022, 2, 6),
                    amount=-0.3,
                    referenceText="internal_reference_1",
                    bankTransactionCode="dummy_transaction_code",
                ),
            ],
            [
                SimpleTransaction(
                    transactionId="transaction_1",
                    datetime=datetime(2022, 2, 1),
                    amount=0.1,
                    referenceText="reference_transaction_1",
                    bankTransactionCode="dummy_transaction_code",
                ),
                SimpleTransaction(
                    transactionId="transaction_2",
                    datetime=datetime(2022, 2, 1),
                    amount=0.3,
                    referenceText="internal_reference_1",
                    bankTransactionCode="dummy_transaction_code",
                ),
                SimpleTransaction(
                    transactionId="transaction_3",
                    datetime=datetime(2022, 2, 6),
                    amount=-0.3,
                    referenceText="internal_reference_1",
                    bankTransactionCode="dummy_transaction_code",
                ),
            ],
        ),
        (
            [
                SimpleTransaction(
                    transactionId="transaction_1",
                    datetime=datetime(2022, 2, 1),
                    amount=0.1,
                    referenceText="reference_transaction_1",
                    bankTransactionCode="dummy_transaction_code",
                ),
                SimpleTransaction(
                    transactionId="transaction_2",
                    datetime=datetime(2022, 2, 1),
                    amount=0,
                    referenceText="internal_reference_1",
                    bankTransactionCode="dummy_transaction_code",
                ),
                SimpleTransaction(
                    transactionId="transaction_3",
                    datetime=datetime(2022, 2, 1),
                    amount=-0.3,
                    referenceText="internal_reference_1",
                    bankTransactionCode="dummy_transaction_code",
                ),
            ],
            [
                SimpleTransaction(
                    transactionId="transaction_1",
                    datetime=datetime(2022, 2, 1),
                    amount=0.1,
                    referenceText="reference_transaction_1",
                    bankTransactionCode="dummy_transaction_code",
                ),
                SimpleTransaction(
                    transactionId="transaction_2",
                    datetime=datetime(2022, 2, 1),
                    amount=0,
                    referenceText="internal_reference_1",
                    bankTransactionCode="dummy_transaction_code",
                ),
                SimpleTransaction(
                    transactionId="transaction_3",
                    datetime=datetime(2022, 2, 1),
                    amount=-0.3,
                    referenceText="internal_reference_1",
                    bankTransactionCode="dummy_transaction_code",
                ),
            ],
        ),
        (
            [
                SimpleTransaction(
                    transactionId="transaction_1",
                    datetime=datetime(2022, 2, 1),
                    amount=0.1,
                    referenceText="reference_transaction_1",
                    bankTransactionCode="dummy_transaction_code",
                ),
                SimpleTransaction(
                    transactionId="transaction_2",
                    datetime=datetime(2022, 2, 1),
                    amount=0.3,
                    referenceText="internal_reference_1",
                    bankTransactionCode="dummy_transaction_code",
                ),
                SimpleTransaction(
                    transactionId="transaction_3",
                    datetime=datetime(2022, 2, 1),
                    amount=-0.3,
                    referenceText="internal_reference_1",
                    bankTransactionCode="dummy_transaction_code",
                ),
                SimpleTransaction(
                    transactionId="transaction_4",
                    datetime=datetime(2022, 2, 1),
                    amount=-0.3,
                    referenceText="internal_reference_1",
                    bankTransactionCode="dummy_transaction_code",
                ),
            ],
            [
                SimpleTransaction(
                    transactionId="transaction_1",
                    datetime=datetime(2022, 2, 1),
                    amount=0.1,
                    referenceText="reference_transaction_1",
                    bankTransactionCode="dummy_transaction_code",
                ),
            ],
        ),
    ],
)
def test_internal_transfers(
    raw_transactions: List[SimpleTransaction],
    clean_transactions: List[SimpleTransaction],
) -> None:
    assert remove_internal_transfers(raw_transactions) == clean_transactions
