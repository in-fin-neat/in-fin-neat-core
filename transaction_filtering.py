from datetime import datetime
from typing import List, Dict, Any, Callable
from .nordigen_helper import get_datetime


def _filter_by_property_range(
    start: Any, end: Any, entry_property: Callable, transactions
):
    return [
        transaction
        for transaction in transactions
        if entry_property(transaction) >= start and entry_property(transaction) <= end
    ]


def transaction_datetime_filter(
    start: datetime, end: datetime, transactions: List[Dict]
) -> List[Dict]:
    return _filter_by_property_range(
        start, end, lambda transaction: get_datetime(transaction), transactions
    )
