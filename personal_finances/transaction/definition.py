from typing import TypedDict
from datetime import datetime


class SimpleTransaction(TypedDict):
    transactionId: str
    datetime: datetime
    amount: float
    referenceText: str
    bankTransactionCode: str
