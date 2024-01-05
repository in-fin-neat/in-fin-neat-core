from enum import Enum
from typing import List
from .definition import SimpleTransaction
from ..config import get_user_configuration


class TransactionType(Enum):
    INCOME = "INCOME"
    EXPENSE = "EXPENSE"
    UNKOWN = "UNKNOWN"


def get_transaction_type(transaction: SimpleTransaction) -> TransactionType:
    if is_income(transaction):
        return TransactionType.INCOME
    if is_expense(transaction):
        return TransactionType.EXPENSE
    return TransactionType.UNKOWN


def is_income(transaction: SimpleTransaction) -> bool:
    return transaction["amount"] > 0 and any(
        income_reference in transaction["referenceText"]
        for income_reference in get_user_configuration().IncomeReferences
    )


def is_expense(transaction: SimpleTransaction) -> bool:
    return (
        transaction["amount"] < 0
        and transaction["bankTransactionCode"]
        in get_user_configuration().ExpenseTransactionCodes
    )


def _filter_by_type(
    transactions: List[SimpleTransaction], transaction_type: TransactionType
) -> List[SimpleTransaction]:
    return [
        transaction
        for transaction in transactions
        if get_transaction_type(transaction) == transaction_type
    ]


def get_income_transactions(
    transactions: List[SimpleTransaction],
) -> List[SimpleTransaction]:
    return _filter_by_type(transactions, TransactionType.INCOME)


def get_expense_transactions(
    transactions: List[SimpleTransaction],
) -> List[SimpleTransaction]:
    return _filter_by_type(transactions, TransactionType.EXPENSE)


def get_unknown_type_transactions(
    transactions: List[SimpleTransaction],
) -> List[SimpleTransaction]:
    return _filter_by_type(transactions, TransactionType.UNKOWN)
