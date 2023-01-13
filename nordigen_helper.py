from datetime import datetime
import dateutil.parser
import uuid
from typing import Dict


INVALID_REFERENCES = ["", "-", None, []]


def get_datetime(transaction: Dict) -> datetime:
    if "bookingDatetime" in transaction:
        return dateutil.parser.isoparse(transaction["bookingDatetime"])

    if "bookingDate" in transaction:
        return dateutil.parser.parse(transaction["bookingDate"])

    raise Exception(f"no sort datetime found! {transaction}")


def get_amount(transaction: Dict) -> float:
    return float(transaction["transactionAmount"]["amount"])


def get_id(transaction: Dict) -> str:
    if "transactionId" not in transaction:
        return str(
            uuid.uuid5(
                uuid.UUID("29fff09d-93fa-49d2-a902-eb39f25ba953"),
                get_datetime(transaction).isoformat()
                + str(get_amount(transaction))
                + get_reference(transaction),
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
