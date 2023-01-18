from bank_client import BankClient, BankDetails, NordigenAuth
from datetime import datetime
import json
import click


def _read_secrets():
    with open("/home/tsutsumi/Downloads/nord-diego.json", "r") as f:
        secrets = json.loads(f.read())
    return secrets["secret_id"], secrets["secret_key"]


@click.command()
def save_transactions():
    """
    Authenticates Nordigen API to pre-configured banks,
    gets transactions and saves into 'data' folder.
    """
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
        print(
            f"""
            {len(transactions['booked']) + len(transactions['pending'])}
            transactions were written
            """
        )


if __name__ == "__main__":
    save_transactions()
