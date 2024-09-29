from __future__ import annotations
from nordigen import NordigenClient
import time
from dataclasses import dataclass
from typing import List, Iterable, Type, Optional
from types import TracebackType
import webbrowser
from functools import reduce
import subprocess
import os
import signal
import requests
import logging

from .bank_client import AuthorizationUrl, GocardlessClient, BankDetails

from .disk_requisition_store import DiskRequisitionStore
from ..bank_interface.nordigen_adapter import (
    EMPTY_NORDIGEN_TRANSACTIONS,
    NordigenTransactions,
    concat_nordigen_transactions,
)
from .disk_token_store import DiskTokenStore
from ..utils import log_wrapper
from .bank_auth import BankClientStoreTokenHandler, GocardlessUrlClientStoreHandler


LOGGER = logging.getLogger(__name__)


@dataclass
class NordigenAuth:
    secret_id: str
    secret_key: str


# Warning: the application does not support multiple users, however some features
#          do support it and this temporary variable is used across features
#          supporing multiple users.
TEMPORARY_FIXED_USER_ID = "temporary-user-id"


class BrowserAuthBankClient:
    def __init__(self, auth: NordigenAuth, bank_details: List[BankDetails]):
        self._bank_details = bank_details
        self._nordigen_client = NordigenClient(
            secret_id=auth.secret_id,
            secret_key=auth.secret_key,
        )
        self._token_store = DiskTokenStore()
        self._requisition_store = DiskRequisitionStore()
        bank_client = GocardlessClient(self._nordigen_client)
        self._bank_auth_handler = BankClientStoreTokenHandler(
            bank_client, self._token_store
        )
        self._bank_auth_handler.handle_auth_token(TEMPORARY_FIXED_USER_ID)

        gocardless_client = GocardlessClient(self._nordigen_client)
        self._gocardless_url_handler = GocardlessUrlClientStoreHandler(
            gocardless_client, self._requisition_store
        )

        self._auth_urls = self._gocardless_url_handler.handle_authorization_urls(
            TEMPORARY_FIXED_USER_ID, bank_details
        )
        self._authorize_in_browser(self._auth_urls)

        LOGGER.info("client initialized")

    def __enter__(self) -> BrowserAuthBankClient:
        self._web_authorizer_process = subprocess.Popen(
            ["uvicorn", "personal_finances.bank_interface.authorizer:app", "--reload"],
            preexec_fn=os.setpgrp,
        )
        LOGGER.info("uvicorn server started")
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        os.killpg(
            os.getpgid(self._web_authorizer_process.pid),
            signal.SIGTERM,
        )
        LOGGER.info("uvicorn server killed")

    def _authorize_in_browser(self, auth_urls: Iterable[AuthorizationUrl]) -> None:
        to_be_authorized_in_browser = list(
            filter(lambda auth_url: auth_url.authorization_url != "", auth_urls)
        )
        if len(to_be_authorized_in_browser) > 0:
            LOGGER.info(
                "opening urls in browser for authorization " +
                str(to_be_authorized_in_browser)
            )
            for url in to_be_authorized_in_browser:
                webbrowser.open(url.authorization_url)

            self._verify_authorizations()
        else:
            LOGGER.info(f"no authorization needed {to_be_authorized_in_browser}")

    def _verify_authorizations(self) -> None:
        validations: List[str] = []

        # TODO: validate content, not only length
        while len(validations) < len(self._bank_details):
            validations = requests.get(
                "http://127.0.0.1:8000/validations/", verify=False
            ).json()
            LOGGER.info(validations)
            time.sleep(1)

    def _get_transactions_for_requisition(
        self, requisition_id: str
    ) -> NordigenTransactions:
        LOGGER.info(f"getting transactions for requisition {requisition_id}")
        accounts = log_wrapper(
            self._nordigen_client.requisition.get_requisition_by_id,
            requisition_id=requisition_id,
        )

        if len(accounts["accounts"]) == 0:
            return EMPTY_NORDIGEN_TRANSACTIONS

        account_ids = accounts["accounts"]
        accounts = map(
            lambda account_id: log_wrapper(
                self._nordigen_client.account_api, id=account_id
            ),
            account_ids,
        )
        return reduce(
            concat_nordigen_transactions,
            map(
                lambda account: log_wrapper(account.get_transactions)["transactions"],
                accounts,
            ),
            EMPTY_NORDIGEN_TRANSACTIONS,
        )

    def get_transactions(self) -> NordigenTransactions:
        return reduce(
            concat_nordigen_transactions,
            map(
                lambda requisition_id: self._get_transactions_for_requisition(
                    requisition_id
                ),
                map(lambda auth_url: auth_url.payload, self._auth_urls),
            ),
            EMPTY_NORDIGEN_TRANSACTIONS,
        )
