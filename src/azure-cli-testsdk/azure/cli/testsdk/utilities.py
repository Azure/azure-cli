# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import uuid
import datetime
import hashlib


def create_random_name(prefix='clitest', length=24):
    if len(prefix) > length:
        raise 'The length of the prefix must not be longer than random name length'

    identity = '{}-{}'.format(str(uuid.getnode()),
                              datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S%f')).encode('utf-8')
    prefix += str(hashlib.sha256(identity).hexdigest())
    return prefix[:length]


def get_sha1_hash(file_path):
    sha1 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        while True:
            data = f.read(65536)
            if not data:
                break
            sha1.update(data)

    return sha1.hexdigest()
