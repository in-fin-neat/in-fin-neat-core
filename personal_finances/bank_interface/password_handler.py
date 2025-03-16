import argon2
import logging

USER_PASSWORD_MIN_LEN = 6
LOGGER = logging.getLogger(__name__)


def password_match(recv_password: str, stored_password: str) -> bool:
    LOGGER.info("Argon2 comparisson start")
    try:
        argon2.PasswordHasher().verify(
            stored_password.encode("utf-8"), recv_password.encode("utf-8")
        )
        return True
    except argon2.exceptions.VerifyMismatchError:
        return False
    except Exception as e:
        LOGGER.info(f"Argon2 comparisson error:{e}")
        return False


def create_hash_password(password: str) -> bytes:
    return argon2.PasswordHasher(
        memory_cost=32768).hash(password.encode()).encode("utf-8")
