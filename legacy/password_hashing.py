import base64
import hashlib
import hmac


def pack_to_bytes(data):
    if isinstance(data, int):
        # Perl pack('N', ...) is 32-bit big-endian (https://perldoc.perl.org/functions/pack)
        # It translates to `>I` in Python struct.pack (https://docs.python.org/3/library/struct.html#format-strings)
        return base64.b64encode(struct.pack('>I', data))
    else:
        raise ValueError(f"Unsupported value type: " + type(data))


def pack_to_string(data):
    return pack_to_bytes(data).decode('ascii')


def make_digest(key):
    key = bytes(key, 'UTF-8')

    digester = hmac.new(key, digestmod=hashlib.sha1)
    # signature1 = digester.hexdigest()
    signature1 = digester.digest()
    print(signature1)

    # signature2 = base64.urlsafe_b64encode(bytes(signature1, 'UTF-8'))
    signature2 = base64.urlsafe_b64encode(signature1)
    print(signature2)

    return str(signature2, 'UTF-8')


# Should look like:
# {X-PBKDF2}HMACSHA1:AABOIA:y/iWFIvSvhe0t5jt6W/z0Q==:JXIxxwwAuy0b5YuXAJyowg9fSjs=
# {X-PBKDF2}HMACSHA1:AABOIA:RWJwnlX8dsOYaQ8XBYMwlg==:8ixd6tYwE6lReOYIQhoEVsZx7Gg=

result = make_digest('changeit')
print(result)

# say('Check : ' . check_password("{X-PBKDF2}HMACSHA1:AABOIA:Kl1+1gliqTf0pMw+CEytmQ==:pLWyngX+mGuHIBYmcqIk/3ELdDo=", "abc"))
