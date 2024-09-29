from typing import Iterable
from .requisition_store import (
    GocardlessRequisitionValidator,
    RequisitionStore,
    gocardless_requisition_adapter,
)
from .bank_client import AuthorizationUrl, BankClient, BankDetails, GocardlessClient
from .token_store import TokenStore
import logging

from ..utils import log_wrapper


LOGGER = logging.getLogger(__name__)


class BankClientStoreTokenHandler:
    def __init__(self, bank_client: BankClient, token_store: TokenStore):
        self._token_store = token_store
        self._bank_client = bank_client

    def handle_auth_token(self, user_id: str) -> None:
        if self._token_store.is_access_token_valid(user_id):
            LOGGER.info("valid access token found")
            stored_token = self._token_store.get_last_token(user_id)
            self._bank_client.set_token(stored_token)

        elif self._token_store.is_refresh_token_valid(user_id):
            LOGGER.info("valid refresh token found")
            last_token = self._token_store.get_last_token(user_id)
            new_access_token = self._bank_client.refresh_access_token(last_token)
            updated_token = self._bank_client.get_updated_access_token(
                last_token, new_access_token
            )
            self._bank_client.set_token(updated_token)
            self._token_store.save_token(user_id, updated_token)

        else:
            LOGGER.info("no valid token found - generating new token")
            new_token_object = log_wrapper(self._bank_client.generate_new_token)
            self._bank_client.set_token(new_token_object)
            self._token_store.save_token(user_id, new_token_object)


class GocardlessUrlClientStoreHandler:
    def __init__(
        self, gocardless_client: GocardlessClient, requisition_store: RequisitionStore
    ):
        self._gocardless_client = gocardless_client
        self._requisition_store = requisition_store

    def handle_authorization_urls(
        self, user_id: str, bank_details: Iterable[BankDetails]
    ) -> Iterable[AuthorizationUrl]:
        requisition_validator = GocardlessRequisitionValidator(
            self._gocardless_client._nordigen_client.requisition
        )

        if self._requisition_store.are_stored_requisitions_valid(
            user_id, requisition_validator
        ):
            return map(
                lambda requisition_id: AuthorizationUrl.model_validate(
                    {
                        # These empty strings will be populated when requisition store
                        # is transformed into URL store, it's needed for bank validation
                        "authorization_url": "",
                        "validation_reference": "",
                        "payload": requisition_id,
                    }
                ),
                self._requisition_store.get_last_requisitions(user_id).RequisitionIds,
            )
        else:
            authorization_urls = map(
                self._gocardless_client.get_authorization_url, bank_details
            )

            LOGGER.info(authorization_urls)

            parsed_requisitions = gocardless_requisition_adapter(authorization_urls)
            self._requisition_store.save_requisitions(user_id, parsed_requisitions)
            return authorization_urls
