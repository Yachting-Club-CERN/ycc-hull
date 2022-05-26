import base64
import logging
import re
import struct
from re import Match, Pattern

from passlib.handlers.pbkdf2 import ldap_pbkdf2_sha1
from passlib.utils.handlers import PrefixWrapper


def _create_hasher() -> PrefixWrapper:
    return ldap_pbkdf2_sha1.using(rounds=20000, salt_size=16)


_LOG = logging.getLogger("ycc.hull.password")
# In Python format:
# {PBKDF2}20000$2/u/l7J2zpnTmlMqBQDgnA$89AeSFShUfrxB6guLEi7CUiTL8c
_PYTHON_HASH_FORMAT_RE: Pattern = re.compile(r"^{PBKDF2}(\d+)[$](.+)[$](.+)$")
# In YCC format, compatible with Enrico's PERL applications:
# {PBKDF2-X}HMACSHA1:AABOIA:2/u/l7J2zpnTmlMqBQDgnA:89AeSFShUfrxB6guLEi7CUiTL8c
_PERL_HASH_FORMAT_RE: Pattern = re.compile(r"^{X-PBKDF2}HMACSHA1:(.+)[:](.+)[:](.+)$")
_HASHER: PrefixWrapper = _create_hasher()


def hash_ycc_password(password: str) -> str:
    if not isinstance(password, str):
        raise ValueError("The password must be a string")

    return _hash_to_perl(_HASHER.hash(password))


def verify_ycc_password(password: str, password_hash: str) -> bool:
    if not isinstance(password, str):
        raise ValueError("The password must be a string")
    if not isinstance(password_hash, str):
        raise ValueError("The hash must be a string")

    return _HASHER.verify(password, _hash_to_python(password_hash))


def _hash_to_perl(python_hash: str) -> str:
    if not isinstance(python_hash, str):
        raise ValueError("The hash must be a string")

    match: Match = _PYTHON_HASH_FORMAT_RE.search(python_hash)
    if not match:
        _LOG.debug("The Python hash seems invalid: " + python_hash)
        raise ValueError("The Python hash seems invalid")

    rounds: str = _pack(int(match.group(1))).replace("==", "")
    return f"{{X-PBKDF2}}HMACSHA1:{rounds}:{match.group(2)}:{match.group(3)}"


def _hash_to_python(perl_hash: str) -> str:
    if not isinstance(perl_hash, str):
        raise ValueError("The hash must be a string")

    match: Match = _PERL_HASH_FORMAT_RE.search(perl_hash)
    if not match:
        _LOG.debug("The Perl hash seems invalid: " + perl_hash)
        raise ValueError("The Perl hash seems invalid")

    rounds: int = _unpack_int(match.group(1) + "==")
    return f"{{PBKDF2}}{rounds}${match.group(2)}${match.group(3)}"


def _pack(data: int) -> str:
    if isinstance(data, int):
        # Perl pack('N', ...) is 32-bit big-endian (https://perldoc.perl.org/functions/pack)
        # It translates to `>I` in Python struct.pack (https://docs.python.org/3/library/struct.html#format-strings)
        return base64.b64encode(struct.pack(">I", data)).decode("ascii")
    else:
        raise ValueError(f"Unsupported value type: " + type(data))


def _unpack_int(data):
    if not isinstance(data, str):
        raise ValueError("The data must be a string")

    return struct.unpack(">I", base64.b64decode(data.encode("ascii")))[0]


hash1 = hash_ycc_password("changeit")
hash2 = hash_ycc_password("changeit")
hash3 = (
    "{X-PBKDF2}HMACSHA1:AABOIA:NtLCjYMAZ8YIL1RRxh9iEw==:vlo/49hy4tJ/EEQeGrFRtn5RCOc="
)

print(verify_ycc_password("changeit", hash1))
print(verify_ycc_password("changeit", hash2))
print(verify_ycc_password("changeit", hash3))
