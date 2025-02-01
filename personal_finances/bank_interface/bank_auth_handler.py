from __future__ import annotations
from dataclasses import dataclass
from functools import partial
from time import sleep
from nordigen import NordigenClient
from typing import List, Iterable
import logging

from .browser_helper import open_urls

from .requisition_store import (
    GocardlessRequisitionValidator,
    gocardless_requisition_adapter,
)
from ..utils import log_wrapper

from .bank_validation_provider import (
    LocalhostValidationProvider,
    BankValidationProvider,
)

from .bank_client import AuthorizationUrl, GocardlessClient, BankDetails

from .disk_requisition_store import DiskRequisitionStore
from .disk_token_store import DiskTokenStore


@dataclass
class NordigenAuth:
    secret_id: str
    secret_key: str


# Warning: the application does not support multiple users, however some features
#          do support it and this temporary variable is used across features
#          supporing multiple users.
TEMPORARY_FIXED_USER_ID = "temporary-user-id"
LOGGER = logging.getLogger(__name__)


class BankAuthorizationHandler:
    def __init__(self, auth: NordigenAuth, bank_details: List[BankDetails]):
        self._bank_details = bank_details
        self._nordigen_client = NordigenClient(
            secret_id=auth.secret_id,
            secret_key=auth.secret_key,
        )
        self._token_store = DiskTokenStore()
        self._requisition_store = DiskRequisitionStore()
        self._bank_client = GocardlessClient(self._nordigen_client)
        self._resolve_auth_token(TEMPORARY_FIXED_USER_ID)

        self.gocardless_client = GocardlessClient(self._nordigen_client)

        with LocalhostValidationProvider() as validation_provider:
            self.auth_urls = self._resolve_authorization_urls(
                TEMPORARY_FIXED_USER_ID, bank_details, validation_provider
            )

            # Front end opens URL for user authorization
            open_urls(
                map(lambda auth_url_obj: auth_url_obj.authorization_url, self.auth_urls)
            )

            self._wait_references_to_be_validated(
                map(
                    lambda auth_url_obj: auth_url_obj.validation_reference,
                    self.auth_urls,
                ),
                validation_provider,
            )

        LOGGER.info("client initialized")

    def _wait_references_to_be_validated(
        self, reference_ids: Iterable[str], validation_provider: BankValidationProvider
    ) -> None:
        all_references_are_validated = False

        LOGGER.info("waiting for user to authorize")
        while not all_references_are_validated:
            all_references_are_validated = all(
                validation_provider.is_reference_validated(r_id)
                for r_id in reference_ids
            )
            LOGGER.debug(f"reference validation {all_references_are_validated}")
            sleep(1)

    def _resolve_auth_token(self, user_id: str) -> None:
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

    def _resolve_authorization_urls(
        self,
        user_id: str,
        bank_details: Iterable[BankDetails],
        validation_provider: BankValidationProvider,
    ) -> List[AuthorizationUrl]:
        requisition_validator = GocardlessRequisitionValidator(
            self.gocardless_client._nordigen_client.requisition
        )

        if self._requisition_store.are_stored_requisitions_valid(
            user_id, requisition_validator
        ):
            LOGGER.debug("requisition store has valid requisitions")
            return list(
                map(
                    lambda requisition_id: AuthorizationUrl.model_validate(
                        {
                            # These empty strings will be populated when
                            # requisition store is transformed into URL store,
                            # it's needed for bank validation
                            "authorization_url": "",
                            "validation_reference": "",
                            "payload": requisition_id,
                        }
                    ),
                    self._requisition_store.get_last_requisitions(
                        user_id
                    ).RequisitionIds,
                )
            )
        else:
            LOGGER.debug("no valid requisitions stored, getting new requisitions")
            authorization_urls = list(
                map(
                    partial(
                        self.gocardless_client.get_authorization_url,
                        validation_provider=validation_provider,
                    ),
                    bank_details,
                )
            )

            parsed_requisitions = gocardless_requisition_adapter(authorization_urls)
            self._requisition_store.save_requisitions(user_id, parsed_requisitions)
            return authorization_urls
