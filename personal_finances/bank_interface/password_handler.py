from abc import ABC, abstractmethod

USER_PASSWORD_MIN_LEN = 6


class Password_handler(ABC):
    @abstractmethod
    def password_match(self, recv_password: str, stored_password: str) -> bool:
        """
        Checks if received password matches with stored one
        """
        pass

    @abstractmethod
    def create_user_hash_password(self, password: str) -> bytes:
        """
        Generates the user's hash from a string input
        """
    pass
