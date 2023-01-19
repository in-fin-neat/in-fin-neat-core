import json
from datetime import datetime
from transaction_grouping import group_transactions, TransactionGroupingType
from transaction_cleaning import remove_internal_transfers
from transaction_filtering import transaction_datetime_filter
from transaction_processing import sum_amount_by, sum_amount
from nordigen_helper import get_reference
from custom_categories import get_category
from transaction_type import (
    get_expense_transactions,
    get_income_transactions,
    get_unknown_type_transactions,
)
from typing import Dict, List, Tuple, Callable, Any, Union
from functools import partial
from file_helper import write_json
import dateutil
import click
import logging


LOGGER = logging.getLogger(__name__)
LOGGER.info = print


def _add_group_category_field(transactions: List[Dict]) -> List[Dict]:
    grouped_transactions, group_references = group_transactions(
        transactions, TransactionGroupingType.ReferenceSimilarity
    )
    return list(
        map(
            lambda transaction: {
                **transaction,
                "customCategory": get_category(
                    get_reference(transaction),
                    group_references[transaction["groupNumber"]],
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
    group_file_path = f"{file_prefix}_per_group.json"
    category_file_path = f"{file_prefix}_per_category.json"
    write_json(group_file_path, amount_per_group)
    write_json(category_file_path, amount_per_category)
    LOGGER.info(f"group amounts report written to: {group_file_path}")
    LOGGER.info(f"category amounts report written to: {category_file_path}")


def _write_balance(
    total_income: List[Dict],
    total_expense: List[Dict],
    context: Dict,
    file_prefix: str,
):

    file_path = f"{file_prefix}balance.json"
    write_json(
        file_path,
        {
            **context,
            "total_income": total_income,
            "total_expense": total_expense,
            "total_balance": total_income + total_expense,
        },
    )
    LOGGER.info(f"balance report written to: {file_path}")


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
    transactions: List[Dict], start_time: datetime, end_time: datetime
):
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


@click.command()
@click.option(
    "-st",
    "--start-time",
    default="1970-01-01T00:00:00Z",
    help="Start time of transactions filter in ISO 8061 format.",
)
@click.option(
    "-et",
    "--end-time",
    default="2100-01-01T00:00:00Z",
    help="End time of transactions filter in ISO 8061 format.",
)
@click.option(
    "-tfp",
    "--transactions-file-path",
    default="data/merged_transactions.json",
    help="File path of transactions fetched previously.",
)
def generate_reports(start_time: str, end_time: str, transactions_file_path: str):
    """Generates reports from transactions according to the time filter specified."""
    with open(transactions_file_path, "r") as transactions_file:
        transactions = json.loads(transactions_file.read())

    write_reports(
        transactions,
        dateutil.parser.isoparse(start_time),
        dateutil.parser.isoparse(end_time),
    )
    LOGGER.info("finished reports")


if __name__ == "__main__":
    generate_reports()