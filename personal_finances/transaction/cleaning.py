from typing import List, Tuple
from datetime import timedelta
from itertools import chain
from .definition import SimpleTransaction
from ..config import get_user_configuration
import logging


LOGGER = logging.getLogger(__name__)


def _has_internal_transfer_features(transaction: SimpleTransaction) -> bool:
    return transaction["amount"] != 0 and any(
        transfer_ref in transaction["referenceText"]
        for transfer_ref in get_user_configuration().InternalTransferReferences
    )


def _get_internal_transfers(
    transactions: List[SimpleTransaction],
) -> List[Tuple[str, str]]:
    skip_processing = set()
    internal_transfers = list()
    internal_transfer_ids = list()
    for current_transaction in transactions:
        current_id = current_transaction["transactionId"]
        current_amount = current_transaction["amount"]
        current_datetime = current_transaction["datetime"]

        if current_id in skip_processing or not _has_internal_transfer_features(
            current_transaction
        ):
            continue

        matching_transactions = [
            transaction
            for transaction in transactions
            if _has_internal_transfer_features(transaction)
            and current_amount == -transaction["amount"]
            and abs(current_datetime - transaction["datetime"])
            < timedelta(days=get_user_configuration().BankProcessingTimeInDays)
            and transaction["transactionId"] not in skip_processing
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

        internal_transfers.append((current_transaction, matching_transactions[0]))
        internal_transfer_ids.append(
            (current_id, matching_transactions[0]["transactionId"])
        )
        skip_processing.add(current_id)
        skip_processing.add(matching_transactions[0]["transactionId"])
        LOGGER.info(
            f"""
            internal transfer pair detected
            {current_transaction} {matching_transactions[0]}
            """
        )

    return internal_transfer_ids


def remove_internal_transfers(
    transactions: List[SimpleTransaction],
) -> List[SimpleTransaction]:
    internal_transfer_ids = set(chain(*_get_internal_transfers(transactions)))
    return [
        transaction
        for transaction in transactions
        if transaction["transactionId"] not in internal_transfer_ids
    ]
