# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import os.path

from azure.cli.core.util import CLIError
import azure.cli.core.azlogging as azlogging
import azure.cli.core.keys as keys

logger = azlogging.get_az_logger(__name__)


def validate_ssh_key(namespace):
    string_or_file = (namespace.ssh_key_value or
                      os.path.join(os.path.expanduser('~'), '.ssh', 'id_rsa.pub'))
    content = string_or_file
    if os.path.exists(string_or_file):
        logger.info('Use existing SSH public key file: %s', string_or_file)
        with open(string_or_file, 'r') as f:
            content = f.read()
    elif not keys.is_valid_ssh_rsa_public_key(content):
        if namespace.generate_ssh_keys:
            # figure out appropriate file names:
            # 'base_name'(with private keys), and 'base_name.pub'(with public keys)
            public_key_filepath = string_or_file
            if public_key_filepath[-4:].lower() == '.pub':
                private_key_filepath = public_key_filepath[:-4]
            else:
                private_key_filepath = public_key_filepath + '.private'
            content = keys.generate_ssh_keys(private_key_filepath, public_key_filepath)
            logger.warning("SSH key files '%s' and '%s' have been generated under ~/.ssh to "
                           "allow SSH access to the VM. If using machines without "
                           "permanent storage like Azure Cloud Shell without an attached "
                           "file share, back up your keys to a safe location",
                           private_key_filepath, public_key_filepath)
        else:
            raise CLIError('An RSA key file or key value must be supplied to SSH Key Value. '
                           'You can use --generate-ssh-keys to let CLI generate one for you')
    namespace.ssh_key_value = content


def validate_create_parameters(namespace):
    if not namespace.name:
        raise CLIError('--name has no value')
    if namespace.dns_name_prefix is not None and not namespace.dns_name_prefix:
        raise CLIError('--dns-prefix has no value')
