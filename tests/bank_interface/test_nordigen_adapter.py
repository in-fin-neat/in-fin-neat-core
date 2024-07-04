from typing import cast
from personal_finances.bank_interface.nordigen_adapter import (
    EMPTY_NORDIGEN_TRANSACTIONS,
    NordigenTransactions,
    concat_nordigen_transactions,
)


def test_concat_nordigen_transactions_double_empty() -> None:
    assert (
        concat_nordigen_transactions(
            EMPTY_NORDIGEN_TRANSACTIONS, EMPTY_NORDIGEN_TRANSACTIONS
        )
        == EMPTY_NORDIGEN_TRANSACTIONS
    )


def test_concat_nordigen_transactions_left_empty() -> None:
    simple_transactions = {"booked": ["fake-tr1"], "pending": ["fake-tr2"]}
    assert concat_nordigen_transactions(
        EMPTY_NORDIGEN_TRANSACTIONS, cast(NordigenTransactions, simple_transactions)
    ) == cast(NordigenTransactions, simple_transactions)


def test_concat_nordigen_transactions_right_empty() -> None:
    simple_transactions = {"booked": ["fake-tr1"], "pending": ["fake-tr2"]}
    assert concat_nordigen_transactions(
        cast(NordigenTransactions, simple_transactions),
        EMPTY_NORDIGEN_TRANSACTIONS,
    ) == cast(NordigenTransactions, simple_transactions)


def test_concat_nordigen_transactions() -> None:
    simple_transactions = {"booked": ["tr1"], "pending": ["tr2"]}
    another_transactions = {"booked": ["tr3"], "pending": ["tr4"]}
    expected_nordigen_transactions = {
        "booked": ["tr3", "tr1"],
        "pending": ["tr4", "tr2"],
    }
    assert concat_nordigen_transactions(
        cast(NordigenTransactions, another_transactions),
        cast(NordigenTransactions, simple_transactions),
    ) == cast(NordigenTransactions, expected_nordigen_transactions)
