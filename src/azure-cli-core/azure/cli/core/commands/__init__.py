# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function

import json
import pkgutil
import re
import sys
import time
import timeit
import traceback
from collections import OrderedDict, defaultdict
from importlib import import_module
from six import string_types, reraise

import azure.cli.core.azlogging as azlogging
import azure.cli.core.telemetry as telemetry
from azure.cli.core.util import CLIError
from azure.cli.core.application import APPLICATION
from azure.cli.core.prompting import prompt_y_n, NoTTYException
from azure.cli.core._config import az_config, DEFAULTS_SECTION
from azure.cli.core.profiles import ResourceType
from azure.cli.core.profiles._shared import get_versioned_sdk_path

from ._introspection import (extract_args_from_signature,
                             extract_full_summary_from_signature)

logger = azlogging.get_az_logger(__name__)


# pylint: disable=too-many-arguments,too-few-public-methods

CONFIRM_PARAM_NAME = 'yes'

BLACKLISTED_MODS = ['context']


class CliArgumentType(object):
    REMOVE = '---REMOVE---'

    def __init__(self, overrides=None, **kwargs):
        if isinstance(overrides, str):
            raise ValueError("Overrides has to be a CliArgumentType (cannot be a string)")
        options_list = kwargs.get('options_list', None)
        if options_list and isinstance(options_list, str):
            kwargs['options_list'] = [options_list]
        self.settings = {}
        self.update(overrides, **kwargs)

    def update(self, other=None, **kwargs):
        if other:
            self.settings.update(**other.settings)
        self.settings.update(**kwargs)


class CliCommandArgument(object):
    _NAMED_ARGUMENTS = ('options_list', 'validator', 'completer', 'id_part', 'arg_group')

    def __init__(self, dest=None, argtype=None, **kwargs):
        self.type = CliArgumentType(overrides=argtype, **kwargs)
        if dest:
            self.type.update(dest=dest)

        # We'll do an early fault detection to find any instances where we have inconsistent
        # set of parameters for argparse
        if not self.options_list and 'required' in self.options:  # pylint: disable=access-member-before-definition
            raise ValueError(message="You can't specify both required and an options_list")
        if not self.options.get('dest', False):
            raise ValueError('Missing dest')
        if not self.options_list:  # pylint: disable=access-member-before-definition
            self.options_list = ('--{}'.format(self.options['dest'].replace('_', '-')),)

    def __getattr__(self, name):
        if name in self._NAMED_ARGUMENTS:
            return self.type.settings.get(name, None)
        elif name == 'name':
            return self.type.settings.get('dest', None)
        elif name == 'options':
            return {key: value for key, value in self.type.settings.items()
                    if key != 'options' and key not in self._NAMED_ARGUMENTS and
                    not value == CliArgumentType.REMOVE}
        elif name == 'choices':
            return self.type.settings.get(name, None)
        else:
            raise AttributeError(message=name)

    def __setattr__(self, name, value):
        if name == 'type':
            return super(CliCommandArgument, self).__setattr__(name, value)
        self.type.settings[name] = value


class LongRunningOperation(object):  # pylint: disable=too-few-public-methods

    def __init__(self, start_msg='', finish_msg='', poller_done_interval_ms=1000.0):
        self.start_msg = start_msg
        self.finish_msg = finish_msg
        self.poller_done_interval_ms = poller_done_interval_ms

    def _delay(self):
        time.sleep(self.poller_done_interval_ms / 1000.0)

    def __call__(self, poller):
        from msrest.exceptions import ClientException
        logger.info("Starting long running operation '%s'", self.start_msg)
        correlation_message = ''
        while not poller.done():
            try:
                # pylint: disable=protected-access
                correlation_id = json.loads(
                    poller._response.__dict__['_content'])['properties']['correlationId']

                correlation_message = 'Correlation ID: {}'.format(correlation_id)
            except:  # pylint: disable=bare-except
                pass

            try:
                self._delay()
            except KeyboardInterrupt:
                logger.error('Long running operation wait cancelled.  %s', correlation_message)
                raise
        try:
            result = poller.result()
        except ClientException as client_exception:
            telemetry.set_exception(
                client_exception,
                fault_type='failed-long-running-operation',
                summary='Unexpected client exception in {}.'.format(LongRunningOperation.__name__))
            message = getattr(client_exception, 'message', client_exception)

            try:
                message = '{} {}'.format(
                    str(message),
                    json.loads(client_exception.response.text)['error']['details'][0]['message'])
            except:  # pylint: disable=bare-except
                pass

            cli_error = CLIError('{}  {}'.format(message, correlation_message))
            # capture response for downstream commands (webapp) to dig out more details
            setattr(cli_error, 'response', getattr(client_exception, 'response', None))
            raise cli_error

        logger.info("Long running operation '%s' completed with result %s",
                    self.start_msg, result)
        return result


# pylint: disable=too-few-public-methods
class DeploymentOutputLongRunningOperation(LongRunningOperation):
    def __call__(self, result):
        from msrest.pipeline import ClientRawResponse
        from msrestazure.azure_operation import AzureOperationPoller

        if isinstance(result, AzureOperationPoller):
            # most deployment operations return a poller
            result = super(DeploymentOutputLongRunningOperation, self).__call__(result)
            outputs = result.properties.outputs
            return {key: val['value'] for key, val in outputs.items()} if outputs else {}
        elif isinstance(result, ClientRawResponse):
            # --no-wait returns a ClientRawResponse
            return None
        else:
            # --validate returns a 'normal' response
            return result


class CommandTable(dict):
    """A command table is a dictionary of name -> CliCommand
    instances.

    The `name` is the space separated name - i.e. 'vm list'
    """

    def register(self, name):
        def wrapped(func):
            cli_command(self, name, func)
            return func

        return wrapped


class CliCommand(object):  # pylint:disable=too-many-instance-attributes

    def __init__(self, name, handler, description=None, table_transformer=None,
                 arguments_loader=None, description_loader=None,
                 formatter_class=None):
        self.name = name
        self.handler = handler
        self.help = None
        self.description = description_loader \
            if description_loader and CliCommand._should_load_description() \
            else description
        self.arguments = {}
        self.arguments_loader = arguments_loader
        self.table_transformer = table_transformer
        self.formatter_class = formatter_class

    @staticmethod
    def _should_load_description():
        return not APPLICATION.session['completer_active']

    def load_arguments(self):
        if self.arguments_loader:
            self.arguments.update(self.arguments_loader())

    def add_argument(self, param_name, *option_strings, **kwargs):
        dest = kwargs.pop('dest', None)
        argument = CliCommandArgument(
            dest or param_name, options_list=option_strings, **kwargs)
        self.arguments[param_name] = argument

    def update_argument(self, param_name, argtype):
        arg = self.arguments[param_name]
        self._resolve_default_value_from_cfg_file(arg, argtype)
        arg.type.update(other=argtype)

    def _resolve_default_value_from_cfg_file(self, arg, overrides):
        if 'configured_default' in overrides.settings:
            def_config = overrides.settings.pop('configured_default', None)
            # same blunt mechanism like we handled id-parts, for create command, no name default
            if (self.name.split()[-1] == 'create' and
                    overrides.settings.get('metavar', None) == 'NAME'):
                return
            setattr(arg.type, 'configured_default_applied', True)
            config_value = az_config.get(DEFAULTS_SECTION, def_config, None)
            if config_value:
                overrides.settings['default'] = config_value
                overrides.settings['required'] = False

    def execute(self, **kwargs):
        return self.handler(**kwargs)


command_table = CommandTable()

# Map to determine what module a command was registered in
command_module_map = {}


def load_params(command):
    try:
        command_table[command].load_arguments()
    except KeyError:
        return
    command_module = command_module_map.get(command, None)
    if not command_module:
        logger.debug("Unable to load commands for '%s'. No module in command module map found.",
                     command)  # pylint: disable=line-too-long
        return
    module_to_load = command_module[:command_module.rfind('.')]
    import_module(module_to_load).load_params(command)
    _apply_parameter_info(command, command_table[command])


def get_command_table(module_name=None):
    '''Loads command table(s)
    When `module_name` is specified, only commands from that module will be loaded.
    If the module is not found, all commands are loaded.
    '''
    loaded = False
    if module_name and module_name not in BLACKLISTED_MODS:
        try:
            import_module('azure.cli.command_modules.' + module_name).load_commands()
            logger.debug("Successfully loaded command table from module '%s'.", module_name)
            loaded = True
        except ImportError:
            logger.debug("Loading all installed modules as module with name '%s' not found.", module_name)  # pylint: disable=line-too-long
        except Exception:  # pylint: disable=broad-except
            pass
    if not loaded:
        installed_command_modules = []
        try:
            mods_ns_pkg = import_module('azure.cli.command_modules')
            installed_command_modules = [modname for _, modname, _ in
                                         pkgutil.iter_modules(mods_ns_pkg.__path__)
                                         if modname not in BLACKLISTED_MODS]
        except ImportError:
            pass
        logger.debug('Installed command modules %s', installed_command_modules)
        cumulative_elapsed_time = 0
        for mod in installed_command_modules:
            try:
                start_time = timeit.default_timer()
                import_module('azure.cli.command_modules.' + mod).load_commands()
                elapsed_time = timeit.default_timer() - start_time
                logger.debug("Loaded module '%s' in %.3f seconds.", mod, elapsed_time)
                cumulative_elapsed_time += elapsed_time
            except Exception as ex:  # pylint: disable=broad-except
                # Changing this error message requires updating CI script that checks for failed
                # module loading.
                logger.error("Error loading command module '%s'", mod)
                telemetry.set_exception(exception=ex, fault_type='module-load-error-' + mod,
                                        summary='Error loading module: {}'.format(mod))
                logger.debug(traceback.format_exc())
        logger.debug("Loaded all modules in %.3f seconds. "
                     "(note: there's always an overhead with the first module loaded)",
                     cumulative_elapsed_time)
    _update_command_definitions(command_table)
    ordered_commands = OrderedDict(command_table)
    return ordered_commands


def register_cli_argument(scope, dest, arg_type=None, **kwargs):
    '''Specify CLI specific metadata for a given argument for a given scope.
    '''
    _cli_argument_registry.register_cli_argument(scope, dest, arg_type, **kwargs)


def register_extra_cli_argument(command, dest, **kwargs):
    '''Register extra parameters for the given command. Typically used to augment auto-command built
    commands to add more parameters than the specific SDK method introspected.
    '''
    _cli_extra_argument_registry[command][dest] = CliCommandArgument(dest, **kwargs)


def cli_command(module_name, name, operation,
                client_factory=None, transform=None, table_transformer=None,
                no_wait_param=None, confirmation=None, exception_handler=None,
                formatter_class=None):
    """ Registers a default Azure CLI command. These commands require no special parameters. """
    command_table[name] = create_command(module_name, name, operation, transform, table_transformer,
                                         client_factory, no_wait_param, confirmation=confirmation,
                                         exception_handler=exception_handler,
                                         formatter_class=formatter_class)


def get_op_handler(operation):
    """ Import and load the operation handler """
    # Patch the unversioned sdk path to include the appropriate API version for the
    # resource type in question.
    from azure.cli.core._profile import CLOUD
    for rt in ResourceType:
        if operation.startswith(rt.import_prefix):
            operation = operation.replace(rt.import_prefix,
                                          get_versioned_sdk_path(CLOUD.profile, rt))
    try:
        mod_to_import, attr_path = operation.split('#')
        op = import_module(mod_to_import)
        for part in attr_path.split('.'):
            op = getattr(op, part)
        return op
    except (ValueError, AttributeError):
        raise ValueError("The operation '{}' is invalid.".format(operation))


def _load_client_exception_class():
    # Since loading msrest is expensive, we avoid it until we have to
    from msrest.exceptions import ClientException
    return ClientException


def _load_azure_exception_class():
    # Since loading msrest is expensive, we avoid it until we have to
    from azure.common import AzureException
    return AzureException


def _is_paged(obj):
    # Since loading msrest is expensive, we avoid it until we have to
    import collections
    if isinstance(obj, collections.Iterable) \
            and not isinstance(obj, list) \
            and not isinstance(obj, dict):
        from msrest.paging import Paged
        return isinstance(obj, Paged)
    return False


def _is_poller(obj):
    # Since loading msrest is expensive, we avoid it until we have to
    if obj.__class__.__name__ == 'AzureOperationPoller':
        from msrestazure.azure_operation import AzureOperationPoller
        return isinstance(obj, AzureOperationPoller)
    return False


def create_command(module_name, name, operation,
                   transform_result, table_transformer, client_factory,
                   no_wait_param=None, confirmation=None, exception_handler=None,
                   formatter_class=None):
    if not isinstance(operation, string_types):
        raise ValueError("Operation must be a string. Got '{}'".format(operation))

    def _execute_command(kwargs):

        if confirmation \
            and not kwargs.get(CONFIRM_PARAM_NAME) \
            and not az_config.getboolean('core', 'disable_confirm_prompt', fallback=False) \
                and not _user_confirmed(confirmation, kwargs):
            raise CLIError('Operation cancelled.')

        client = client_factory(kwargs) if client_factory else None
        try:
            op = get_op_handler(operation)
            try:
                result = op(client, **kwargs) if client else op(**kwargs)
                if no_wait_param and kwargs.get(no_wait_param, None):
                    return None  # return None for 'no-wait'

                # apply results transform if specified
                if transform_result:
                    return transform_result(result)

                # otherwise handle based on return type of results
                if _is_poller(result):
                    return LongRunningOperation('Starting {}'.format(name))(result)
                elif _is_paged(result):
                    return list(result)
                return result
            except Exception as ex:  # pylint: disable=broad-except
                if exception_handler:
                    exception_handler(ex)
                else:
                    reraise(*sys.exc_info())
        except _load_client_exception_class() as client_exception:
            fault_type = name.replace(' ', '-') + '-client-error'
            telemetry.set_exception(client_exception, fault_type=fault_type,
                                    summary='Unexpected client exception during command creation')
            message = getattr(client_exception, 'message', client_exception)
            raise _polish_rp_not_registerd_error(CLIError(message))
        except _load_azure_exception_class() as azure_exception:
            fault_type = name.replace(' ', '-') + '-service-error'
            telemetry.set_exception(azure_exception, fault_type=fault_type,
                                    summary='Unexpected azure exception during command creation')
            message = re.search(r"([A-Za-z\t .])+", str(azure_exception))
            raise CLIError('\n{}'.format(message.group(0) if message else str(azure_exception)))
        except ValueError as value_error:
            fault_type = name.replace(' ', '-') + '-value-error'
            telemetry.set_exception(value_error, fault_type=fault_type,
                                    summary='Unexpected value exception during command creation')
            raise CLIError(value_error)
        except CLIError as cli_error:
            raise _polish_rp_not_registerd_error(cli_error)

    command_module_map[name] = module_name
    name = ' '.join(name.split())

    def arguments_loader():
        return extract_args_from_signature(get_op_handler(operation), no_wait_param=no_wait_param)

    def description_loader():
        return extract_full_summary_from_signature(get_op_handler(operation))

    cmd = CliCommand(name, _execute_command, table_transformer=table_transformer,
                     arguments_loader=arguments_loader, description_loader=description_loader,
                     formatter_class=formatter_class)
    if confirmation:
        cmd.add_argument(CONFIRM_PARAM_NAME, '--yes', '-y',
                         action='store_true',
                         help='Do not prompt for confirmation')
    return cmd


def _user_confirmed(confirmation, command_args):
    if callable(confirmation):
        return confirmation(command_args)
    try:
        if isinstance(confirmation, string_types):
            return prompt_y_n(confirmation)
        return prompt_y_n('Are you sure you want to perform this operation?')
    except NoTTYException:
        logger.warning('Unable to prompt for confirmation as no tty available. Use --yes.')
        return False


def _polish_rp_not_registerd_error(cli_error):
    msg = str(cli_error)
    pertinent_text_namespace = 'The subscription must be registered to use namespace'
    pertinent_text_feature = 'is not registered for feature'
    # pylint: disable=line-too-long
    if pertinent_text_namespace in msg:
        reg = r".*{} '(.*)'".format(pertinent_text_namespace)
        match = re.match(reg, msg)
        cli_error = CLIError(
            "Run 'az provider register -n {}' to register the namespace first".format(
                match.group(1)))
    elif pertinent_text_feature in msg:
        reg = r".*{}\s+([^\s]+)\s+".format(pertinent_text_feature)
        match = re.match(reg, msg)
        parts = match.group(1).split('/')
        if len(parts) == 2:
            cli_error = CLIError(
                "Run 'az feature register --namespace {} -n {}' to enable the feature first".format(
                    parts[0], parts[1]))
    return cli_error


def _get_cli_argument(command, argname):
    return _cli_argument_registry.get_cli_argument(command, argname)


def _get_cli_extra_arguments(command):
    return _cli_extra_argument_registry[command].items()


class _ArgumentRegistry(object):
    def __init__(self):
        self.arguments = defaultdict(lambda: {})

    def register_cli_argument(self, scope, dest, argtype, **kwargs):
        argument = CliArgumentType(overrides=argtype,
                                   **kwargs)
        self.arguments[scope][dest] = argument

    def get_cli_argument(self, command, name):
        parts = command.split()
        result = CliArgumentType()
        for index in range(0, len(parts) + 1):
            probe = ' '.join(parts[0:index])
            override = self.arguments.get(probe, {}).get(name, None)
            if override:
                result.update(override)
        return result


_cli_argument_registry = _ArgumentRegistry()
_cli_extra_argument_registry = defaultdict(lambda: {})


def _apply_parameter_info(command_name, command):
    for argument_name in command.arguments:
        overrides = _get_cli_argument(command_name, argument_name)
        command.update_argument(argument_name, overrides)

    # Add any arguments explicitly registered for this command
    for argument_name, argument_definition in _get_cli_extra_arguments(command_name):
        command.arguments[argument_name] = argument_definition
        command.update_argument(argument_name, _get_cli_argument(command_name, argument_name))


def _update_command_definitions(command_table_to_update):
    for command_name, command in command_table_to_update.items():
        _apply_parameter_info(command_name, command)
