from enum import Enum
from typing import Dict, List
from nordigen_helper import (
    get_amount,
    get_proprietary_bank_transaction_code,
    get_reference,
)


EXPENSE_TRANSACTION_CODES = [
    "CARD_PAYMENT",
    "Mobile TopUp",
    "CARD_REFUND",
    "Direct Debt",
]
INCOME_TRANSACTION_CODES = ["Credit Transfer"]

INCOME_REFERENCES = [
    "irish manufacturing research",
    "amazon development centre ireland",
    "rent",
]


class TransactionType(Enum):
    INCOME = "INCOME"
    EXPENSE = "EXPENSE"
    UNKOWN = "UNKNOWN"


def get_transaction_type(transaction: Dict) -> TransactionType:
    if is_income(transaction):
        return TransactionType.INCOME
    if is_expense(transaction):
        return TransactionType.EXPENSE
    return TransactionType.UNKOWN


def is_income(transaction: Dict) -> bool:
    amount = get_amount(transaction)
    reference = get_reference(transaction)

    return amount > 0 and any(
        income_reference in reference for income_reference in INCOME_REFERENCES
    )


def is_expense(transaction: Dict) -> bool:
    amount = get_amount(transaction)
    transaction_code = get_proprietary_bank_transaction_code(transaction)
    return amount < 0 and transaction_code in EXPENSE_TRANSACTION_CODES


def _filter_by_type(
    transactions: List[Dict], transaction_type: TransactionType
) -> List[Dict]:
    return [
        transaction
        for transaction in transactions
        if get_transaction_type(transaction) == transaction_type
    ]


def get_income_transactions(transactions: List[Dict]) -> List[Dict]:
    return _filter_by_type(transactions, TransactionType.INCOME)


def get_expense_transactions(transactions: List[Dict]) -> List[Dict]:
    return _filter_by_type(transactions, TransactionType.EXPENSE)


def get_unknown_type_transactions(transactions: List[Dict]) -> List[Dict]:
    return _filter_by_type(transactions, TransactionType.UNKOWN)
