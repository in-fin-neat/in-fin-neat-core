import json
from typing import Dict, List, Callable
from functools import reduce
from nordigen_helper import (
    get_amount,
    get_reference,
)
from transaction_grouping import get_reference_groups, TransactionGroupingType
from transaction_cleaning import remove_internal_transfers
from custom_categories import get_category


def _sum_amount_by(key: Callable, transactions_to_be_summed: List[Dict]):
    return list(map(lambda entry: entry[1], sorted(
        reduce(
            lambda amount_per_key, transaction: {
                **amount_per_key,
                key(transaction): {
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
    )))


def _add_reference_groups():
    pass


with open("data/transactions.json", "r") as transactions_file:
    transactions = json.loads(transactions_file.read())


transactions = transactions["pending"] + transactions["booked"]
transactions = remove_internal_transfers(transactions)
groups, group_reference = get_reference_groups(
    transactions, TransactionGroupingType.ReferenceSimilarity
)
transactions = list(
    map(
        lambda transaction: {
            **transaction,
            "groupName": group_reference[get_reference(transaction)]["groupName"],
            "groupNumber": group_reference[get_reference(transaction)]["groupNumber"],
        },
        transactions,
    )
)
transactions = list(
    map(
        lambda transaction: {
            **transaction,
            "groupName": group_reference[get_reference(transaction)]["groupName"],
            "groupNumber": group_reference[get_reference(transaction)]["groupNumber"],
            "customCategory": get_category(get_reference(transaction)),
        },
        transactions,
    )
)
amount_per_group = _sum_amount_by(
    lambda transaction: transaction["groupNumber"], transactions
)
amount_per_category = _sum_amount_by(
    lambda transaction: transaction["customCategory"], transactions
)

with open("data/amount_per_group.json", "w") as o_file:
    o_file.write(json.dumps(amount_per_group))

with open("data/amount_per_category.json", "w") as o_file:
    o_file.write(json.dumps(amount_per_category))
