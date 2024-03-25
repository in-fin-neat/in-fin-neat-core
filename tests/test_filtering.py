import pytest
from datetime import datetime, timedelta
from typing import List

from personal_finances.transaction.definition import SimpleTransaction
from personal_finances.transaction.filtering import transaction_datetime_filter

TEST_START_DATETIME = datetime(1994, 1, 2, 3, 4, 5)
TEST_END_DATETIME = datetime(1994, 1, 2, 3, 4, 7)


def create_transaction(index: int, datetime: datetime) -> SimpleTransaction:
    return SimpleTransaction(
        transactionId="transaction_" + str(index),
        datetime=datetime,
        amount=index,
        referenceText="reference_transaction",
        bankTransactionCode="dummy_transaction_code",
    )


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


def test_empty_transaction_list_input() -> None:
    assert_transaction_datetime_filter(
        TEST_START_DATETIME,
        TEST_END_DATETIME,
        [],
        [],
    )


def test_transactions_datetime_filter() -> None:
    start_st = TEST_START_DATETIME
    end_st = TEST_END_DATETIME
    within_range_list = []
    outside_range_list = []

    within_range_list.append(create_transaction(1, start_st))
    within_range_list.append(create_transaction(2, start_st + timedelta(seconds=1)))
    within_range_list.append(create_transaction(3, end_st - timedelta(seconds=1)))
    within_range_list.append(create_transaction(4, end_st))

    outside_range_list.append(create_transaction(5, start_st - timedelta(seconds=1)))
    outside_range_list.append(create_transaction(6, end_st + timedelta(seconds=1)))

    assert_transaction_datetime_filter(
        start_st,
        end_st,
        within_range_list + outside_range_list,
        within_range_list,
    )


def test_invalid_datetime_input_should_raise_exception() -> None:
    transaction_list = [create_transaction(1, TEST_START_DATETIME)]

    with pytest.raises(ValueError):
        transaction_datetime_filter(
            start=TEST_END_DATETIME,
            end=TEST_START_DATETIME,
            transactions=transaction_list,
        )
