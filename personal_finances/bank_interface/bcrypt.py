from .password_handler import Password_handler
import bcrypt


class Encription(Password_handler):
    def password_match(self, recv_password: str, stored_password: str) -> bool:
        if bcrypt.checkpw(
            recv_password.encode("utf-8"), stored_password.encode("utf-8")
        ):
            return True
        else:
            return False

    def create_user_hash_password(self, password: str) -> bytes:
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt())
