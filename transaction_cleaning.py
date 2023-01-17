from typing import Dict, List
from datetime import timedelta
from itertools import chain
from nordigen_helper import (
    get_datetime,
    get_amount,
    get_id,
    get_reference,
)


INTERNAL_TRANSFER_CUSTOM_REFERENCES = [
    "revolut",
    "google pay top-up",
    "n26",
    "aib",
    "amanda",
    "diego",
    "sent from",
]
BANK_PROCESSING_TIME_IN_DAYS = 4


def _has_internal_transfer_features(transaction: Dict) -> bool:
    reference = get_reference(transaction)
    amount = get_amount(transaction)
    return amount != 0 and any(
        transfer_ref in reference
        for transfer_ref in INTERNAL_TRANSFER_CUSTOM_REFERENCES
    )


def _get_internal_transfers(transactions: List[Dict]) -> List[Dict]:
    skip_processing = set()
    internal_transfers = list()
    internal_transfer_ids = list()
    for current_transaction in transactions:
        current_id = get_id(current_transaction)
        current_amount = get_amount(current_transaction)
        current_datetime = get_datetime(current_transaction)

        if current_id in skip_processing or not _has_internal_transfer_features(
            current_transaction
        ):
            continue

        matching_transactions = [
            transaction
            for transaction in transactions
            if _has_internal_transfer_features(transaction)
            and current_amount == -get_amount(transaction)
            and abs(current_datetime - get_datetime(transaction))
            < timedelta(days=BANK_PROCESSING_TIME_IN_DAYS)
        ]

        if len(matching_transactions) > 1:
            print(
                f"""
                ambiguous possible transfers:
                {current_transaction} {matching_transactions}
                selecting first in list as a matching transaction
                """
            )

        if len(matching_transactions) == 0:
            continue

        internal_transfers.append((current_transaction, matching_transactions[0]))
        internal_transfer_ids.append((current_id, get_id(matching_transactions[0])))
        skip_processing.add(current_id)
        skip_processing.add(get_id(matching_transactions[0]))
        print(
            f"internal transfer pair detected {current_transaction} {matching_transactions[0]}"
        )

    return internal_transfer_ids


def remove_internal_transfers(transactions: List[Dict]) -> List[Dict]:
    internal_transfer_ids = set(chain(*_get_internal_transfers(transactions)))
    return [
        transaction
        for transaction in transactions
        if get_id(transaction) not in internal_transfer_ids
    ]
