from datetime import datetime
import dateutil.parser
from dateutil.tz import tzutc
import uuid
from typing import List, Any, TypedDict, NotRequired
from ..transaction.definition import SimpleTransaction


INVALID_REFERENCES: List[Any] = ["", "-", None, []]


class TransactionAmount(TypedDict):
    amount: float
    currency: str


class NordigenTransaction(TypedDict):
    # Either bookingDatetime or bookingDate
    bookingDatetime: NotRequired[str]
    bookingDate: NotRequired[str]
    internalTransactionId: NotRequired[str]
    transactionAmount: TransactionAmount
    transactionId: NotRequired[str]
    creditorName: NotRequired[str]
    debtorName: NotRequired[str]
    remittanceInformationUnstructured: NotRequired[str]
    remittanceInformationUnstructuredArray: NotRequired[List[str]]
    merchantCategoryCode: NotRequired[str]
    proprietaryBankTransactionCode: NotRequired[str]


class NordigenTransactions(TypedDict):
    booked: List[NordigenTransaction]
    pending: List[NordigenTransaction]


EMPTY_NORDIGEN_TRANSACTIONS: NordigenTransactions = {"booked": [], "pending": []}


def concat_nordigen_transactions(
    first: NordigenTransactions, second: NordigenTransactions
) -> NordigenTransactions:
    return {
        "booked": first["booked"] + second["booked"],
        "pending": first["pending"] + second["pending"],
    }


def as_simple_transaction(transaction: NordigenTransaction) -> SimpleTransaction:
    return {
        "transactionId": get_id(transaction),
        "datetime": get_datetime(transaction),
        "amount": get_amount(transaction),
        "referenceText": get_reference(transaction),
        "bankTransactionCode": get_proprietary_bank_transaction_code(transaction),
    }


def get_datetime(transaction: NordigenTransaction) -> datetime:
    if "bookingDatetime" in transaction:
        return dateutil.parser.isoparse(transaction["bookingDatetime"])

    if "bookingDate" in transaction:
        booking_date = dateutil.parser.parse(transaction["bookingDate"])
        return booking_date.replace(tzinfo=booking_date.tzinfo or tzutc())

    raise Exception(f"no sort datetime found! {transaction}")


def get_amount(transaction: NordigenTransaction) -> float:
    return float(transaction["transactionAmount"]["amount"])


def get_currency(transaction: NordigenTransaction) -> str:
    return transaction["transactionAmount"]["currency"]


def _get_internal_transaction_id(transaction: NordigenTransaction) -> str:
    if "internalTransactionId" in transaction:
        return transaction["internalTransactionId"]
    return str(uuid.uuid4())


def get_id(transaction: NordigenTransaction) -> str:
    if "transactionId" not in transaction:
        return str(
            uuid.uuid5(
                uuid.UUID("29fff09d-93fa-49d2-a902-eb39f25ba953"),
                _get_internal_transaction_id(transaction)
                + str(get_amount(transaction))
                + str(get_currency(transaction)),
            )
        )

    return transaction["transactionId"]


def get_reference(transaction: NordigenTransaction) -> str:
    reference_keys = {
        "creditorName": lambda _: _,
        "remittanceInformationUnstructured": lambda _: _,
        "remittanceInformationUnstructuredArray": lambda reference_list: ", ".join(
            reference_list
        ),
        "debtorName": lambda _: _,
    }

    transaction_references = set()
    for reference_key, transformation in reference_keys.items():
        if reference_key in transaction:
            reference_value = transformation(transaction[reference_key])  # type: ignore
            if reference_value not in INVALID_REFERENCES:
                transaction_references.add(reference_value.lower())

    if len(transaction_references) == 0:
        raise Exception(f"no reference found {transaction}")

    return ", ".join(sorted(transaction_references))


def get_category_code(transaction: NordigenTransaction) -> str:
    if "merchantCategoryCode" in transaction:
        return transaction["merchantCategoryCode"]

    return "INVALID CATEGORY"


def get_proprietary_bank_transaction_code(transaction: NordigenTransaction) -> str:
    if "proprietaryBankTransactionCode" in transaction:
        return transaction["proprietaryBankTransactionCode"]

    return "UNKNOWN_PROPRIETARY_TRANSACTION_CODE"
