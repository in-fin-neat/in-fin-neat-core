from typing import Dict, List, Callable
from functools import reduce
from nordigen_helper import (
    get_amount,
    get_reference,
)


def sum_amount_by(
    transactions: List[Dict],
    *,
    key: Callable,
    add_dict: Callable = lambda _: {},
) -> List[Dict]:
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
                    transactions,
                    {
                        key(transaction): {"amount": 0, "references": []}
                        for transaction in transactions
                    },
                ).items(),
                key=lambda entry: entry[1]["amount"],
            ),
        )
    )


def sum_amount(transactions: List[Dict]) -> float:
    return reduce(
        lambda total, transaction: get_amount(transaction) + total,
        transactions,
        0,
    )
