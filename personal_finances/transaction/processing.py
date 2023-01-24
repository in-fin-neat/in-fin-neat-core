from typing import Dict, List, Callable, Hashable, TypedDict, Any, NotRequired, Iterable
from functools import reduce
from .definition import SimpleTransaction


class ReferencesAmountByKey(TypedDict, total=False):
    amount: float
    references: List[str]
    key: NotRequired[Hashable]


EMPTY_AMOUNT_OBJECT: ReferencesAmountByKey = {"amount": 0.0, "references": []}


def _reduce_amount_and_references_by_key(
    transactions: Iterable[SimpleTransaction],
    key: Callable[[SimpleTransaction], Hashable],
) -> Dict[Hashable, ReferencesAmountByKey]:
    return reduce(
        lambda amount_per_key, transaction: {
            **amount_per_key,
            key(transaction): {
                "key": key(transaction),
                "amount": amount_per_key[key(transaction)]["amount"]
                + transaction["amount"],
                "references": amount_per_key[key(transaction)]["references"]
                + [transaction["referenceText"]],
            },
        },
        transactions,
        {key(transaction): EMPTY_AMOUNT_OBJECT for transaction in transactions},
    )


def sum_amount_by(
    transactions: Iterable[SimpleTransaction],
    *,
    key: Callable[[SimpleTransaction], Hashable],
    extra_key_context: Callable[[Hashable], Dict[str, Any]] = lambda _: {},
) -> List[Dict]:
    return list(
        map(
            lambda entry: {**entry[1], **extra_key_context(entry[0])},
            sorted(
                _reduce_amount_and_references_by_key(transactions, key).items(),
                key=lambda entry: entry[1]["amount"],
            ),
        )
    )


def sum_amount(transactions: Iterable[SimpleTransaction]) -> float:
    return reduce(
        lambda total, transaction: transaction["amount"] + total,
        transactions,
        0.0,
    )
