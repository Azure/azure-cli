# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


import hashlib
import hmac


class KDF:
    @staticmethod
    def to_big_endian_32bits(value):
        result = bytearray()
        result.append((value & 0xFF000000) >> 24)
        result.append((value & 0x00FF0000) >> 16)
        result.append((value & 0x0000FF00) >> 8)
        result.append(value & 0x000000FF)
        return result

    @staticmethod
    def to_big_endian_64bits(value):
        result = bytearray()
        result.append((value & 0xFF00000000000000) >> 56)
        result.append((value & 0x00FF000000000000) >> 48)
        result.append((value & 0x0000FF0000000000) >> 40)
        result.append((value & 0x000000FF00000000) >> 32)
        result.append((value & 0x00000000FF000000) >> 24)
        result.append((value & 0x0000000000FF0000) >> 16)
        result.append((value & 0x000000000000FF00) >> 8)
        result.append(value & 0x00000000000000FF)
        return result

    @staticmethod
    def test_sp800_108():
        label = 'label'
        context = 'context'
        bit_length = 256
        hex_result = 'f0ca51f6308791404bf68b56024ee7c64d6c737716f81d47e1e68b5c4e399575'
        key = bytearray()
        key.extend([0x41] * 32)

        new_key = KDF.sp800_108(key, label, context, bit_length)
        hex_value = new_key.hex().replace('-', '')
        return hex_value.lower() == hex_result

    @staticmethod
    def sp800_108(key_in: bytearray, label: str, context: str, bit_length):
        """
        Note - initialize out to be the number of bytes of keying material that you need
        This implements SP 800-108 in counter mode, see section 5.1

        Fixed values:
            1. h - The length of the output of the PRF in bits, and
            2. r - The length of the binary representation of the counter i.

        Input: KI, Label, Context, and L.

        Process:
            1. n := ⎡L/h⎤.
            2. If n > 2^(r-1), then indicate an error and stop.
            3. result(0):= ∅.
            4. For i = 1 to n, do
                a. K(i) := PRF (KI, [i]2 || Label || 0x00 || Context || [L]2)
                b. result(i) := result(i-1) || K(i).

            5. Return: KO := the leftmost L bits of result(n).
        """

        if bit_length <= 0 or bit_length % 8 != 0:
            return None

        L = bit_length
        bytes_needed = bit_length // 8
        hMAC = hmac.HMAC(key_in, digestmod=hashlib.sha512)
        hash_bits = hMAC.digest_size
        n = L // hash_bits
        if L % hash_bits != 0:
            n += 1

        hmac_data_suffix = bytearray()
        hmac_data_suffix.extend(label.encode('UTF-8'))
        hmac_data_suffix.append(0)
        hmac_data_suffix.extend(context.encode('UTF-8'))
        hmac_data_suffix.extend(KDF.to_big_endian_32bits(bit_length))

        out_value = bytearray()
        for i in range(n):
            hmac_data = bytearray()
            hmac_data.extend(KDF.to_big_endian_32bits(i + 1))
            hmac_data.extend(hmac_data_suffix)
            hMAC.update(hmac_data)
            hash_value = hMAC.digest()

            if bytes_needed > len(hash_value):
                out_value.extend(hash_value)
                bytes_needed -= len(hash_value)
            else:
                out_value.extend(hash_value[len(out_value): len(out_value) + bytes_needed])
                return out_value

        return None


if __name__ == '__main__':
    print(KDF.test_sp800_108())
