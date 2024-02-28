from typing import List
from datetime import timedelta
from .definition import SimpleTransaction
from ..config import get_user_configuration
import logging


LOGGER = logging.getLogger(__name__)


def _validate_transaction(transaction: SimpleTransaction) -> None:
    for key, expected_type in SimpleTransaction.__annotations__.items():
        value = transaction.get(key, None)
        if key == "amount" and (isinstance(value, float) or isinstance(value, int)):
            continue  # Allow integers for 'amount' as well as floats
        if not isinstance(value, expected_type):
            raise TypeError(
                f"Invalid type for {key}, expected {expected_type.__name__}"
            )


def _has_internal_transfer_features(transaction: SimpleTransaction) -> bool:
    return transaction["amount"] != 0 and any(
        transfer_ref in transaction["referenceText"]
        for transfer_ref in get_user_configuration().InternalTransferReferences
    )


def _get_internal_transfers(
    transactions: List[SimpleTransaction],
) -> set[int]:
    internal_transfers = set()
    for index, current_transaction in enumerate(transactions):
        _validate_transaction(current_transaction)

        current_datetime = current_transaction["datetime"]
        current_amount = current_transaction["amount"]

        if index in internal_transfers or not _has_internal_transfer_features(
            current_transaction
        ):
            continue

        matching_transactions = [
            transaction
            for index, transaction in enumerate(transactions)
            if _has_internal_transfer_features(transaction)
            and current_amount == -transaction["amount"]
            and abs(current_datetime - transaction["datetime"])
            < timedelta(days=get_user_configuration().BankProcessingTimeInDays)
            and index not in internal_transfers
        ]

        if len(matching_transactions) > 1:
            LOGGER.info(
                f"""
                ambiguous possible transfers:
                {current_transaction} {matching_transactions}
                selecting first in list as a matching transaction
                """
            )

        if len(matching_transactions) == 0:
            continue

        internal_transfers.add(transactions.index(current_transaction))
        internal_transfers.add(transactions.index(matching_transactions[0]))

        LOGGER.info(
            f"""
            internal transfer pair detected
            {current_transaction} {matching_transactions[0]}
            """
        )
    return internal_transfers


def remove_internal_transfers(
    transactions: List[SimpleTransaction],
) -> List[SimpleTransaction]:
    internal_transfer_ids = _get_internal_transfers(transactions)
    return [
        transaction
        for index, transaction in enumerate(transactions)
        if index not in internal_transfer_ids
    ]
