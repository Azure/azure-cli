# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import secrets
import time

from knack.util import CLIError
from azure.cli.command_modules.keyvault.security_domain.shared_secret import SharedSecret


def single_byte_test(shares, required):
    for i in range(0x100):
        secret = SharedSecret(shares, required)
        share_array = secret.make_byte_shares(i)
        result = SharedSecret.get_secret_byte(share_array, required)
        if i != result:
            raise CLIError('single_byte_test failed.')


def test_126_shares():
    shares = 126
    print('[Running] 126 share test.')

    # python is much slower than other languages, so only do every 4th number
    # if you want to test every possible combination, then change inc to -1
    inc = -4
    for required in range(shares, 1, inc):
        print('\tshares={}, required={}'.format(shares, required))
        single_byte_test(shares, required)

    print('[Success] 126 share test.')


def test_all_shares():
    # When testing other languages, this goes up to 127 shares, and 16 required
    # to do full testing, change max_shares and max_required
    print('[Running] all share test.')
    max_shares = 30
    for shares in range(2, max_shares):
        max_required = 10
        print('\tshares={}'.format(shares))

        if shares > max_required:
            limit = max_required
        else:
            limit = shares

        for required in range(limit, 1, -1):
            print('\tshares={}, required={}'.format(shares, required))
            single_byte_test(shares, required)

    print('[Success] all share test.')


def perf_test():
    shares = 40
    required = 16
    then = time.time_ns()
    single_byte_test(shares, required)
    print('Total elapsed = {}'.format(time.time_ns() - then))


def random_single_byte_test():
    # note - in C++ and C#, this is 126 shares, 16 required, and 100000 iterations
    shares = 30
    required = 10
    iterations = 1000

    for i in range(iterations):
        # just use i % 256 as the secret
        secret_value = i % 256
        secret = SharedSecret(shares, required)
        share_array = secret.make_byte_shares(secret_value)

        tmp_array = share_array
        random_shares = []

        for j in range(required):
            r = secrets.randbits(8)
            pos = r % len(tmp_array)
            val = tmp_array[pos]
            random_shares.append(val)
            tmp_array.remove(val)

        result = SharedSecret.get_secret_byte(random_shares, required)

        if result != secret_value:
            raise CLIError('random_single_byte_test failed')


def check_result(a, b):
    # not for cryptographic purposes
    # assumes equal length inputs
    for i in range(len(a)):
        if a[i] != b[i]:
            return False
    return True


def test_large_secret():
    # note, because Python is so much slower, only doing
    # 1000 iterations, not 1 million
    iterations = 1000
    shares = 11
    required = 5
    secret_size = 32

    for i in range(iterations):
        ss = SharedSecret(shares, required)

        # in order to make debugging a bit easier,
        # start with a known plaintext, not random
        secret = bytearray(32)
        if i == 0:
            for x in range(32):
                secret[x] = 0x41 + x
        else:
            # randbits returns an int, not an array of bytes
            tmp = secrets.randbits(secret_size*8)

            # Let's convert it
            secret = tmp.to_bytes(secret_size, 'little')

        share_arrays = ss.make_shares(secret)
        plaintext = SharedSecret.get_plaintext(share_arrays, required)

        if not check_result(secret, plaintext):
            raise CLIError('test_large_secret failed')

        if (i + 1) % (iterations // 10) == 0:
            print('{} iterations'.format(i + 1))

    print('[Success] test_large_secret')


def run_all_tests():
    # As it turns out, the Python code is 274 times slower than
    # the C# or C++ implementation. It's all in the math, which is a LOT
    # slower than even managed code.

    # As a result, tests that run in 15 seconds take about an hour and 15
    # minutes, which is much too long. So we're going to cut back on the
    # tests. If you want to run them all, feel free to uncomment below.

    print('Running single-byte tests')
    # print("Testing 126 shares, 2-126 required")
    test_126_shares()

    print('\nTesting up to 30 shares, 2-10 required')
    test_all_shares()

    # This can be used to do performance analysis
    perf_test()

    print('\nRandom single-byte test')
    random_single_byte_test()

    print('\nTesting large secrets')
    test_large_secret()


if __name__ == '__main__':
    run_all_tests()
