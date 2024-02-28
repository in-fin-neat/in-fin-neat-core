from unittest.mock import Mock, patch
import pytest
from typing import List, Generator
from personal_finances.transaction.cleaning import remove_internal_transfers
from personal_finances.transaction.definition import SimpleTransaction
from datetime import datetime, timedelta
from copy import deepcopy

BANK_PROCESSING_TIME_IN_DAYS = 5

INTERNAL_TRANSFER_REFERENCES = [
    "internal reference 0",
    "internal reference 1",
]

NO_INTERNAL_TRANSFER_LIST = [
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

INTERNAL_TRANSFER_LIST = [
    SimpleTransaction(
        transactionId="transaction_internal_transfer_1",
        datetime=datetime.now(),
        amount=0.3,
        referenceText="dummy noise"
        + INTERNAL_TRANSFER_REFERENCES[0]
        + "data dummy data dummy",
        bankTransactionCode="dummy_transaction_code",
    ),
    SimpleTransaction(
        transactionId="transaction_internal_transfer_2",
        datetime=datetime.now(),
        amount=-0.3,
        referenceText="dummy noise"
        + INTERNAL_TRANSFER_REFERENCES[0]
        + "data dummy data dummy",
        bankTransactionCode="dummy_transaction_code",
    ),
    SimpleTransaction(
        transactionId="transaction_internal_transfer_3",
        datetime=datetime.now(),
        amount=98321.12798,
        referenceText="dummy noise dummy noise"
        + INTERNAL_TRANSFER_REFERENCES[1]
        + "data dummy data dummy",
        bankTransactionCode="dummy_transaction_code",
    ),
    SimpleTransaction(
        transactionId="transaction_internal_transfer_4",
        datetime=datetime.now(),
        amount=-98321.12798,
        referenceText="dummy dummy dummy test noise"
        + INTERNAL_TRANSFER_REFERENCES[1]
        + "data dummy data dummy",
        bankTransactionCode="dummy_transaction_code",
    ),
    SimpleTransaction(
        transactionId="transaction_internal_transfer_5",
        datetime=datetime.now(),
        amount=10,
        referenceText="dummy noise"
        + INTERNAL_TRANSFER_REFERENCES[0]
        + "data dummy data dummy",
        bankTransactionCode="dummy_transaction_code",
    ),
    SimpleTransaction(
        transactionId="transaction_internal_transfer_6",
        datetime=datetime.now(),
        amount=-10,
        referenceText="dummy dummy dummy test noise"
        + INTERNAL_TRANSFER_REFERENCES[1]
        + "data dummy data dummy",
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


def assert_transaction_list(
    input_transaction_list: List[SimpleTransaction],
    expected_cleaned_list: List[SimpleTransaction],
) -> None:
    assert remove_internal_transfers(input_transaction_list) == expected_cleaned_list


def test_list_without_internal_transfer_should_get_untouched() -> None:
    assert_transaction_list(NO_INTERNAL_TRANSFER_LIST, NO_INTERNAL_TRANSFER_LIST)


def test_list_with_internal_transfer_should_get_cleaned() -> None:
    one_internal_transaction = NO_INTERNAL_TRANSFER_LIST + INTERNAL_TRANSFER_LIST
    assert_transaction_list(one_internal_transaction, NO_INTERNAL_TRANSFER_LIST)


def test_list_with_internal_transfer_exceed_proccesing_time() -> None:
    exceed_day_pair = deepcopy(INTERNAL_TRANSFER_LIST[:2])
    exceed_day_pair[0]["datetime"] += timedelta(days=BANK_PROCESSING_TIME_IN_DAYS + 1)

    transaction_list = (
        NO_INTERNAL_TRANSFER_LIST + exceed_day_pair + INTERNAL_TRANSFER_LIST[2:]
    )
    expected_list = NO_INTERNAL_TRANSFER_LIST + exceed_day_pair
    assert_transaction_list(transaction_list, expected_list)


def test_list_with_zero_amount_in_internal_transfer() -> None:
    zero_amount_pair = deepcopy(INTERNAL_TRANSFER_LIST[:2])
    zero_amount_pair[0]["amount"] = 0

    transaction_list = (
        NO_INTERNAL_TRANSFER_LIST + zero_amount_pair + INTERNAL_TRANSFER_LIST[2:]
    )
    expected_list = NO_INTERNAL_TRANSFER_LIST + zero_amount_pair
    assert_transaction_list(transaction_list, expected_list)


def test_list_with_duplicated_internal_transfer_() -> None:
    duplicated_transfer = INTERNAL_TRANSFER_LIST + [INTERNAL_TRANSFER_LIST[0]]

    transaction_list = NO_INTERNAL_TRANSFER_LIST + duplicated_transfer
    expected_cleaned_list = NO_INTERNAL_TRANSFER_LIST + [INTERNAL_TRANSFER_LIST[0]]

    assert_transaction_list(transaction_list, expected_cleaned_list)


def test_list_with_invalid_internal_transfer() -> None:
    for key in INTERNAL_TRANSFER_LIST[0].keys():
        invalid_list = deepcopy(INTERNAL_TRANSFER_LIST)
        invalid_list[0][key] = None  # type: ignore[literal-required]
        transaction_list = NO_INTERNAL_TRANSFER_LIST + invalid_list
        try:
            remove_internal_transfers(transaction_list)
        except Exception as e:
            assert isinstance(e, TypeError)
        else:
            pytest.fail(
                "TypeError was expected but not raised by key '{0}'".format(key)
            )
