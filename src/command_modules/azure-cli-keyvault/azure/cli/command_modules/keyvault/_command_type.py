# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import base64

from knack.introspection import extract_full_summary_from_signature, extract_args_from_signature
from knack.util import CLIError

from azure.cli.core.commands import LongRunningOperation, AzCommandGroup, AzArgumentContext


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


def keyvault_exception_handler(ex):
    from msrest.exceptions import ValidationError, ClientRequestError
    from azure.keyvault.models import KeyVaultErrorException
    if isinstance(ex, (ValidationError, KeyVaultErrorException)):
        try:
            raise CLIError(ex.inner_exception.error.message)
        except AttributeError:
            raise CLIError(ex)
    elif isinstance(ex, ClientRequestError):
        if 'Failed to establish a new connection' in str(ex.inner_exception):
            raise CLIError('Max retries exceeded attempting to connect to vault. '
                           'The vault may not exist or you may need to flush your DNS cache '
                           'and try again later.')
        raise CLIError(ex)


class KeyVaultCommandGroup(AzCommandGroup):

    def __init__(self, command_loader, group_name, **kwargs):
        from azure.cli.command_modules.keyvault._client_factory import keyvault_data_plane_factory
        # all regular and custom commands should use the keyvault data plane client
        merged_kwargs = self._merge_kwargs(kwargs, base_kwargs=command_loader.module_kwargs)
        merged_kwargs['custom_command_type'].settings['client_factory'] = keyvault_data_plane_factory
        super(KeyVaultCommandGroup, self).__init__(command_loader, group_name, **kwargs)

    def _create_keyvault_command(self, name, method_name=None, command_type_name=None, **kwargs):
        self._check_stale()

        merged_kwargs = self._flatten_kwargs(kwargs, command_type_name)
        operations_tmpl = merged_kwargs['operations_tmpl']
        command_name = '{} {}'.format(self.group_name, name) if self.group_name else name

        def get_op_handler():
            return self.command_loader.get_op_handler(operations_tmpl.format(method_name))

        def keyvault_arguments_loader():
            op = get_op_handler()
            self.command_loader._apply_doc_string(op, merged_kwargs)  # pylint: disable=protected-access
            cmd_args = list(
                extract_args_from_signature(op, excluded_params=self.command_loader.excluded_command_handler_args))
            return cmd_args

        def keyvault_description_loader():
            op = get_op_handler()
            self.command_loader._apply_doc_string(op, merged_kwargs)  # pylint: disable=protected-access
            return extract_full_summary_from_signature(op)

        def keyvault_command_handler(command_args):
            from azure.cli.core.util import get_arg_list
            from azure.cli.core.commands.client_factory import resolve_client_arg_name
            from msrest.paging import Paged
            from azure.cli.core.util import poller_classes

            op = get_op_handler()
            op_args = get_arg_list(op)
            command_type = merged_kwargs.get('command_type', None)
            client_factory = command_type.settings.get('client_factory', None) if command_type \
                else merged_kwargs.get('client_factory', None)

            client_arg_name = resolve_client_arg_name(operations_tmpl.format(method_name), kwargs)
            if client_arg_name in op_args:
                client = client_factory(self.command_loader.cli_ctx, command_args)
                command_args[client_arg_name] = client
            try:
                result = op(**command_args)
                # apply results transform if specified
                transform_result = merged_kwargs.get('transform', None)
                if transform_result:
                    return _encode_hex(transform_result(result))

                # otherwise handle based on return type of results
                if isinstance(result, poller_classes()):
                    return _encode_hex(
                        LongRunningOperation(self.command_loader.cli_ctx, 'Starting {}'.format(name))(result))
                elif isinstance(result, Paged):
                    try:
                        return _encode_hex(list(result))
                    except TypeError:
                        # TODO: Workaround for an issue in either KeyVault server-side or msrest
                        # See https://github.com/Azure/autorest/issues/1309
                        return []
                else:
                    return _encode_hex(result)
            except Exception as ex:  # pylint: disable=broad-except
                return keyvault_exception_handler(ex)

        self.command_loader._cli_command(command_name, handler=keyvault_command_handler,  # pylint: disable=protected-access
                                         argument_loader=keyvault_arguments_loader,
                                         description_loader=keyvault_description_loader,
                                         **merged_kwargs)

    def keyvault_command(self, name, method_name=None, command_type=None, **kwargs):
        """ Registers an Azure CLI KeyVault Data Plane command. These commands must respond to a
        challenge from the service when they make requests. """
        command_type_name = 'command_type'
        if command_type:
            kwargs[command_type_name] = command_type
        self._create_keyvault_command(name, method_name, command_type_name, **kwargs)

    def keyvault_custom(self, name, method_name=None, command_type=None, **kwargs):
        command_type_name = 'custom_command_type'
        if command_type:
            kwargs[command_type_name] = command_type
        self._create_keyvault_command(name, method_name, command_type_name, **kwargs)


class KeyVaultArgumentContext(AzArgumentContext):

    def attributes_argument(self, name, attr_class, create=False, ignore=None):
        from azure.cli.command_modules.keyvault._validators import get_attribute_validator, datetime_type
        from azure.cli.core.commands.parameters import get_three_state_flag

        from knack.arguments import ignore_type

        ignore = ignore or []
        self.argument('{}_attributes'.format(name), ignore_type,
                      validator=get_attribute_validator(name, attr_class, create))
        if create:
            self.extra('disabled', help='Create {} in disabled state.'.format(name), arg_type=get_three_state_flag())
        else:
            self.extra('enabled', help='Enable the {}.'.format(name), arg_type=get_three_state_flag())
        if 'expires' not in ignore:
            self.extra('expires', default=None, help='Expiration UTC datetime  (Y-m-d\'T\'H:M:S\'Z\').',
                       type=datetime_type)
        if 'not_before' not in ignore:
            self.extra('not_before', default=None, type=datetime_type,
                       help='Key not usable before the provided UTC datetime  (Y-m-d\'T\'H:M:S\'Z\').')
