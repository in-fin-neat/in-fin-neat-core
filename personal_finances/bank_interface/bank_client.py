from abc import ABC, abstractmethod
from typing import Any, Dict, Iterable, cast
from pydantic import BaseModel
from functools import reduce
from copy import deepcopy
from nordigen import NordigenClient
from .bank_validation_provider import BankValidationProvider
from ..bank_interface.nordigen_adapter import (
    EMPTY_NORDIGEN_TRANSACTIONS,
    NordigenTransactions,
    concat_nordigen_transactions,
)
from .token_store import (
    AccessTokenObject,
    GocardlessAccessToken,
    TokenObject,
    gocardless_access_token_adapter,
    gocardless_token_adapter,
)
from datetime import datetime
import logging
from ..utils import log_wrapper
import uuid


LOGGER = logging.getLogger(__name__)
NordigenRequisition = Any


class BankDetails(BaseModel):
    name: str
    country: str


class AuthorizationUrl(BaseModel):
    authorization_url: str
    validation_reference: str
    payload: str


class BankClient(ABC):
    @abstractmethod
    def set_token(self, token_object: TokenObject) -> None:
        pass

    @abstractmethod
    def refresh_access_token(
        self, current_token_object: TokenObject
    ) -> AccessTokenObject:
        pass

    def get_updated_access_token(
        self, current_token_object: TokenObject, new_access_token: AccessTokenObject
    ) -> TokenObject:
        new_token_object = deepcopy(current_token_object)
        new_token_object.AccessToken = new_access_token.AccessToken
        new_token_object.AccessExpires = new_access_token.AccessExpires
        new_token_object.AccessRefreshEpoch = int(datetime.now().timestamp())
        return new_token_object

    @abstractmethod
    def generate_new_token(self) -> TokenObject:
        pass

    @abstractmethod
    def get_authorization_url(
        self, bank_details: BankDetails, validation_provider: BankValidationProvider
    ) -> AuthorizationUrl:
        pass


class GocardlessClient(BankClient):
    def __init__(self, nordigen_client: NordigenClient):
        self._nordigen_client = nordigen_client

    def set_token(self, token_object: TokenObject) -> None:
        self._nordigen_client.token = token_object.AccessToken

    def refresh_access_token(
        self, current_token_object: TokenObject
    ) -> AccessTokenObject:
        gocardless_token = self._nordigen_client.exchange_token(
            current_token_object.RefreshToken
        )
        return gocardless_access_token_adapter(
            GocardlessAccessToken(**cast(Dict, gocardless_token))
        )

    def generate_new_token(self) -> TokenObject:
        new_gocardless_token = log_wrapper(self._nordigen_client.generate_token)
        return gocardless_token_adapter(new_gocardless_token)

    def get_authorization_url(
        self, bank_details: BankDetails, validation_provider: BankValidationProvider
    ) -> AuthorizationUrl:
        institution_id = log_wrapper(
            self._nordigen_client.institution.get_institution_id_by_name,
            country=bank_details.country,
            institution=bank_details.name,
        )

        validation_reference = str(uuid.uuid4())
        requisition = log_wrapper(
            self._nordigen_client.initialize_session,
            institution_id=institution_id,
            redirect_uri=validation_provider.get_validation_url(validation_reference),
            reference_id=validation_reference,
        )
        return AuthorizationUrl(
            authorization_url=requisition.link,
            validation_reference=validation_reference,
            payload=requisition.requisition_id,  # that's specific for gocardless
        )

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

    def get_transactions(self, requisition_ids: Iterable[str]) -> NordigenTransactions:
        return reduce(
            concat_nordigen_transactions,
            map(
                lambda requisition_id: self._get_transactions_for_requisition(
                    requisition_id
                ),
                requisition_ids,
            ),
            EMPTY_NORDIGEN_TRANSACTIONS,
        )
