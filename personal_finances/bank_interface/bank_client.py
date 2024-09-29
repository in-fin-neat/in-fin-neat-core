from abc import ABC, abstractmethod
from typing import Any, Dict, cast
from pydantic import BaseModel

from nordigen import NordigenClient

from .token_store import (
    AccessTokenObject,
    GocardlessAccessToken,
    TokenObject,
    gocardless_access_token_adapter,
    gocardless_token_adapter,
    gocardless_update_access_token,
)
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

    @abstractmethod
    def get_updated_access_token(
        self, current_token_object: TokenObject, new_access_token: AccessTokenObject
    ) -> TokenObject:
        pass

    @abstractmethod
    def generate_new_token(self) -> TokenObject:
        pass

    @abstractmethod
    def get_authorization_url(self, bank_details: BankDetails) -> AuthorizationUrl:
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

    def get_updated_access_token(
        self, current_token_object: TokenObject, new_access_token: AccessTokenObject
    ) -> TokenObject:
        return gocardless_update_access_token(
            GocardlessAccessToken(**cast(Dict, new_access_token)), current_token_object
        )

    def generate_new_token(self) -> TokenObject:
        new_gocardless_token = log_wrapper(self._nordigen_client.generate_token)
        return gocardless_token_adapter(new_gocardless_token)

    def get_authorization_url(self, bank_details: BankDetails) -> AuthorizationUrl:
        institution_id = (
            log_wrapper(
                self._nordigen_client.institution.get_institution_id_by_name,
                country=bank_details.country,
                institution=bank_details.name,
            ),
        )

        validation_reference = uuid.uuid4()
        requisition = log_wrapper(
            self._nordigen_client.initialize_session,
            institution_id=institution_id,
            # TODO: change to redirect to https:/<dns>/validations/validation_reference
            redirect_uri=f"http://127.0.0.1:8000/validations/{institution_id}",
            reference_id=f"infineat.{validation_reference}",
        )
        return AuthorizationUrl(
            authorization_url=requisition.link,
            validation_reference=str(validation_reference),
            payload=requisition.requisition_id,  # that's specific for gocardless
        )
