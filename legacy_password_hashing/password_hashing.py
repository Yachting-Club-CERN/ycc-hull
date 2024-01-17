"""
YCC Legacy Password Hashing
"""
import base64
import logging
import re
import struct
from re import Match, Pattern

from passlib.handlers.pbkdf2 import ldap_pbkdf2_sha1
from passlib.utils.handlers import PrefixWrapper


def _create_hasher() -> PrefixWrapper:
    return ldap_pbkdf2_sha1.using(rounds=20000, salt_size=16)


_logger = logging.getLogger(__name__)

# In Python format:
# {PBKDF2}20000$2/u/l7J2zpnTmlMqBQDgnA$89AeSFShUfrxB6guLEi7CUiTL8c
_PYTHON_HASH_FORMAT_RE: Pattern = re.compile(r"^{PBKDF2}(\d+)[$](.+)[$](.+)$")

# In YCC format, compatible with Enrico's PERL applications:
# {PBKDF2-X}HMACSHA1:AABOIA:2/u/l7J2zpnTmlMqBQDgnA:89AeSFShUfrxB6guLEi7CUiTL8c
_PERL_HASH_FORMAT_RE: Pattern = re.compile(r"^{X-PBKDF2}HMACSHA1:(.+)[:](.+)[:](.+)$")

_HASHER: PrefixWrapper = _create_hasher()

_ERROR_PASSWORD_NOT_STRING = "The password must be a string"
_ERROR_HASH_NOT_STRING = "The hash must be a string"


def hash_ycc_password(password: str) -> str:
    """
    Hashes a YCC legacy password.

    Args:
        password (str): password

    Returns:
        str: password hash
    """
    if not isinstance(password, str):
        raise ValueError(_ERROR_PASSWORD_NOT_STRING)

    return _hash_to_perl(_HASHER.hash(password))


def verify_ycc_password(password: str, password_hash: str) -> bool:
    """
    Verifies a YCC legacy password.

    Args:
        password (str): password
        password_hash (str): password hash

    Returns:
        bool: verification result
    """
    if not isinstance(password, str):
        raise ValueError(_ERROR_PASSWORD_NOT_STRING)
    if not isinstance(password_hash, str):
        raise ValueError(_ERROR_HASH_NOT_STRING)

    return _HASHER.verify(password, _hash_to_python(password_hash))


def _hash_to_perl(python_hash: str) -> str:
    if not isinstance(python_hash, str):
        raise ValueError(_ERROR_HASH_NOT_STRING)

    # . => +: from LDAP BASE64 format
    match: Match | None = _PYTHON_HASH_FORMAT_RE.search(python_hash.replace(".", "+"))
    if not match:
        _logger.debug("The Python hash seems invalid: %s", python_hash)
        raise ValueError("The Python hash seems invalid")

    rounds: str = _pack(int(match.group(1))).replace(
        "=", ""
    )  # Legacy code removes padding
    return f"{{X-PBKDF2}}HMACSHA1:{rounds}:{match.group(2)}:{match.group(3)}"


def _hash_to_python(perl_hash: str) -> str:
    if not isinstance(perl_hash, str):
        raise ValueError(_ERROR_HASH_NOT_STRING)

    # . => +: from LDAP BASE64 format
    match: Match | None = _PERL_HASH_FORMAT_RE.search(perl_hash.replace("+", "."))
    if not match:
        _logger.debug("The Perl hash seems invalid: %s", perl_hash)
        raise ValueError("The Perl hash seems invalid")

    rounds: int = _unpack_int(match.group(1) + "==")  # Legacy code removes padding
    return f"{{PBKDF2}}{rounds}${match.group(2)}${match.group(3)}"


def _pack(data: int) -> str:
    if isinstance(data, int):
        # Perl pack('N', ...) is 32-bit big-endian (https://perldoc.perl.org/functions/pack)
        # It translates to `>I` in Python struct.pack (https://docs.python.org/3/library/struct.html#format-strings)
        return base64.b64encode(struct.pack(">I", data)).decode("ascii")
    raise ValueError(f"Unsupported value type: {type(data)}")


def _unpack_int(data: str) -> int:
    if not isinstance(data, str):
        raise ValueError("The data must be a string")

    return struct.unpack(">I", base64.b64decode(data.encode("ascii")))[0]
