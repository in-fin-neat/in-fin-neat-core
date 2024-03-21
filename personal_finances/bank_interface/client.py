from __future__ import annotations
from nordigen import NordigenClient
import time
from dataclasses import dataclass
from typing import Dict, List, Callable, Any, Iterable, Type, Optional, cast
from types import TracebackType
import webbrowser
from functools import reduce
import subprocess
import os
import signal
import requests
import logging

from .disk_requisition_store import DiskRequisitionStore
from personal_finances.bank_interface.nordigen_adapter import (
    EMPTY_NORDIGEN_TRANSACTIONS,
    NordigenTransactions,
    concat_nordigen_transactions,
)
from personal_finances.bank_interface.requisition_store import (
    GocardlessRequisitionValidator,
    Requisitions,
    gocardless_requisition_adapter,
)
from .disk_token_store import DiskTokenStore
from .token_store import (
    GocardlessAccessToken,
    gocardless_token_adapter,
    gocardless_update_access_token,
)


LOGGER = logging.getLogger(__name__)
NordigenRequisition = Any


@dataclass
class BankDetails:
    name: str
    country: str


@dataclass
class NordigenAuth:
    secret_id: str
    secret_key: str


def log_wrapper(func: Callable, *args: Any, **kwargs: Any) -> Any:
    LOGGER.info(f"calling {func.__name__} with {kwargs}")
    response = func(*args, **kwargs)
    LOGGER.info(f"response from {func.__name__} is {response}")
    return response


# Warning: the application does not support multiple users, however some features
#          do support it and this temporary variable is used across features
#          supporing multiple users.
TEMPORARY_FIXED_USER_ID = "temporary-user-id"


class BankClient:
    def __init__(self, auth: NordigenAuth, bank_details: List[BankDetails]):
        self._bank_details = bank_details
        self._nordigen_client = NordigenClient(
            secret_id=auth.secret_id,
            secret_key=auth.secret_key,
        )
        self._token_store = DiskTokenStore()
        self._requisition_store = DiskRequisitionStore()

        self._handle_tokens()

        LOGGER.info("client initialized")

    def __enter__(self) -> BankClient:
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

    def _handle_tokens(self) -> None:
        if self._token_store.is_access_token_valid(TEMPORARY_FIXED_USER_ID):
            LOGGER.info("valid access token found")
            self._nordigen_client.token = self._token_store.get_last_token(
                TEMPORARY_FIXED_USER_ID
            ).AccessToken

        elif self._token_store.is_refresh_token_valid(TEMPORARY_FIXED_USER_ID):
            LOGGER.info("valid refresh token found")
            last_token = self._token_store.get_last_token(TEMPORARY_FIXED_USER_ID)
            new_access_token = self._nordigen_client.exchange_token(
                last_token.RefreshToken
            )
            updated_token = gocardless_update_access_token(
                GocardlessAccessToken(**cast(Dict, new_access_token)), last_token
            )
            self._token_store.save_token(TEMPORARY_FIXED_USER_ID, updated_token)
        else:
            LOGGER.info("no valid token found - generating new token")
            # Users are prompted with URLs to authorize their bank data
            new_token = log_wrapper(self._nordigen_client.generate_token)
            new_token_object = gocardless_token_adapter(new_token)

            self._nordigen_client.token = new_token_object.AccessToken
            self._token_store.save_token(TEMPORARY_FIXED_USER_ID, new_token_object)

    def _create_bank_requisitions(self) -> Iterable[NordigenRequisition]:
        institution_ids: Iterable[Any] = map(
            lambda bank_details: log_wrapper(
                self._nordigen_client.institution.get_institution_id_by_name,
                country=bank_details.country,
                institution=bank_details.name,
            ),
            self._bank_details,
        )

        return map(
            lambda institution_id: log_wrapper(
                self._nordigen_client.initialize_session,
                institution_id=institution_id,
                redirect_uri=f"http://127.0.0.1:8000/validations/{institution_id}",
                reference_id=f"Diego Personal PC {time.time()}",
            ),
            institution_ids,
        )

    def _authorize_requisition(self, requisition: NordigenRequisition) -> None:
        webbrowser.open(requisition.link)

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

    def _get_requisitions(self) -> Requisitions:
        requisition_validator = GocardlessRequisitionValidator(
            self._nordigen_client.requisition
        )

        if self._requisition_store.are_all_requisition_valid(
            TEMPORARY_FIXED_USER_ID, requisition_validator
        ):
            return self._requisition_store.get_last_requisitions(
                TEMPORARY_FIXED_USER_ID
            )
        else:
            requisitions = list(self._create_bank_requisitions())
            for requisition in requisitions:
                self._authorize_requisition(requisition)

            self._verify_authorizations()

            LOGGER.info(requisitions)

            parsed_requisitions = gocardless_requisition_adapter(requisitions)
            self._requisition_store.save_requisitions(
                TEMPORARY_FIXED_USER_ID, parsed_requisitions
            )
            return parsed_requisitions

    def get_transactions(self) -> NordigenTransactions:
        return reduce(
            concat_nordigen_transactions,
            map(
                lambda requisitionId: self._get_transactions_for_requisition(
                    requisitionId
                ),
                self._get_requisitions().RequisitionIds,
            ),
            EMPTY_NORDIGEN_TRANSACTIONS,
        )
