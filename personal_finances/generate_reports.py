import json
from datetime import datetime
from personal_finances.bank_interface.nordigen_adapter import as_simple_transaction
from personal_finances.transaction.grouping import (
    group_transactions,
    TransactionGroupingType,
    GroupedTransaction,
)
from personal_finances.transaction.cleaning import remove_internal_transfers
from personal_finances.transaction.filtering import transaction_datetime_filter
from personal_finances.transaction.processing import sum_amount_by, sum_amount
from personal_finances.transaction.type import (
    get_expense_transactions,
    get_income_transactions,
    get_unknown_type_transactions,
)
from personal_finances.transaction.definition import SimpleTransaction
from personal_finances.transaction.categorizing import get_category
from personal_finances.file_helper import write_json
from personal_finances.config import cache_user_configuration
from typing import List, Tuple, Callable, Any, Union, cast
from functools import partial
import dateutil.parser
import click
import logging


LOGGER = logging.getLogger(__name__)

ProcessorDataType = Union[Any, Tuple[Any, Any]]


class InvalidDatetime(Exception):
    pass


class InvalidDatetimeRange(Exception):
    pass


class CategorizedTransaction(GroupedTransaction):
    customCategory: str


def _add_group_category_field(
    transactions: List[SimpleTransaction],
) -> List[CategorizedTransaction]:
    grouped_transactions, group_references = group_transactions(
        transactions, TransactionGroupingType.ReferenceSimilarity
    )
    return list(
        map(
            lambda transaction: cast(
                CategorizedTransaction,
                {
                    **transaction,
                    "customCategory": get_category(
                        transaction["referenceText"],
                        group_references[transaction["groupNumber"]],
                        fallback_reference=transaction["groupName"],
                    ),
                },
            ),
            grouped_transactions,
        )
    )


def _split_by_type(transactions: List[SimpleTransaction]) -> Tuple[List, List]:
    income_transactions = get_income_transactions(transactions)

    # Treating unknown as expenses
    expense_transactions = get_expense_transactions(
        transactions
    ) + get_unknown_type_transactions(transactions)

    return income_transactions, expense_transactions


def _write_category_amounts(
    transactions: List[CategorizedTransaction], file_prefix: str
) -> None:
    amount_per_group = sum_amount_by(
        transactions,
        key=lambda transaction: cast(CategorizedTransaction, transaction)[
            "groupNumber"
        ],
        extra_key_context=lambda group_number: {
            "groupName": next(
                transaction["groupName"]
                for transaction in transactions
                if transaction["groupNumber"] == group_number
            )
        },
    )
    amount_per_category = sum_amount_by(
        transactions,
        key=lambda transaction: cast(CategorizedTransaction, transaction)[
            "customCategory"
        ],
    )
    group_file_path = f"{file_prefix}_per_group.json"
    category_file_path = f"{file_prefix}_per_category.json"
    categorized_transactions_file_path = f"{file_prefix}_categorized_transactions.json"
    write_json(group_file_path, amount_per_group)
    write_json(category_file_path, amount_per_category)
    write_json(
        categorized_transactions_file_path,
        transactions,
        json_converter=lambda dt_obj: dt_obj.isoformat(),
    )
    LOGGER.info(f"group amounts report written to: {group_file_path}")
    LOGGER.info(f"category amounts report written to: {category_file_path}")


def _write_balance(
    total_income: float,
    total_expense: float,
    start_time: datetime,
    end_time: datetime,
    file_prefix: str,
) -> None:
    file_path = f"{file_prefix}balance.json"
    write_json(
        file_path,
        {
            "start_time": start_time,
            "end_time": end_time,
            "total_income": total_income,
            "total_expense": total_expense,
            "total_balance": total_income + total_expense,
        },
    )
    LOGGER.info(f"balance report written to: {file_path}")


def _apply_processor(
    processor: Callable, processor_input: ProcessorDataType
) -> ProcessorDataType:
    if isinstance(processor_input, tuple):
        return tuple(map(processor, processor_input))
    return processor(processor_input)


def _process_transactions(
    transactions: List[SimpleTransaction], start_time: datetime, end_time: datetime
) -> Tuple[List[CategorizedTransaction], List[CategorizedTransaction]]:
    processors: List[Callable] = [
        remove_internal_transfers,
        partial(transaction_datetime_filter, start_time, end_time),
        _split_by_type,
        _add_group_category_field,
    ]

    processed_transactions: ProcessorDataType = transactions
    for processor in processors:
        processed_transactions = _apply_processor(processor, processed_transactions)

    # from _split_by_type return order
    income_transactions = processed_transactions[0]
    expense_transactions = processed_transactions[1]
    return income_transactions, expense_transactions


def _write_reports(
    transactions: List[SimpleTransaction], start_time: datetime, end_time: datetime
) -> None:
    (
        income_transactions,
        expense_transactions,
    ) = _process_transactions(transactions, start_time, end_time)
    total_income = sum_amount(income_transactions)
    total_expense = sum_amount(expense_transactions)
    time_range = f"{start_time.isoformat()}_{end_time.isoformat()}"

    _write_balance(
        total_income=total_income,
        total_expense=total_expense,
        start_time=start_time,
        end_time=end_time,
        file_prefix=f"reports/{time_range}/",
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
@click.option(
    "-ucfp",
    "--user-config-file-path",
    default="config/user_config.yaml",
    help="File path of user configuration.",
)
def generate_reports(
    start_time: str,
    end_time: str,
    transactions_file_path: str,
    user_config_file_path: str,
) -> None:
    """Generates reports from transactions according to the time filter specified."""
    try:
        start_datetime = dateutil.parser.isoparse(start_time)
        end_datetime = dateutil.parser.isoparse(end_time)
    except ValueError as e:
        raise InvalidDatetime(e)

    if start_datetime > end_datetime:
        raise InvalidDatetimeRange(
            f"invalid input: start time {start_time} greater than end_time {end_time}"
        )

    cache_user_configuration(user_config_file_path)
    with open(transactions_file_path, "r") as transactions_file:
        transactions: List[SimpleTransaction] = list(
            map(
                as_simple_transaction,
                json.loads(transactions_file.read()),
            )
        )

    _write_reports(
        transactions,
        start_datetime,
        end_datetime,
    )
    LOGGER.info("finished reports")


if __name__ == "__main__":
    generate_reports()
