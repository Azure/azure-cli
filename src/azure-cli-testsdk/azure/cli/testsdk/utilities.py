# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import hashlib
import math
import os
import base64

from .exceptions import CliTestError


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


def get_sha1_hash(file_path):
    sha1 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        while True:
            data = f.read(65536)
            if not data:
                break
            sha1.update(data)

    return sha1.hexdigest()


def find_recording_dir(test_file):
    """ Find the directory containing the recording of given test file based on current profile. """
    from azure.cli.core._profile import get_active_cloud, init_known_clouds
    from azure.cli.core.cloud import CloudNotRegisteredException
    try:
        api_profile = get_active_cloud().profile
    except CloudNotRegisteredException:
        init_known_clouds()
        api_profile = get_active_cloud().profile

    base_dir = os.path.join(os.path.dirname(test_file), 'recordings')
    return os.path.join(base_dir, api_profile)


def get_active_api_profile():
    from azure.cli.core._profile import get_active_cloud, init_known_clouds
    from azure.cli.core.cloud import CloudNotRegisteredException
    try:
        return get_active_cloud().profile
    except CloudNotRegisteredException:
        init_known_clouds()
        return get_active_cloud().profile
