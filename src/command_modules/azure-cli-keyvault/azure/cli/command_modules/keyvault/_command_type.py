# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import base64
from six import string_types

from azure.cli.core.commands import (command_table,
                                     command_module_map,
                                     CliCommand,
                                     LongRunningOperation,
                                     get_op_handler)
from azure.cli.core.commands._introspection import \
    (extract_full_summary_from_signature, extract_args_from_signature)

from azure.cli.core.util import CLIError


def _encode_hex(item):
    """ Recursively crawls the object structure and converts bytes or bytearrays to base64
    encoded strings. """
    if isinstance(item, list):
        return [_encode_hex(x) for x in item]
    elif hasattr(item, '__dict__'):
        for key, val in item.__dict__.items():
            if not key.startswith('_'):
                try:
                    setattr(item, key, _encode_hex(val))
                except TypeError:
                    item.__dict__[key] = _encode_hex(val)
        return item
    elif isinstance(item, (bytes, bytearray)):
        return base64.b64encode(item).decode('utf-8')
    return item


def _create_key_vault_command(module_name, name, operation, transform_result, table_transformer):
    if not isinstance(operation, string_types):
        raise ValueError("Operation must be a string. Got '{}'".format(operation))

    def _execute_command(kwargs):
        from msrest.paging import Paged
        from msrest.exceptions import ValidationError, ClientRequestError
        from msrestazure.azure_operation import AzureOperationPoller
        from azure.cli.core._profile import Profile
        from azure.keyvault import KeyVaultClient, KeyVaultAuthentication
        from azure.keyvault.models import KeyVaultErrorException

        try:

            def get_token(server, resource, scope):  # pylint: disable=unused-argument
                import adal
                try:
                    return Profile().get_login_credentials(resource)[0]._token_retriever()  # pylint: disable=protected-access
                except adal.AdalError as err:
                    # pylint: disable=no-member
                    if (hasattr(err, 'error_response') and
                            ('error_description' in err.error_response) and
                            ('AADSTS70008:' in err.error_response['error_description'])):
                        raise CLIError(
                            "Credentials have expired due to inactivity. Please run 'az login'")
                    raise CLIError(err)

            op = get_op_handler(operation)
            # since the convenience client can be inconvenient, we have to check and create the
            # correct client version
            client = KeyVaultClient(KeyVaultAuthentication(get_token))
            result = op(client, **kwargs)

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
        except ClientRequestError as ex:
            if 'Failed to establish a new connection' in str(ex.inner_exception):
                raise CLIError('Max retries exceeded attempting to connect to vault. '
                               'The vault may not exist or you may need to flush your DNS cache '
                               'and try again later.')
            raise CLIError(ex)

    command_module_map[name] = module_name
    name = ' '.join(name.split())

    def arguments_loader():
        return extract_args_from_signature(get_op_handler(operation))

    def description_loader():
        return extract_full_summary_from_signature(get_op_handler(operation))

    cmd = CliCommand(name, _execute_command, table_transformer=table_transformer,
                     arguments_loader=arguments_loader, description_loader=description_loader)
    return cmd


def cli_keyvault_data_plane_command(
        name, operation, transform=None, table_transformer=None):
    """ Registers an Azure CLI KeyVault Data Plane command. These commands must respond to a
    challenge from the service when they make requests. """
    command = _create_key_vault_command(__name__, name, operation, transform, table_transformer)
    command_table[command.name] = command
