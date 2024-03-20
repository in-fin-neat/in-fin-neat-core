import pytest
from datetime import datetime, timedelta
from typing import List

from personal_finances.transaction.definition import SimpleTransaction
from personal_finances.transaction.filtering import transaction_datetime_filter

TEST_TRANSACTIONS_QTD_TO_GENERATE = 300
TEST_TRANSACTION_START_DATETIME = datetime(1994, 1, 2, 3, 4, 5)
TEST_TRANSACTION_END_DATETIME = TEST_TRANSACTION_START_DATETIME + timedelta(
    seconds=TEST_TRANSACTIONS_QTD_TO_GENERATE
)


def create_simple_transaction(index: int, datetime: datetime) -> SimpleTransaction:
    return SimpleTransaction(
        transactionId="transaction_" + str(index),
        datetime=datetime,
        amount=index,
        referenceText="reference_transaction",
        bankTransactionCode="dummy_transaction_code",
    )


def create_transactions_in_range(
    quantity: int, datetime_offset: datetime
) -> List[SimpleTransaction]:
    transactions = []
    for i in range(0, quantity):
        transaction_datetime = datetime_offset + timedelta(seconds=i)
        transactions.append(create_simple_transaction(i, transaction_datetime))
    return transactions


def assert_transaction_datetime_filter(
    start_datetime: datetime,
    end_datetime: datetime,
    transactions: List[SimpleTransaction],
    filtered_transactions: List[SimpleTransaction],
) -> None:
    assert (
        transaction_datetime_filter(start_datetime, end_datetime, transactions)
        == filtered_transactions
    )


def test_all_transactions_within_range_should_not_filter() -> None:
    transaction_list = create_transactions_in_range(
        TEST_TRANSACTIONS_QTD_TO_GENERATE, TEST_TRANSACTION_START_DATETIME
    )

    assert_transaction_datetime_filter(
        TEST_TRANSACTION_START_DATETIME,
        TEST_TRANSACTION_END_DATETIME,
        transaction_list,
        transaction_list,
    )


def test_all_transactions_without_range_should_return_empty() -> None:
    transaction_list = create_transactions_in_range(
        TEST_TRANSACTIONS_QTD_TO_GENERATE,
        TEST_TRANSACTION_END_DATETIME + timedelta(seconds=1),
    )

    assert_transaction_datetime_filter(
        TEST_TRANSACTION_START_DATETIME,
        TEST_TRANSACTION_END_DATETIME,
        transaction_list,
        [],
    )


def test_transactions_without_range_should_get_filtered() -> None:
    before_range_transactions = create_transactions_in_range(
        TEST_TRANSACTIONS_QTD_TO_GENERATE,
        TEST_TRANSACTION_START_DATETIME
        + timedelta(seconds=-TEST_TRANSACTIONS_QTD_TO_GENERATE),
    )
    within_range_transactions = create_transactions_in_range(
        TEST_TRANSACTIONS_QTD_TO_GENERATE,
        TEST_TRANSACTION_START_DATETIME,
    )
    after_range_transactions = create_transactions_in_range(
        TEST_TRANSACTIONS_QTD_TO_GENERATE,
        TEST_TRANSACTION_END_DATETIME + timedelta(seconds=1),
    )

    transaction_list = (
        before_range_transactions + within_range_transactions + after_range_transactions
    )

    assert_transaction_datetime_filter(
        TEST_TRANSACTION_START_DATETIME,
        TEST_TRANSACTION_END_DATETIME,
        transaction_list,
        within_range_transactions,
    )


def test_invalid_date_input_should_raise_exception() -> None:
    transaction_list = create_transactions_in_range(
        TEST_TRANSACTIONS_QTD_TO_GENERATE,
        TEST_TRANSACTION_START_DATETIME,
    )

    with pytest.raises(ValueError):
        transaction_datetime_filter(
            start=TEST_TRANSACTION_END_DATETIME,
            end=TEST_TRANSACTION_START_DATETIME,
            transactions=transaction_list,
        )


def test_invalid_transaction_list_input_should_raise_exception() -> None:
    with pytest.raises(ValueError):
        transaction_datetime_filter(
            start=TEST_TRANSACTION_START_DATETIME,
            end=TEST_TRANSACTION_END_DATETIME,
            transactions=[],
        )
