import base64
import struct

rounds = 20000


def pack_to_bytes(data):
    if isinstance(data, int):
        # Perl pack('N', ...) is 32-bit big-endian (https://perldoc.perl.org/functions/pack)
        # It translates to `>I` in Python struct.pack (https://docs.python.org/3/library/struct.html#format-strings)
        return base64.b64encode(struct.pack(">I", data))
    else:
        raise ValueError(f"Unsupported value type: " + type(data))


def pack_to_string(data):
    return pack_to_bytes(data).decode("ascii")


print(pack_to_bytes(rounds))
print(pack_to_string(rounds))
