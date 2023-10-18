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


def _read_secrets(secret_json_file: str) -> Tuple[str, str]:
    try:
        with open(secret_json_file, "r") as f:
            try:
                secrets = json.loads(f.read())
            except ValueError:
                raise ValueError("{} is a not valid JSON".format(secret_json_file))

        if secrets.get("secret_id") is None:
            raise KeyError("secret_id key not found in {}".format(secret_json_file))
        if secrets.get("secret_key") is None:
            raise KeyError("secret_key key not found in {}".format(secret_json_file))
        return secrets["secret_id"], secrets["secret_key"]

    except IOError:
        raise IOError("{} secret file does not exist".format(secret_json_file))


def _ensure_data_path_exist() -> None:
    if not os.path.exists("data"):
        os.makedirs("data")


@click.command()
@click.option(
    "-s",
    "--secret_json_file",
    required=True,
    help="Nordigen secrets JSON file for authentication",
    type=str,
)
def fetch_transactions(secret_json_file: str) -> None:
    """
    Authenticates Nordigen API to pre-configured banks,
    gets transactions and saves into 'data' folder.
    """
    _ensure_data_path_exist()
    secret_id, secret_key = _read_secrets(secret_json_file)
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
