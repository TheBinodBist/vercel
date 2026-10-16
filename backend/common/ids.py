import re
import secrets

ID_LENGTH = 5
ID_ALPHABET = "123456789qwertyuiopasdfghjklzxcvbnm"
ID_RE = re.compile(r"^[1-9a-z]{%d}$" % ID_LENGTH)


def generate_id() -> str:
    return "".join(secrets.choice(ID_ALPHABET) for _ in range(ID_LENGTH))


def is_valid_id(value: str) -> bool:
    return bool(value) and ID_RE.match(value) is not None
