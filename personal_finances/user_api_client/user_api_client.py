import base64
import logging
from decorator import decorator
import requests
from typing import Callable, Dict, Any, List, Optional

from schwifty import IBAN

LOGGER = logging.getLogger(__name__)


class ApiClientError(Exception):
    """Generic error raised by the UserApiClient when requests fail."""

    pass


def _make_request(method: Callable, url: str, headers: Dict[str, str]) -> Any:
    try:
        response = method(url, headers=headers)
        response.raise_for_status()  # raises an HTTP error if one occurred
        LOGGER.info("User API request successful")
        return response
    except requests.RequestException as exc:
        raise ApiClientError(f"User API request failed: {exc}") from exc


def _post(url: str, headers: Dict[str, str]) -> Any:
    return _make_request(requests.post, url, headers)


def _get(url: str, headers: Dict[str, str]) -> Any:
    return _make_request(requests.get, url, headers)


def _put(url: str, headers: Dict[str, str]) -> Any:
    return _make_request(requests.put, url, headers)


class UserApiClient:
    """
    A client that wraps the user-related API endpoints.
    """

    def __init__(self, base_url: str) -> None:
        """
        Initializes the client with a base URL.
        """
        self.base_url: str = base_url
        self.auth_token: Optional[str] = ""

    @decorator
    @staticmethod
    def _check_args(func: Callable, self: Any, *args: Any, **kwargs: Any) -> Any:
        all_args = list(args) + list(kwargs.values())
        for arg in all_args:
            if arg is None or arg == "":
                raise ValueError("Arguments cannot be None or an empty string.")
        return func(self, *args, **kwargs)

    @decorator
    @staticmethod
    def _check_token_not_none(
        func: Callable, self: Any, *args: Any, **kwargs: Any
    ) -> Any:
        if not self.auth_token:
            raise ApiClientError("Cannot make request before logging in.")
        return func(self, *args, **kwargs)

    @_check_args
    def login(self, user_id: str, password: str) -> str:
        """
        Logs in a user using POST /users/{userId}/login and stores the returned token.

        :raises ValueError: If user_id or password is empty/None.
        :raises ApiClientError: If the request fails.
        """

        creds = f"{user_id}:{password}"
        encoded_creds = base64.b64encode(creds.encode()).decode()
        headers = {"Authorization": f"Basic {encoded_creds}"}
        url: str = f"{self.base_url}/users/{user_id}/login"

        LOGGER.info(f"New login attempt for user: {user_id}")

        response = _post(url, headers=headers)
        data: Dict[str, Any] = response.json()
        self.auth_token = data["token"]

        return self.auth_token if self.auth_token is not None else ""

    @_check_args
    @_check_token_not_none
    def get_bank_accounts(self, user_id: str) -> List[str]:
        """
        Retrieves the list of bank accounts for the specified user via
        GET /users/{userId}/bank-accounts/.

        :raises ValueError: If user_id is empty/None.
        :raises ApiClientError: If not logged in, or request fails.
        """

        url: str = f"{self.base_url}/users/{user_id}/bank-accounts/"
        headers: Dict[str, str] = {"Authorization": f"Bearer {self.auth_token}"}

        LOGGER.info(f"Requesting IBANs of user: {user_id}")

        response = _get(url, headers=headers)
        data: Dict[str, Any] = response.json()
        ibans = data.get("ibanList", [])
        LOGGER.info(f"IBANs of {user_id}: {ibans}")

        return ibans if ibans is not None else []

    @_check_args
    @_check_token_not_none
    def update_bank_account(self, user_id: str, iban: str) -> Dict[str, Any]:
        """
        Updates a bank account via PUT /users/{userId}/bank-accounts/{iban}.

        :raises ValueError: If user_id or iban is empty/None, or if iban is invalid.
        :raises ApiClientError: If not logged in, or request fails.
        """

        IBAN(iban)
        url: str = f"{self.base_url}/users/{user_id}/bank-accounts/{iban}"
        headers: Dict[str, str] = {"Authorization": f"Bearer {self.auth_token}"}

        response = _put(url, headers=headers)
        response_message: Dict[str, Any] = response.json()

        return response_message
