from datetime import datetime
import dateutil.parser
from dateutil.tz import tzutc
import uuid
from typing import Dict, List, Any


INVALID_REFERENCES: List[Any] = ["", "-", None, []]


def get_datetime(transaction: Dict) -> datetime:
    if "bookingDatetime" in transaction:
        return dateutil.parser.isoparse(transaction["bookingDatetime"])

    if "bookingDate" in transaction:
        booking_date = dateutil.parser.parse(transaction["bookingDate"])
        return booking_date.replace(tzinfo=booking_date.tzinfo or tzutc())

    raise Exception(f"no sort datetime found! {transaction}")


def get_amount(transaction: Dict) -> float:
    return float(transaction["transactionAmount"]["amount"])


def _get_internal_transaction_id(transaction: Dict) -> str:
    return transaction["internalTransactionId"]


def get_id(transaction: Dict) -> str:
    if "transactionId" not in transaction:
        return str(
            uuid.uuid5(
                uuid.UUID("29fff09d-93fa-49d2-a902-eb39f25ba953"),
                _get_internal_transaction_id(transaction)
                + str(get_amount(transaction))
            )
        )

    return transaction["transactionId"]


def get_reference(transaction: Dict) -> str:
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
            reference_value = transformation(transaction[reference_key])
            if reference_value not in INVALID_REFERENCES:
                transaction_references.add(reference_value.lower())

    if len(transaction_references) == 0:
        raise Exception(f"no reference found {transaction}")

    return ", ".join(sorted(transaction_references))


def get_category_code(transaction: Dict) -> str:
    if "merchantCategoryCode" in transaction:
        return transaction["merchantCategoryCode"]

    return "INVALID CATEGORY"


def get_proprietary_bank_transaction_code(transaction: Dict) -> str:
    if "proprietaryBankTransactionCode" in transaction:
        return transaction["proprietaryBankTransactionCode"]

    return "UNKNOWN_PROPRIETARY_TRANSACTION_CODE"
