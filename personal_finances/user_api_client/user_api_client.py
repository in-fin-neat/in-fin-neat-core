import base64
import logging
import requests
from typing import Dict, Any, List

from schwifty import IBAN
from schwifty.exceptions import SchwiftyException

LOGGER = logging.getLogger(__name__)


class ApiClientError(Exception):
    """Generic error raised by the UserApiClient when requests fail."""

    pass


class UserApiClient:
    """
    A client that wraps the user-related API endpoints.
    """

    def __init__(self, base_url: str) -> None:
        """
        Initializes the client with a base URL.

        :param base_url: The base URL of the API, e.g. "https://example.com"
        """
        self.base_url: str = base_url
        self.auth_token: str = ""

    def login(self, user_id: str, password: str) -> str:
        """
        Logs in a user using POST /users/{userId}/login and stores the returned token.

        :raises ValueError: If user_id or password is empty/None.
        :raises ApiClientError: If the request fails.
        """
        if not user_id:
            raise ValueError("User ID cannot be empty or None.")
        if not password:
            raise ValueError("Password cannot be empty or None.")

        creds = f"{user_id}:{password}"
        encoded_creds = base64.b64encode(creds.encode()).decode()

        LOGGER.info(f"New login attempt for user: {user_id}")

        headers = {"Authorization": f"Basic {encoded_creds}"}

        url: str = f"{self.base_url}/users/{user_id}/login"

        try:
            response = requests.post(url, headers=headers)
            response.raise_for_status()
            LOGGER.info(f"Login sucessful for user: {user_id}")
        except requests.RequestException as exc:
            raise ApiClientError(f"Login request failed: {exc}") from exc

        data: Dict[str, Any] = response.json()
        if "token" not in data:
            raise ApiClientError("Login response did not contain a 'token' field.")
        self.auth_token = data["token"]

        return self.auth_token

    def get_bank_accounts(self, user_id: str) -> List[str]:
        """
        Retrieves the list of bank accounts for the specified user via
        GET /users/{userId}/bank-accounts/.

        :raises ValueError: If user_id is empty/None.
        :raises ApiClientError: If not logged in, or request fails.
        """
        if not user_id:
            raise ValueError("User ID cannot be empty or None.")
        if not self.auth_token:
            raise ApiClientError("Cannot get bank accounts before logging in.")

        url: str = f"{self.base_url}/users/{user_id}/bank-accounts/"
        headers: Dict[str, str] = {"Authorization": f"Bearer {self.auth_token}"}

        LOGGER.info(f"Requesting IBANs of user: {user_id}")

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise ApiClientError(f"Get bank accounts request failed: {exc}") from exc

        data: Dict[str, Any] = response.json()

        ibans = []
        ibans = data.get("ibanList", [])
        LOGGER.info(f"IBANs of {user_id}: {ibans}")
        return ibans

    def update_bank_account(self, user_id: str, iban: str) -> Dict[str, Any]:
        """
        Updates a bank account via PUT /users/{userId}/bank-accounts/{iban}.

        :raises ValueError: If user_id or iban is empty/None, or if iban is invalid.
        :raises ApiClientError: If not logged in, or request fails.
        """
        if not user_id:
            raise ValueError("User ID cannot be empty or None.")
        if not iban:
            raise ValueError("IBAN cannot be empty or None.")

        try:
            IBAN(iban)
        except SchwiftyException as exc:
            raise ValueError(f"The provided IBAN ({iban}) is invalid: {exc}")

        if not self.auth_token:
            raise ApiClientError("Cannot update a bank account before logging in.")

        url: str = f"{self.base_url}/users/{user_id}/bank-accounts/{iban}"
        headers: Dict[str, str] = {"Authorization": f"Bearer {self.auth_token}"}

        try:
            response = requests.put(url, headers=headers)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise ApiClientError(f"Update bank account request failed: {exc}") from exc

        response_message: Dict[str, Any] = response.json()
        return response_message
