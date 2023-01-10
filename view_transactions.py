from bank_client import BankClient, BankDetails, NordigenAuth
import json

def _read_secrets():
    with open("/home/tsutsumi/Downloads/nord-diego.json", "r") as f:
        secrets = json.loads(f.read())
    return secrets["secret_id"], secrets["secret_key"]


secret_id, secret_key = _read_secrets()
with BankClient(
    NordigenAuth(secret_id, secret_key),
    [
        BankDetails(name="Revolut", country="LV"),
        BankDetails(name="N26", country="DE"),
        BankDetails(name="Allied Irish Banks", country="IE")
    ]
) as bank_client:
    print(bank_client.get_transactions())
