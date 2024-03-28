from datetime import datetime
from typing import List, Any, Callable, Iterable
from .definition import SimpleTransaction


def _filter_by_property_range(
    start: Any, end: Any, entry_property: Callable, collection: Iterable
) -> List:
    return [
        item
        for item in collection
        if entry_property(item) >= start and entry_property(item) <= end
    ]


def transaction_datetime_filter(
    start: datetime, end: datetime, transactions: List[SimpleTransaction]
) -> List[SimpleTransaction]:
    if start > end:
        raise ValueError("Start date cannot be greater than end date")

    return _filter_by_property_range(
        start, end, lambda transaction: transaction["datetime"], transactions
    )
