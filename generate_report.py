import json
from datetime import datetime
from transaction_grouping import group_transactions, TransactionGroupingType
from transaction_cleaning import remove_internal_transfers
from transaction_filtering import transaction_datetime_filter
from transaction_processing import sum_amount_by, sum_amount
from custom_categories import get_category
from transaction_type import (
    get_expense_transactions,
    get_income_transactions,
    get_unknown_type_transactions,
)
from typing import Dict, List, Tuple, Callable, Any, Union
from functools import partial
from file_helper import write_json


def _add_group_category_field(transactions: List[Dict]) -> List[Dict]:
    grouped_transactions, group_references = group_transactions(
        transactions, TransactionGroupingType.ReferenceSimilarity
    )
    return list(
        map(
            lambda transaction: {
                **transaction,
                "customCategory": get_category(
                    "".join(group_references[transaction["groupNumber"]]),
                    fallback_reference=str(transaction["groupNumber"]),
                ),
            },
            grouped_transactions,
        )
    )


def _split_by_type(transactions: List[Dict]) -> Tuple[List, List]:
    income_transactions = get_income_transactions(transactions)
    expense_transactions = get_expense_transactions(
        transactions
    ) + get_unknown_type_transactions(transactions)

    return income_transactions, expense_transactions


def _write_category_amounts(transactions: List[Dict], file_prefix: str):
    amount_per_group = sum_amount_by(
        transactions,
        key=lambda transaction: transaction["groupNumber"],
        add_dict=lambda transaction: {"groupName": transaction["groupName"]},
    )
    amount_per_category = sum_amount_by(
        transactions,
        key=lambda transaction: transaction["customCategory"],
        add_dict=lambda transaction: {"category": transaction["customCategory"]},
    )
    write_json(f"{file_prefix}_per_group.json", amount_per_group)
    write_json(f"{file_prefix}_per_category.json", amount_per_category)


def _write_balance(
    total_income: List[Dict],
    total_expense: List[Dict],
    context: Dict,
    file_prefix: str,
):
    write_json(
        f"{file_prefix}balance.json",
        {
            **context,
            "total_income": total_income,
            "total_expense": total_expense,
            "total_balance": total_income + total_expense,
        },
    )


def _apply_processor(processor: Callable, processor_input: Union[Tuple, Any]) -> Any:
    if isinstance(processor_input, tuple):
        return tuple(map(processor, processor_input))
    return processor(processor_input)


def _process_transactions(
    transactions: List[Dict], start_time: datetime, end_time: datetime
) -> List[Dict]:
    processors = [
        remove_internal_transfers,
        partial(transaction_datetime_filter, start_time, end_time),
        _split_by_type,
        _add_group_category_field,
    ]

    processed_transactions = transactions
    for processor in processors:
        processed_transactions = _apply_processor(processor, processed_transactions)

    # from _split_by_type return order
    income_transactions = processed_transactions[0]
    expense_transactions = processed_transactions[1]
    return income_transactions, expense_transactions


def write_reports(
    raw_transactions: List[Dict], start_time: datetime, end_time: datetime
):
    transactions = raw_transactions["booked"] + raw_transactions["pending"]
    (
        income_transactions,
        expense_transactions,
    ) = _process_transactions(transactions, start_time, end_time)
    total_income = sum_amount(income_transactions)
    total_expense = sum_amount(expense_transactions)
    time_range = f"{start_time.isoformat()}_{end_time.isoformat()}"

    _write_balance(
        total_income,
        total_expense,
        {"start_time": start_time.isoformat(), "end_time": end_time.isoformat()},
        f"reports/{time_range}/",
    )
    _write_category_amounts(income_transactions, f"reports/{time_range}/income")
    _write_category_amounts(expense_transactions, f"reports/{time_range}/expense")


with open("data/transactions.json", "r") as transactions_file:
    raw_transactions = json.loads(transactions_file.read())

write_reports(
    raw_transactions,
    datetime(year=2022, month=11, day=1),
    datetime(year=2022, month=11, day=30, hour=23, minute=59, second=59),
)

print("reports written")
