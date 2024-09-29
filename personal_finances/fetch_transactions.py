from personal_finances.bank_interface.bank_auth_handler import (
    BankAuthorizationHandler,
    NordigenAuth,
)
from personal_finances.bank_interface.bank_client import BankDetails
import logging
from typing import Tuple
from datetime import datetime
import json
import click
import os


LOGGER = logging.getLogger(__name__)


def _read_secrets() -> Tuple[str, str]:
    return os.environ["GOCARDLESS_SECRET_ID"], os.environ["GOCARDLESS_SECRET_KEY"]


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
    auth_handler = BankAuthorizationHandler(
        auth=NordigenAuth(secret_id, secret_key),
        bank_details=[
            BankDetails(name="Revolut", country="LV"),
            BankDetails(name="N26", country="DE"),
            BankDetails(name="Allied Irish Banks", country="IE"),
        ],
    )

    with open(
        f"data/transactions-{datetime.now().isoformat()}.json", "w"
    ) as output_file:
        transactions = auth_handler.gocardless_client.get_transactions(
            map(lambda url: url.payload, auth_handler.auth_urls)
        )
        output_file.write(json.dumps(transactions, indent=4))
        LOGGER.info(
            f"""
            {len(transactions['booked']) + len(transactions['pending'])}
            transactions were written
            """
        )


if __name__ == "__main__":
    fetch_transactions()
