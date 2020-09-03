# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


import base64
import hashlib
import secrets

from cryptography.hazmat.primitives.serialization import Encoding


class Utils:
    @staticmethod
    def convert_to_uint16(b: bytearray):
        ret = [0 for _ in range(len(b) // 2)]
        for i in range(0, len(b), 2):
            tmp = bytearray()
            tmp.append(b[i])
            tmp.append(b[i + 1])

            # It's already in the same byte order
            # as the system that encrypted it, so don't reverse it
            ret[i // 2] = (b[i + 1] << 8) | b[i]  # TODO

        return ret

    @staticmethod
    def get_random(cb):
        ret = bytearray()
        for i in range(cb):
            ret.append(secrets.randbits(8))
        return ret

    @staticmethod
    def get_SHA256_thumbprint(cert):
        public_bytes = cert.public_bytes(Encoding.DER)
        return hashlib.sha256(public_bytes).digest()

    @staticmethod
    def security_domain_b64_url_encode_for_x5c(s):
        return base64.b64encode(s).decode('ascii')

    @staticmethod
    def security_domain_b64_url_encode(s):
        return base64.b64encode(s).decode('ascii').strip('=').replace('+', '-').replace('/', '_')


if __name__ == '__main__':
    b = bytearray()
    b.extend(b'swadawdawd')
    x = Utils.convert_to_uint16(b)
    print(x)
