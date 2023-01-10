from nordigen import NordigenClient
import time
from dataclasses import dataclass
from typing import List, Callable, Any
import webbrowser
from functools import reduce
from itertools import tee
import subprocess, sys, os, signal
import requests
import logging


LOGGER = logging.getLogger(__name__)
LOGGER.info = print


@dataclass
class BankDetails:
    name: str
    country: str


@dataclass
class NordigenAuth:
    secret_id: str
    secret_key: str


def log_wrapper(func: Callable, *args, **kwargs) -> Any:
    LOGGER.info(f"calling {func.__name__} with {kwargs}")
    response = func(*args, **kwargs)
    LOGGER.info(f"response from {func.__name__} is {response}")
    return response


EMPTY_TRANSACTIONS = {"booked": [], "pending": []}


class BankClient:
    def __init__(self, auth: NordigenAuth, bank_details: List[BankDetails]):
        self.bank_details = bank_details
        self._nordigen_client = NordigenClient(
            secret_id=auth.secret_id,
            secret_key=auth.secret_key,
        )
        self._token = log_wrapper(self._nordigen_client.generate_token)
        LOGGER.info("client initialized")

    def __enter__(self):
        self._web_authorizer_process = subprocess.Popen(
            ["uvicorn", "authorizer:app", "--reload"],
            preexec_fn=os.setpgrp
        )
        LOGGER.info("uvicorn server started")
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        os.killpg(
            os.getpgid(self._web_authorizer_process.pid),
            signal.SIGTERM,
        )
        LOGGER.info("uvicorn server killed")

    def _create_bank_sessions(self):
        institution_ids = map(
            lambda bank_details: log_wrapper(
                self._nordigen_client.institution.get_institution_id_by_name,
                country=bank_details.country,
                institution=bank_details.name,
            ),
            self.bank_details
        )

        return map(
            lambda institution_id: log_wrapper(
                self._nordigen_client.initialize_session,
                institution_id=institution_id,
                redirect_uri=f"http://localhost:8000/validations/{institution_id}",
                reference_id=f"Diego Personal PC {time.time()}"
            ),
            institution_ids
        )

    def _authorize_session(self, session):
        webbrowser.open(session.link)

    def _verify_authorizations(self):
        validations = []

        # TODO: validate content, not only length
        while len(validations) < len(self.bank_details):
            validations = requests.get("http://localhost:8000/validations/", verify=False).json()
            LOGGER.info(validations)
            time.sleep(1)

    def _get_transactions_for_requisition(self, requisition_id):
        LOGGER.info(f"getting transactions for requisition {requisition_id}")
        accounts = log_wrapper(
            self._nordigen_client.requisition.get_requisition_by_id,
            requisition_id=requisition_id
        )

        if len(accounts["accounts"]) == 0:
            return EMPTY_TRANSACTIONS

        account_id = accounts["accounts"][0]
        account = log_wrapper(self._nordigen_client.account_api, id=account_id)
        transactions = log_wrapper(account.get_transactions)
        return transactions["transactions"]

    def get_transactions(self):
        sessions = list(self._create_bank_sessions())
        for session in sessions:
            self._authorize_session(session)

        self._verify_authorizations()

        LOGGER.info(sessions)

        return reduce(
            lambda all_transactons, transactions: {
                "booked": all_transactons["booked"] + transactions["booked"],
                "pending": all_transactons["pending"] + transactions["pending"]
            },
            map(
                lambda session: self._get_transactions_for_requisition(session.requisition_id),
                sessions,
            ),
            EMPTY_TRANSACTIONS
        )
