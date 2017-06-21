# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os

from azure.cli.core.application import APPLICATION
import azure.cli.core.azlogging as azlogging

logger = azlogging.get_az_logger(__name__)


def _generate_ssh_keys(private_key_filepath, public_key_filepath):
    import paramiko

    ssh_dir, _ = os.path.split(private_key_filepath)
    if not os.path.exists(ssh_dir):
        os.makedirs(ssh_dir)
        os.chmod(ssh_dir, 0o700)

    key = paramiko.RSAKey.generate(2048)
    key.write_private_key_file(private_key_filepath)
    os.chmod(private_key_filepath, 0o600)

    with open(public_key_filepath, 'w') as public_key_file:
        public_key = '%s %s' % (key.get_name(), key.get_base64())
        public_key_file.write(public_key)
    os.chmod(public_key_filepath, 0o644)

    return public_key


def _is_valid_ssh_rsa_public_key(openssh_pubkey):
    # http://stackoverflow.com/questions/2494450/ssh-rsa-public-key-validation-using-a-regular-expression
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


def _handle_container_ssh_file(**kwargs):
    if kwargs['command'] != 'acs create':
        return

    args = kwargs['args']
    string_or_file = args.ssh_key_value
    content = string_or_file
    if os.path.exists(string_or_file):
        logger.info('Use existing SSH public key file: %s', string_or_file)
        with open(string_or_file, 'r') as f:
            content = f.read()
    elif not _is_valid_ssh_rsa_public_key(content) and args.generate_ssh_keys:
        # figure out appropriate file names:
        # 'base_name'(with private keys), and 'base_name.pub'(with public keys)
        public_key_filepath = string_or_file
        if public_key_filepath[-4:].lower() == '.pub':
            private_key_filepath = public_key_filepath[:-4]
        else:
            private_key_filepath = public_key_filepath + '.private'
        content = _generate_ssh_keys(private_key_filepath, public_key_filepath)
        logger.warning('Created SSH key files: %s,%s', private_key_filepath, public_key_filepath)
    args.ssh_key_value = content


APPLICATION.register(APPLICATION.COMMAND_PARSER_PARSED, _handle_container_ssh_file)
