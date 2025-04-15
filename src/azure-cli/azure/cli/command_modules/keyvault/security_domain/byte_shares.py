# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import array

from azure.cli.command_modules.keyvault.security_domain.mod_math import ModMath


class Share:
    def __init__(self, x, v):
        self.x = x
        self.v = v

    @staticmethod
    def from_uint16(w):
        x = w >> 9
        v = w & 0x1ff
        return Share(x, v)

    def to_uint16(self):
        return (self.x << 8) | self.v


class ByteShares:
    def __init__(self, required, secret_byte):
        self.coefficients = ByteShares.init_coefficients(required, secret_byte)

    @staticmethod
    def init_coefficients(required, secret_byte):
        coefficients = array.array('H')
        for _ in range(required - 1):
            coefficients.append(ModMath.get_random())
        coefficients.append(secret_byte)
        return coefficients

    def set_secret_byte(self, secret_byte):
        self.coefficients[-1] = secret_byte

    def make_share(self, x):
        v = ModMath.multiply(self.coefficients[0], x)
        v = ModMath.add(v, self.coefficients[1])

        for i in range(2, len(self.coefficients)):
            v = ModMath.multiply(v, x)
            v = ModMath.add(v, self.coefficients[i])
        return Share(x, v)

    @staticmethod
    def get_secret(shares, required):
        secret = 0
        for i in range(required):
            numerator = denominator = 1
            si = Share.from_uint16(shares[i])
            for j in range(required):
                if i == j:
                    continue
                sj = Share.from_uint16(shares[j])
                numerator = ModMath.multiply(numerator, sj.x)
                diff = ModMath.subtract(sj.x, si.x)
                denominator = ModMath.multiply(diff, denominator)

            invert = ModMath.invert(denominator)
            ci = ModMath.multiply(numerator, invert)
            tmp = ModMath.multiply(ci, si.v)
            secret = ModMath.add(secret, tmp)

        return secret
