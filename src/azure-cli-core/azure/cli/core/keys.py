# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import os.path

from knack.util import CLIError
from knack.log import get_logger
logger = get_logger(__name__)


def is_valid_ssh_rsa_public_key(openssh_pubkey):
    # http://stackoverflow.com/questions/2494450/ssh-rsa-public-key-validation-using-a-regular-expression # pylint: disable=line-too-long
    # A "good enough" check is to see if the key starts with the correct header.
    import struct
    try:
        from base64 import decodebytes as base64_decode
    except ImportError:
        # deprecated and redirected to decodebytes in Python 3
        from base64 import decodestring as base64_decode

    parts = openssh_pubkey.split()
    if len(parts) < 2:
        return False
    key_type = parts[0]
    key_string = parts[1]

    data = base64_decode(key_string.encode())  # pylint:disable=deprecated-method
    int_len = 4
    str_len = struct.unpack('>I', data[:int_len])[0]  # this should return 7
    return data[int_len:int_len + str_len] == key_type.encode()


def generate_ssh_keys(private_key_filepath, public_key_filepath):
    import paramiko
    from paramiko.ssh_exception import PasswordRequiredException, SSHException

    if os.path.isfile(public_key_filepath):
        try:
            with open(public_key_filepath, 'r') as public_key_file:
                public_key = public_key_file.read()
                pub_ssh_dir = os.path.dirname(public_key_filepath)
                logger.warning("Public SSH key file '%s' already exists in the directory: '%s'. "
                               "New SSH key files will not be generated.",
                               public_key_filepath, pub_ssh_dir)

                return public_key
        except IOError as e:
            raise CLIError(e)

    ssh_dir = os.path.dirname(private_key_filepath)
    if not os.path.exists(ssh_dir):
        os.makedirs(ssh_dir)
        os.chmod(ssh_dir, 0o700)

    if os.path.isfile(private_key_filepath):
        # try to use existing private key if it exists.
        try:
            key = paramiko.RSAKey(filename=private_key_filepath)
            logger.warning("Private SSH key file '%s' was found in the directory: '%s'. "
                           "We will generate a paired public key file '%s'",
                           private_key_filepath, ssh_dir, public_key_filepath)
        except (PasswordRequiredException, SSHException, IOError) as e:
            raise CLIError(e)

    else:
        # otherwise generate new private key.
        key = paramiko.RSAKey.generate(2048)
        key.write_private_key_file(private_key_filepath)
        os.chmod(private_key_filepath, 0o600)

    with open(public_key_filepath, 'w') as public_key_file:
        public_key = '{} {}'.format(key.get_name(), key.get_base64())
        public_key_file.write(public_key)
    os.chmod(public_key_filepath, 0o644)

    return public_key
