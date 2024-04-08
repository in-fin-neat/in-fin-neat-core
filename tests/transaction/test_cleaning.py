from unittest.mock import Mock, patch
from typing import List, Generator, Optional
from personal_finances.transaction.cleaning import remove_internal_transfers
from personal_finances.transaction.definition import SimpleTransaction
from datetime import datetime, timedelta
import random
import pytest
from copy import deepcopy

BANK_PROCESSING_TIME_IN_DAYS = 5

INTERNAL_TRANSFER_REFERENCES = [
    "internal reference 0",
    "internal reference 1",
]

REGULAR_TRANSACTIONS_LIST = [
    SimpleTransaction(
        transactionId="transaction_dummy_1",
        datetime=datetime.now(),
        amount=0.1,
        referenceText="reference_transaction_dummy_1",
        bankTransactionCode="dummy_transaction_code",
    ),
    SimpleTransaction(
        transactionId="transaction_dummy_2",
        datetime=datetime.now(),
        amount=0.2,
        referenceText="reference_transaction_dummy_2",
        bankTransactionCode="dummy_transaction_code",
    ),
]


@pytest.fixture(autouse=True)
def user_config_mock() -> Generator[Mock, None, None]:
    with patch(
        "personal_finances.transaction.cleaning.get_user_configuration"
    ) as u_mock:
        u_mock.return_value.InternalTransferReferences = INTERNAL_TRANSFER_REFERENCES
        u_mock.return_value.BankProcessingTimeInDays = BANK_PROCESSING_TIME_IN_DAYS
        yield u_mock


def create_pair_internal_transaction(
    amount: Optional[float] = None,
) -> List[SimpleTransaction]:
    transfer_amount = random.random() if amount is None else amount
    transfer_datetime = datetime.now()

    internal_trasaction_pair = [
        SimpleTransaction(
            transactionId=str(random.random()),
            datetime=transfer_datetime,
            amount=transfer_amount,
            referenceText="dummy noise"
            + INTERNAL_TRANSFER_REFERENCES[0]
            + "data dummy data dummy",
            bankTransactionCode="dummy_transaction_code",
        ),
        SimpleTransaction(
            transactionId=str(random.random()),
            datetime=transfer_datetime,
            amount=-transfer_amount,
            referenceText="dummy noise"
            + INTERNAL_TRANSFER_REFERENCES[1]
            + "data dummy data dummy",
            bankTransactionCode="dummy_transaction_code",
        ),
    ]
    return internal_trasaction_pair


def create_list_with_internal_transactions(
    amount: Optional[float] = None,
) -> List[SimpleTransaction]:
    return (
        create_pair_internal_transaction(amount)
        + create_pair_internal_transaction(amount)
        + create_pair_internal_transaction(amount)
    )


def copy_first_element(
    internal_transfer_pair: List[SimpleTransaction],
) -> SimpleTransaction:
    duplicated_transfer_element = deepcopy(internal_transfer_pair[0])
    duplicated_transfer_element["transactionId"] = str(random.random())

    return duplicated_transfer_element


def assert_transaction_list(
    input_transaction_list: List[SimpleTransaction],
    expected_cleaned_list: List[SimpleTransaction],
) -> None:
    assert remove_internal_transfers(input_transaction_list) == expected_cleaned_list


def test_empty_list() -> None:
    """
    Validates if an empty input list return an empty output list.
    """
    assert_transaction_list([], [])


def test_list_without_internal_transfer_should_get_untouched() -> None:
    """
    Validates that a list of transactions without internal transfers
    remains unchanged after processing.
    """
    assert_transaction_list(REGULAR_TRANSACTIONS_LIST, REGULAR_TRANSACTIONS_LIST)


def test_list_with_internal_transfer_should_get_cleaned() -> None:
    """
    Tests whether the remove_internal_transfers function correctly identifies
    and removes internal transfer transactions from a list that includes both
    regular and internal transfer transactions.
    """
    one_internal_transaction = (
        REGULAR_TRANSACTIONS_LIST + create_list_with_internal_transactions()
    )

    assert_transaction_list(one_internal_transaction, REGULAR_TRANSACTIONS_LIST)


def test_list_with_internal_transfer_exceed_proccesing_time() -> None:
    """
    Checks if the remove_internal_transfers function properly handles
    internal transfers that exceed the bank processing time. It ensures
    that transactions are not considered internal transfers if the time
    difference between them is greater than the bank's processing time limit
    """
    transaction_edited_datetime = create_pair_internal_transaction()
    transaction_edited_datetime[0]["datetime"] += timedelta(
        days=BANK_PROCESSING_TIME_IN_DAYS + 1
    )

    transaction_list = REGULAR_TRANSACTIONS_LIST + transaction_edited_datetime

    assert_transaction_list(transaction_list, transaction_list)


def test_list_with_zero_amount_in_internal_transfer() -> None:
    """
    Verifies that transactions with a zero amount are not treated
    as internal transfers.
    """
    transaction_edited_ammount = create_pair_internal_transaction()
    transaction_edited_ammount[0]["amount"] = 0

    transaction_list = REGULAR_TRANSACTIONS_LIST + transaction_edited_ammount
    assert_transaction_list(transaction_list, transaction_list)


def test_list_with_duplicated_internal_transfer_one_element() -> None:
    """
    Assesses the handling of duplicated transactions in a list that includes
    internal transfers. It tests whether remove_internal_transfers can correctly
    identify and process a list with one element of an internal transfer pair
    duplicated.
    """
    pair_internal_transaction = create_pair_internal_transaction()
    duplicated_element = copy_first_element(pair_internal_transaction)

    transaction_list = (
        REGULAR_TRANSACTIONS_LIST + pair_internal_transaction + [duplicated_element]
    )

    expected_cleaned_list = REGULAR_TRANSACTIONS_LIST + [duplicated_element]

    assert_transaction_list(transaction_list, expected_cleaned_list)


def test_list_with_internal_transfer_with_same_ammount() -> None:
    """
    Tests the function's ability to handle multiple internal transfer
    transactions with the same amount. It verifies that remove_internal_transfers
    correctly identifies and removes all internal transfer transactions when
    they have identical amounts.
    """
    same_amount_internal_transfers = create_list_with_internal_transactions(amount=3)

    transaction_list = REGULAR_TRANSACTIONS_LIST + same_amount_internal_transfers
    expected_cleaned_list = REGULAR_TRANSACTIONS_LIST

    assert_transaction_list(transaction_list, expected_cleaned_list)


def test_raising_error_at_get_user_config(user_config_mock: Mock) -> None:
    """
    Checks the behavior when get_user_configuration raises a exception.
    It ensures that the exception is propagated and not silently ignored
    during the execution.
    """
    one_internal_transaction = (
        REGULAR_TRANSACTIONS_LIST + create_list_with_internal_transactions()
    )

    user_config_mock.side_effect = [KeyError, user_config_mock.return_value]
    with pytest.raises(KeyError):
        assert_transaction_list(one_internal_transaction, REGULAR_TRANSACTIONS_LIST)

    user_config_mock.side_effect = [user_config_mock.return_value, OSError]
    with pytest.raises(OSError):
        assert_transaction_list(one_internal_transaction, REGULAR_TRANSACTIONS_LIST)
