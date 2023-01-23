import click
import logging
import os
import re
from typing import List, Dict
import json
from collections import defaultdict
from personal_finances.file_helper import write_json
from personal_finances.bank_interface.nordigen_fields import get_id


LOGGER = logging.getLogger(__name__)
LOGGER.info = print


def _get_deduped_transaction(dupe_transactions: List[Dict]) -> Dict:
    if len(dupe_transactions) == 1:
        return dupe_transactions[0]

    LOGGER.info(f"deduping: {dupe_transactions}")
    return sorted(
        dupe_transactions,
        key=lambda dupe_transaction: len(dupe_transaction.keys()),
        reverse=True,
    )[0]


def dedupe_transactions(transactions: List[Dict]) -> List[Dict]:
    transactions_by_id = defaultdict(list)
    for transaction in transactions:
        transactions_by_id[get_id(transaction)].append(transaction)

    deduped_transactions = []
    for id, dupe_transactions in transactions_by_id.items():
        deduped_transactions.append(_get_deduped_transaction(dupe_transactions))

    return deduped_transactions


@click.command()
def merge_transactions():
    """
    Merges files with pattern 'data/transactions*.json' into
    'data/merged_transactions.json'.

    Since 'pending' transactions have different schema,
    this command ignores them.

    Warning: This command uses relative paths,
    you need to have a 'data' directory in the current
    directory you are calling this command
    """
    transaction_files = (
        transaction_file
        for transaction_file in os.listdir("data/")
        if re.match(r"transactions.*\.json", transaction_file) is not None
    )
    transactions = []
    for transaction_file in transaction_files:
        print(f"opening {transaction_file}")
        with open(f"data/{transaction_file}", "r") as t_file:
            file_transactions = json.loads(t_file.read())
            transactions += file_transactions["booked"]
            # ignoring "pending", some of them have no way to ID+dedupe
            # transactions += file_transactions["pending"]

    deduped_transactions = dedupe_transactions(transactions)
    write_json("data/merged_transactions.json", deduped_transactions)


if __name__ == "__main__":
    merge_transactions()
