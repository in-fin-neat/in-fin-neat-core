import json
from typing import Dict, List, Callable
from functools import reduce
from nordigen_helper import (
    get_amount,
    get_reference,
)
from transaction_grouping import group_transactions, TransactionGroupingType
from transaction_cleaning import remove_internal_transfers
from transaction_type import (
    get_expense_transactions,
    get_income_transactions,
    get_unknown_type_transactions,
)
from custom_categories import get_category


def _sum_amount_by(
    transactions_to_be_summed: List[Dict],
    *,
    key: Callable,
    add_dict: Callable = lambda _: {},
):
    return list(
        map(
            lambda entry: entry[1],
            sorted(
                reduce(
                    lambda amount_per_key, transaction: {
                        **amount_per_key,
                        key(transaction): {
                            **add_dict(transaction),
                            "amount": amount_per_key[key(transaction)]["amount"]
                            + get_amount(transaction),
                            "references": amount_per_key[key(transaction)]["references"]
                            + [get_reference(transaction)],
                        },
                    },
                    transactions_to_be_summed,
                    {
                        key(transaction): {"amount": 0, "references": []}
                        for transaction in transactions_to_be_summed
                    },
                ).items(),
                key=lambda entry: entry[1]["amount"],
            ),
        )
    )


def write_aggregated_amounts(transactions: List[Dict], file_prefix: str):
    transactions, group_references = group_transactions(
        transactions, TransactionGroupingType.ReferenceSimilarity
    )

    transactions = list(
        map(
            lambda transaction: {
                **transaction,
                "customCategory": get_category(
                    "".join(group_references[transaction["groupNumber"]]),
                    fallback_reference=str(transaction["groupNumber"])
                ),
            },
            transactions,
        )
    )

    amount_per_group = _sum_amount_by(
        transactions,
        key=lambda transaction: transaction["groupNumber"],
        add_dict=lambda transaction: {"groupName": transaction["groupName"]},
    )
    amount_per_category = _sum_amount_by(
        transactions,
        key=lambda transaction: transaction["customCategory"],
        add_dict=lambda transaction: {"category": transaction["customCategory"]},
    )
    with open(f"{file_prefix}_per_group.json", "w") as o_file:
        o_file.write(json.dumps(amount_per_group, indent=4))

    with open(f"{file_prefix}_per_category.json", "w") as o_file:
        o_file.write(json.dumps(amount_per_category, indent=4))


with open("data/transactions.json", "r") as transactions_file:
    transactions = json.loads(transactions_file.read())

raw_transactions = transactions["pending"] + transactions["booked"]
transactions = remove_internal_transfers(raw_transactions)
income_transactions = get_income_transactions(transactions)
expense_transactions = get_expense_transactions(
    transactions
) + get_unknown_type_transactions(transactions)
write_aggregated_amounts(income_transactions, "data/income")
write_aggregated_amounts(expense_transactions, "data/expense")

total_income = reduce(
    lambda total, transaction: get_amount(transaction) + total, income_transactions, 0
)
total_expenses = reduce(
    lambda total, transaction: get_amount(transaction) + total, expense_transactions, 0
)
raw_balance = reduce(
    lambda total, transaction: get_amount(transaction) + total, raw_transactions, 0
)

print(
    f"""total_income: {total_income},
    total_expenses: {total_expenses},
    balance: {total_income + total_expenses}"""
)

print(f"raw_transaction_balance: {raw_balance}")
