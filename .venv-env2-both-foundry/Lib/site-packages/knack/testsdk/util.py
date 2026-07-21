# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import math
import base64

from .exceptions import CliTestError


def find_recording_dir(test_file):
    return os.path.join(os.path.dirname(test_file), 'recordings')


def create_random_name(prefix='clitest', length=24):
    if len(prefix) > length:
        raise CliTestError('The length of the prefix must not be longer than random name length')

    padding_size = length - len(prefix)
    if padding_size < 4:
        raise CliTestError('The randomized part of the name is shorter than 4, which may not be able to offer enough '
                           'randomness')

    random_bytes = os.urandom(int(math.ceil(float(padding_size) / 8) * 5))
    random_padding = base64.b32encode(random_bytes)[:padding_size]

    return str(prefix + random_padding.decode().lower())
