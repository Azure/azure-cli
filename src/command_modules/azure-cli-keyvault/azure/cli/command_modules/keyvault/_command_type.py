#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

import base64

from msrest.paging import Paged
from msrest.exceptions import ValidationError
from msrestazure.azure_operation import AzureOperationPoller

from azure.cli.core.commands import command_table, CliCommand, LongRunningOperation
from azure.cli.core.commands._introspection import \
    (extract_full_summary_from_signature, extract_args_from_signature)
from azure.cli.core._profile import Profile
from azure.cli.core._util import CLIError

from azure.cli.command_modules.keyvault.convenience import KeyVaultClient, KeyVaultAuthentication
from azure.cli.command_modules.keyvault.keyvaultclient.models import KeyVaultErrorException

def _encode_hex(item):
    """ Recursively crawls the object structure and converts bytes or bytearrays to base64
    encoded strings. """
    if isinstance(item, list):
        return [_encode_hex(x) for x in item]
    elif hasattr(item, '__dict__'):
        for key, val in item.__dict__.items():
            item.__dict__[key] = _encode_hex(val)
        return item
    elif isinstance(item, bytes) or isinstance(item, bytearray):
        return base64.b64encode(item).decode('utf-8')
    else:
        return item

def _create_key_vault_command(name, operation, transform_result, table_transformer):

    def _execute_command(kwargs):

        try:

            def get_token(server, resource, scope): # pylint: disable=unused-argument
                return Profile().get_login_credentials(resource)[0]._token_retriever() # pylint: disable=protected-access

            client = KeyVaultClient(KeyVaultAuthentication(get_token))
            result = operation(client, **kwargs)

            # apply results transform if specified
            if transform_result:
                return _encode_hex(transform_result(result))

            # otherwise handle based on return type of results
            if isinstance(result, AzureOperationPoller):
                return _encode_hex(LongRunningOperation('Starting {}'.format(name))(result))
            elif isinstance(result, Paged):
                try:
                    return _encode_hex(list(result))
                except TypeError:
                    # TODO: Workaround for an issue in either KeyVault server-side or msrest
                    # See https://github.com/Azure/autorest/issues/1309
                    return []
            else:
                return _encode_hex(result)
        except (ValidationError, KeyVaultErrorException) as ex:
            try:
                raise CLIError(ex.inner_exception.error.message)
            except AttributeError:
                raise CLIError(ex)

    name = ' '.join(name.split())
    cmd = CliCommand(name, _execute_command, table_transformer=table_transformer)
    cmd.description = extract_full_summary_from_signature(operation)
    cmd.arguments.update(extract_args_from_signature(operation))
    return cmd

def cli_keyvault_data_plane_command(
        name, operation, transform=None, table_transformer=None):
    """ Registers an Azure CLI KeyVault Data Plane command. These commands must respond to a
    challenge from the service when they make requests. """
    command = _create_key_vault_command(name, operation, transform, table_transformer)
    command_table[command.name] = command
