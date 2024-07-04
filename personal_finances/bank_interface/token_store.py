from abc import ABC, abstractmethod
from copy import deepcopy
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from nordigen.types import TokenType


class TokenObject(BaseModel):
    AccessToken: str
    AccessExpires: int
    RefreshToken: str
    RefreshExpires: int
    CreationEpoch: int
    AccessRefreshEpoch: int


class GocardlessAccessToken(BaseModel):
    access: str
    access_expires: int


def gocardless_token_adapter(gocardless_token: TokenType) -> TokenObject:
    token_dict = {
        "AccessToken": gocardless_token["access"],
        "AccessExpires": gocardless_token["access_expires"],
        "RefreshToken": gocardless_token["refresh"],
        "RefreshExpires": gocardless_token["refresh_expires"],
        "CreationEpoch": int(datetime.now().timestamp()),
        "AccessRefreshEpoch": int(datetime.now().timestamp()),
    }
    return TokenObject.model_validate(token_dict)


def gocardless_update_access_token(
    access_token: GocardlessAccessToken, existing_token_object: TokenObject
) -> TokenObject:
    new_token_object = deepcopy(existing_token_object)
    new_token_object.AccessToken = access_token.access
    new_token_object.AccessExpires = access_token.access_expires
    new_token_object.AccessRefreshEpoch = int(datetime.now().timestamp())
    return new_token_object


class TokenNotFound(Exception):
    pass


class TokenStore(ABC):
    @abstractmethod
    def save_token(self, user_id: str, token: TokenObject) -> Optional[TokenObject]:
        """
        Saves the new token and returns the older one
        """
        pass

    @abstractmethod
    def get_last_token(self, user_id: str) -> TokenObject:
        """
        Retrieves the last token from the store for a given user id
        """
        pass

    def is_access_token_valid(self, user_id: str) -> bool:
        """
        Checks whether the access token is not expired
        """
        try:
            last_token = self.get_last_token(user_id)
        except TokenNotFound:
            return False

        now_epoch = int(datetime.now().timestamp())
        return (last_token.AccessRefreshEpoch + last_token.AccessExpires) > now_epoch

    def is_refresh_token_valid(self, user_id: str) -> bool:
        """
        Checks whether the refresh token is not expired
        """
        try:
            last_token = self.get_last_token(user_id)
        except TokenNotFound:
            return False

        now_epoch = int(datetime.now().timestamp())
        return (last_token.CreationEpoch + last_token.RefreshExpires) > now_epoch
