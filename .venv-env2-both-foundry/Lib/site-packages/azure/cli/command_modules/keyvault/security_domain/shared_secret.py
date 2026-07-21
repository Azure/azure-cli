# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import array

from knack.util import CLIError
from azure.cli.command_modules.keyvault.security_domain.byte_shares import ByteShares


class SharedSecret:
    max_shares = 126

    def __init__(self, shares=None, required=0):
        if required < 2:
            raise CLIError('Incorrect required count.')

        if shares is None:
            shares = 0
        else:
            if shares > SharedSecret.max_shares or required > shares:
                raise CLIError('Incorrect share or required count.')

        self.shares = shares
        self.required = required
        self.byte_shares = ByteShares(required, 0)

    def make_byte_shares(self, b):
        share_array = []
        self.byte_shares.set_secret_byte(b)

        for x in range(1, self.shares + 1):
            s = self.byte_shares.make_share(x)
            share_array.append(s.to_uint16())

        return share_array

    def make_shares(self, plaintext):
        share_arrays = []
        for i, p in enumerate(plaintext):
            share_array = self.make_byte_shares(p)
            for sa in share_array:
                if i == 0:
                    share_arrays.append(array.array('H'))
                current_share_array = sa
                current_share_array.append(sa)
        return share_arrays

    @staticmethod
    def get_secret_byte(share_array, required):
        if len(share_array) < required:
            raise CLIError('Insufficient shares.')
        return ByteShares.get_secret(share_array, required)

    @staticmethod
    def get_plaintext(share_arrays, required):
        if len(share_arrays) < required:
            raise CLIError('Insufficient shares.')

        plaintext = bytearray()
        plaintext_len = len(share_arrays[0])

        for j in range(plaintext_len):
            sv = array.array('H')
            for i in range(required):
                sa = share_arrays[i]
                sv.append(sa[j])

            text = SharedSecret.get_secret_byte(sv, required)
            plaintext.append(text)

        return plaintext
