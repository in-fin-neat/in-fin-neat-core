from personal_finances.bank_interface.client import (
    BankClient,
    BankDetails,
    NordigenAuth,
)
import logging
from typing import Tuple
from datetime import datetime
import json
import click
import os


LOGGER = logging.getLogger(__name__)


def _read_secrets() -> Tuple[str, str]:
    with open("/home/tsutsumi/Downloads/nord-diego.json", "r") as f:
        secrets = json.loads(f.read())
    return secrets["secret_id"], secrets["secret_key"]


def _ensure_data_path_exist() -> None:
    if not os.path.exists("data"):
        os.makedirs("data")


@click.command()
def fetch_transactions() -> None:
    """
    Authenticates Nordigen API to pre-configured banks,
    gets transactions and saves into 'data' folder.
    """
    _ensure_data_path_exist()
    secret_id, secret_key = _read_secrets()
    with BankClient(
        NordigenAuth(secret_id, secret_key),
        [
            BankDetails(name="Revolut", country="LV"),
            BankDetails(name="N26", country="DE"),
            BankDetails(name="Allied Irish Banks", country="IE"),
        ],
    ) as bank_client, open(
        f"data/transactions-{datetime.now().isoformat()}.json", "w"
    ) as output_file:
        transactions = bank_client.get_transactions()
        output_file.write(json.dumps(transactions, indent=4))
        LOGGER.info(
            f"""
            {len(transactions['booked']) + len(transactions['pending'])}
            transactions were written
            """
        )


if __name__ == "__main__":
    fetch_transactions()
