# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os

from azure.cli.core.application import APPLICATION
from azure.cli.core.keys import generate_ssh_keys
from azure.cli.core.keys import is_valid_ssh_rsa_public_key
import azure.cli.core.azlogging as azlogging

logger = azlogging.get_az_logger(__name__)


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
    elif not is_valid_ssh_rsa_public_key(content) and args.generate_ssh_keys:
        # figure out appropriate file names:
        # 'base_name'(with private keys), and 'base_name.pub'(with public keys)
        public_key_filepath = string_or_file
        if public_key_filepath[-4:].lower() == '.pub':
            private_key_filepath = public_key_filepath[:-4]
        else:
            private_key_filepath = public_key_filepath + '.private'
        content = generate_ssh_keys(private_key_filepath, public_key_filepath)
        logger.warning('Created SSH key files: %s,%s', private_key_filepath, public_key_filepath)
    args.ssh_key_value = content


APPLICATION.register(APPLICATION.COMMAND_PARSER_PARSED, _handle_container_ssh_file)
