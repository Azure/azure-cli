# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import secrets


class ModMath:
    @staticmethod
    def reduce(x):
        t = (x & 0xff) - (x >> 8)
        t += (t >> 31) & 257
        return t

    @staticmethod
    def multiply(x, y):
        return ModMath.reduce(x * y)

    @staticmethod
    def invert(x):
        ret = x
        for _ in range(7):
            ret = ModMath.multiply(ret, ret)
            ret = ModMath.multiply(ret, x)
        return ret

    @staticmethod
    def add(x, y):
        return ModMath.reduce(x + y)

    @staticmethod
    def subtract(x, y):
        return ModMath.reduce(x - y + 257)

    @staticmethod
    def get_random():
        return ModMath.reduce(secrets.randbits(16))
