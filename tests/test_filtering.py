import pytest
from datetime import datetime
from typing import List

from personal_finances.transaction.definition import SimpleTransaction
from personal_finances.transaction.filtering import transaction_datetime_filter


@pytest.mark.parametrize(
    "start_datetime, end_datetime, transactions, filtered_transactions",
    [
        (0, 0, [], []),
        (
            datetime(2022, 2, 1, 0, 0, 0),
            datetime(2022, 2, 1, 0, 0, 2),
            [
                SimpleTransaction(
                    transactionId="transaction_1",
                    datetime=datetime(2022, 2, 1, 0, 0, 0),
                    amount=0.1,
                    referenceText="reference_transaction",
                    bankTransactionCode="dummy_transaction_code",
                ),
                SimpleTransaction(
                    transactionId="transaction_2",
                    datetime=datetime(2022, 2, 1, 0, 0, 1),
                    amount=0.2,
                    referenceText="reference_transaction",
                    bankTransactionCode="dummy_transaction_code",
                ),
                SimpleTransaction(
                    transactionId="transaction_3",
                    datetime=datetime(2022, 2, 1, 0, 0, 2),
                    amount=0.3,
                    referenceText="reference_transaction",
                    bankTransactionCode="dummy_transaction_code",
                ),
            ],
            [
                SimpleTransaction(
                    transactionId="transaction_1",
                    datetime=datetime(2022, 2, 1, 0, 0, 0),
                    amount=0.1,
                    referenceText="reference_transaction",
                    bankTransactionCode="dummy_transaction_code",
                ),
                SimpleTransaction(
                    transactionId="transaction_2",
                    datetime=datetime(2022, 2, 1, 0, 0, 1),
                    amount=0.2,
                    referenceText="reference_transaction",
                    bankTransactionCode="dummy_transaction_code",
                ),
                SimpleTransaction(
                    transactionId="transaction_3",
                    datetime=datetime(2022, 2, 1, 0, 0, 2),
                    amount=0.3,
                    referenceText="reference_transaction",
                    bankTransactionCode="dummy_transaction_code",
                ),
            ],
        ),
        (
            datetime(2022, 2, 1, 0, 0, 0),
            datetime(2022, 2, 1, 0, 0, 1),
            [
                SimpleTransaction(
                    transactionId="transaction_1",
                    datetime=datetime(2022, 2, 1, 0, 0, 0),
                    amount=0.1,
                    referenceText="reference_transaction",
                    bankTransactionCode="dummy_transaction_code",
                ),
                SimpleTransaction(
                    transactionId="transaction_2",
                    datetime=datetime(2022, 2, 1, 0, 0, 1),
                    amount=0.2,
                    referenceText="reference_transaction",
                    bankTransactionCode="dummy_transaction_code",
                ),
                SimpleTransaction(
                    transactionId="transaction_3",
                    datetime=datetime(2022, 2, 1, 0, 0, 2),
                    amount=0.3,
                    referenceText="reference_transaction",
                    bankTransactionCode="dummy_transaction_code",
                ),
            ],
            [
                SimpleTransaction(
                    transactionId="transaction_1",
                    datetime=datetime(2022, 2, 1, 0, 0, 0),
                    amount=0.1,
                    referenceText="reference_transaction",
                    bankTransactionCode="dummy_transaction_code",
                ),
                SimpleTransaction(
                    transactionId="transaction_2",
                    datetime=datetime(2022, 2, 1, 0, 0, 1),
                    amount=0.2,
                    referenceText="reference_transaction",
                    bankTransactionCode="dummy_transaction_code",
                ),
            ],
        ),
        (
            datetime(2022, 2, 1, 0, 0, 1),
            datetime(2022, 2, 1, 0, 0, 2),
            [
                SimpleTransaction(
                    transactionId="transaction_1",
                    datetime=datetime(2022, 2, 1, 0, 0, 0),
                    amount=0.1,
                    referenceText="reference_transaction",
                    bankTransactionCode="dummy_transaction_code",
                ),
                SimpleTransaction(
                    transactionId="transaction_2",
                    datetime=datetime(2022, 2, 1, 0, 0, 1),
                    amount=0.2,
                    referenceText="reference_transaction",
                    bankTransactionCode="dummy_transaction_code",
                ),
                SimpleTransaction(
                    transactionId="transaction_3",
                    datetime=datetime(2022, 2, 1, 0, 0, 2),
                    amount=0.3,
                    referenceText="reference_transaction",
                    bankTransactionCode="dummy_transaction_code",
                ),
            ],
            [
                SimpleTransaction(
                    transactionId="transaction_2",
                    datetime=datetime(2022, 2, 1, 0, 0, 1),
                    amount=0.2,
                    referenceText="reference_transaction",
                    bankTransactionCode="dummy_transaction_code",
                ),
                SimpleTransaction(
                    transactionId="transaction_3",
                    datetime=datetime(2022, 2, 1, 0, 0, 2),
                    amount=0.3,
                    referenceText="reference_transaction",
                    bankTransactionCode="dummy_transaction_code",
                ),
            ],
        ),
    ],
)
def test_transaction_datetime_filter(
    start_datetime: datetime,
    end_datetime: datetime,
    transactions: List[SimpleTransaction],
    filtered_transactions: List[SimpleTransaction],
) -> None:
    assert (
        transaction_datetime_filter(start_datetime, end_datetime, transactions)
        == filtered_transactions
    )
