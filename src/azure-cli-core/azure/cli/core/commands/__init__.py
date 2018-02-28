# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function

import datetime
import json
import logging as logs
import sys
import time
from importlib import import_module
import six

from knack.arguments import CLICommandArgument, ignore_type, ArgumentsContext
from knack.commands import CLICommand, CommandGroup
from knack.invocation import CommandInvoker
from knack.log import get_logger
from knack.parser import ARGPARSE_SUPPORTED_KWARGS
from knack.util import CLIError

from azure.cli.core import EXCLUDED_PARAMS
from azure.cli.core.extension import get_extension
import azure.cli.core.telemetry as telemetry

logger = get_logger(__name__)

CLI_COMMON_KWARGS = ['min_api', 'max_api', 'resource_type', 'operation_group',
                     'custom_command_type', 'command_type']

CLI_COMMAND_KWARGS = ['transform', 'table_transformer', 'confirmation', 'exception_handler',
                      'client_factory', 'operations_tmpl', 'no_wait_param', 'supports_no_wait', 'validator',
                      'client_arg_name', 'doc_string_source', 'deprecate_info'] + CLI_COMMON_KWARGS
CLI_PARAM_KWARGS = \
    ['id_part', 'completer', 'validator', 'options_list', 'configured_default', 'arg_group', 'arg_type'] \
    + CLI_COMMON_KWARGS + ARGPARSE_SUPPORTED_KWARGS

CONFIRM_PARAM_NAME = 'yes'

# 1 hour in milliseconds
DEFAULT_QUERY_TIME_RANGE = 3600000

BLACKLISTED_MODS = ['context', 'shell', 'documentdb', 'component']


def _explode_list_args(args):
    '''Iterate through each attribute member of args and create a copy with
    the IterateValues 'flattened' to only contain a single value

    Ex.
        { a1:'x', a2:IterateValue(['y', 'z']) } => [{ a1:'x', a2:'y'),{ a1:'x', a2:'z'}]
    '''
    from azure.cli.core.commands.validators import IterateValue
    import argparse
    list_args = {argname: argvalue for argname, argvalue in vars(args).items()
                 if isinstance(argvalue, IterateValue)}
    if not list_args:
        yield args
    else:
        values = list(zip(*list_args.values()))
        for key in list_args:
            delattr(args, key)

        for value in values:
            new_ns = argparse.Namespace(**vars(args))
            for key_index, key in enumerate(list_args.keys()):
                setattr(new_ns, key, value[key_index])
            yield new_ns


def _expand_file_prefixed_files(args):
    def _load_file(path):
        from azure.cli.core.util import read_file_content
        if path == '-':
            content = sys.stdin.read()
        else:
            import os
            content = read_file_content(os.path.expanduser(path), allow_binary=True)

        return content[0:-1] if content and content[-1] == '\n' else content

    def _maybe_load_file(arg):
        ix = arg.find('@')
        if ix == -1:  # no @ found
            return arg

        poss_file = arg[ix + 1:]
        if not poss_file:  # if nothing after @ then it can't be a file
            return arg
        elif ix == 0:
            return _load_file(poss_file)

        # if @ not at the start it can't be a file
        return arg

    def _expand_file_prefix(arg):
        arg_split = arg.split('=', 1)
        try:
            return '='.join([arg_split[0], _maybe_load_file(arg_split[1])])
        except IndexError:
            return _maybe_load_file(arg_split[0])

    return list([_expand_file_prefix(arg) for arg in args])


def _pre_command_table_create(cli_ctx, args):
    cli_ctx.refresh_request_id()
    return _expand_file_prefixed_files(args)


class AzCliCommand(CLICommand):

    def __init__(self, loader, name, handler, description=None, table_transformer=None,
                 arguments_loader=None, description_loader=None,
                 formatter_class=None, deprecate_info=None, validator=None, **kwargs):
        super(AzCliCommand, self).__init__(loader.cli_ctx, name, handler, description=description,
                                           table_transformer=table_transformer, arguments_loader=arguments_loader,
                                           description_loader=description_loader, formatter_class=formatter_class,
                                           deprecate_info=deprecate_info, validator=validator, **kwargs)
        self.loader = loader
        self.command_source = None
        self.no_wait_param = kwargs.get('no_wait_param', None)
        self.supports_no_wait = kwargs.get('supports_no_wait', False)
        self.exception_handler = kwargs.get('exception_handler', None)
        self.confirmation = kwargs.get('confirmation', False)
        self.command_kwargs = kwargs

    def _resolve_default_value_from_cfg_file(self, arg, overrides):
        from azure.cli.core._config import DEFAULTS_SECTION

        if not hasattr(arg.type, 'required_tooling'):
            required = arg.type.settings.get('required', False)
            setattr(arg.type, 'required_tooling', required)
        if 'configured_default' in overrides.settings:
            def_config = overrides.settings.pop('configured_default', None)
            setattr(arg.type, 'default_name_tooling', def_config)
            # same blunt mechanism like we handled id-parts, for create command, no name default
            if self.name.split()[-1] == 'create' and overrides.settings.get('metavar', None) == 'NAME':
                return
            setattr(arg.type, 'configured_default_applied', True)
            config_value = self.cli_ctx.config.get(DEFAULTS_SECTION, def_config, None)
            if config_value:
                logger.info("Configured default '%s' for arg %s", config_value, arg.name)
                overrides.settings['default'] = config_value
                overrides.settings['required'] = False

    def load_arguments(self):
        super(AzCliCommand, self).load_arguments()
        if self.arguments_loader:
            cmd_args = self.arguments_loader()
            if self.supports_no_wait or self.no_wait_param:
                if self.supports_no_wait:
                    no_wait_param_dest = 'no_wait'
                elif self.no_wait_param:
                    no_wait_param_dest = self.no_wait_param
                cmd_args.append(
                    (no_wait_param_dest,
                     CLICommandArgument(no_wait_param_dest, options_list=['--no-wait'], action='store_true',
                                        help='Do not wait for the long-running operation to finish.')))
            self.arguments.update(cmd_args)

    def update_argument(self, param_name, argtype):
        from azure.cli.core.commands.validators import DefaultStr, DefaultInt
        arg = self.arguments[param_name]
        self._resolve_default_value_from_cfg_file(arg, argtype)
        arg.type.update(other=argtype)
        arg_default = arg.type.settings.get('default', None)
        if isinstance(arg_default, str):
            arg_default = DefaultStr(arg_default)
        elif isinstance(arg_default, int):
            arg_default = DefaultInt(arg_default)
        if arg_default:
            arg.type.settings['default'] = arg_default

    def __call__(self, *args, **kwargs):
        if self.command_source and isinstance(self.command_source, ExtensionCommandSource) and \
                self.command_source.overrides_command:
            logger.warning(self.command_source.get_command_warn_msg())
        return super(AzCliCommand, self).__call__(*args, **kwargs)

    def _merge_kwargs(self, kwargs, base_kwargs=None):
        base = base_kwargs if base_kwargs is not None else getattr(self, 'command_kwargs')
        return _merge_kwargs(kwargs, base)

    def get_api_version(self, resource_type=None, operation_group=None):
        resource_type = resource_type or self.command_kwargs.get('resource_type', None)
        return self.loader.get_api_version(resource_type=resource_type, operation_group=operation_group)

    def supported_api_version(self, resource_type=None, min_api=None, max_api=None, operation_group=None):
        resource_type = resource_type or self.command_kwargs.get('resource_type', None)
        return self.loader.supported_api_version(resource_type=resource_type, min_api=min_api, max_api=max_api,
                                                 operation_group=operation_group)

    def get_models(self, *attr_args, **kwargs):
        resource_type = kwargs.get('resource_type', self.command_kwargs.get('resource_type', None))
        operation_group = kwargs.get('operation_group', self.command_kwargs.get('operation_group', None))
        return self.loader.get_sdk(*attr_args, resource_type=resource_type, mod='models',
                                   operation_group=operation_group)


# pylint: disable=too-few-public-methods
class AzCliCommandInvoker(CommandInvoker):

    # pylint: disable=too-many-statements,too-many-locals,too-many-branches
    def execute(self, args):
        from knack.events import (EVENT_INVOKER_PRE_CMD_TBL_CREATE, EVENT_INVOKER_POST_CMD_TBL_CREATE,
                                  EVENT_INVOKER_CMD_TBL_LOADED, EVENT_INVOKER_PRE_PARSE_ARGS,
                                  EVENT_INVOKER_POST_PARSE_ARGS, EVENT_INVOKER_TRANSFORM_RESULT,
                                  EVENT_INVOKER_FILTER_RESULT)
        from knack.util import CommandResultItem, todict
        from azure.cli.core.commands.events import EVENT_INVOKER_PRE_CMD_TBL_TRUNCATE

        # TODO: Can't simply be invoked as an event because args are transformed
        args = _pre_command_table_create(self.cli_ctx, args)

        self.cli_ctx.raise_event(EVENT_INVOKER_PRE_CMD_TBL_CREATE, args=args)
        self.commands_loader.load_command_table(args)
        self.cli_ctx.raise_event(EVENT_INVOKER_PRE_CMD_TBL_TRUNCATE,
                                 load_cmd_tbl_func=self.commands_loader.load_command_table, args=args)
        command = self._rudimentary_get_command(args)
        telemetry.set_raw_command_name(command)

        try:
            self.commands_loader.command_table = {command: self.commands_loader.command_table[command]}
        except KeyError:
            # Trim down the command table to reduce the number of subparsers required to optimize the performance.
            #
            # When given a command table like this:
            #
            # network application-gateway create
            # network application-gateway delete
            # network list-usages
            # storage account create
            # storage account list
            #
            # input:  az
            # output: network application-gateway create
            #         storage account create
            #
            # input:  az network
            # output: network application-gateway create
            #         network list-usages

            cmd_table = {}
            group_names = set()
            for cmd_name, cmd in self.commands_loader.command_table.items():
                if command and not cmd_name.startswith(command):
                    continue

                cmd_stub = cmd_name[len(command):].strip()
                group_name = cmd_stub.split(' ', 1)[0]
                if group_name not in group_names:
                    cmd_table[cmd_name] = cmd
                    group_names.add(group_name)
                self.commands_loader.command_table = cmd_table

        self.commands_loader.command_table = self.commands_loader.command_table  # update with the truncated table
        self.commands_loader.command_name = command
        self.commands_loader.load_arguments(command)
        self.cli_ctx.raise_event(EVENT_INVOKER_POST_CMD_TBL_CREATE, cmd_tbl=self.commands_loader.command_table)
        self.parser.cli_ctx = self.cli_ctx
        self.parser.load_command_table(self.commands_loader.command_table)

        self.cli_ctx.raise_event(EVENT_INVOKER_CMD_TBL_LOADED, cmd_tbl=self.commands_loader.command_table,
                                 parser=self.parser)

        if not args:
            self.cli_ctx.completion.enable_autocomplete(self.parser)
            subparser = self.parser.subparsers[tuple()]
            self.help.show_welcome(subparser)

            # TODO: No event in base with which to target
            telemetry.set_command_details('az')
            telemetry.set_success(summary='welcome')
            return None

        if args[0].lower() == 'help':
            args[0] = '--help'

        self.cli_ctx.completion.enable_autocomplete(self.parser)

        self.cli_ctx.raise_event(EVENT_INVOKER_PRE_PARSE_ARGS, args=args)
        parsed_args = self.parser.parse_args(args)
        self.cli_ctx.raise_event(EVENT_INVOKER_POST_PARSE_ARGS, command=parsed_args.command, args=parsed_args)

        # TODO: This fundamentally alters the way Knack.invocation works here. Cannot be customized
        # with an event. Would need to be customized via inheritance.
        results = []
        for expanded_arg in _explode_list_args(parsed_args):
            cmd = expanded_arg.func
            if hasattr(expanded_arg, 'cmd'):
                expanded_arg.cmd = cmd

            self.cli_ctx.data['command'] = expanded_arg.command

            self._validation(expanded_arg)

            params = self._filter_params(expanded_arg)

            command_source = self.commands_loader.command_table[command].command_source

            extension_version = None
            try:
                if command_source:
                    extension_version = get_extension(command_source.extension_name).version
            except Exception:  # pylint: disable=broad-except
                pass

            telemetry.set_command_details(self.cli_ctx.data['command'], self.data['output'],
                                          [(p.split('=', 1)[0] if p.startswith('--') else p[:2]) for p in args if
                                           (p.startswith('-') and len(p) > 1)],
                                          extension_name=command_source.extension_name if command_source else None,
                                          extension_version=extension_version)
            if command_source:
                self.data['command_extension_name'] = command_source.extension_name

            try:
                result = cmd(params)
                if cmd.supports_no_wait and getattr(expanded_arg, 'no_wait', False):
                    result = None
                elif cmd.no_wait_param and getattr(expanded_arg, cmd.no_wait_param, False):
                    result = None

                # TODO: Not sure how to make this actually work with the TRANSFORM event...
                transform_op = cmd.command_kwargs.get('transform', None)
                if transform_op:
                    result = transform_op(result)

                if _is_poller(result):
                    result = LongRunningOperation(self.cli_ctx, 'Starting {}'.format(cmd.name))(result)
                elif _is_paged(result):
                    result = list(result)

                result = todict(result)
                event_data = {'result': result}
                self.cli_ctx.raise_event(EVENT_INVOKER_TRANSFORM_RESULT, event_data=event_data)
                self.cli_ctx.raise_event(EVENT_INVOKER_FILTER_RESULT, event_data=event_data)
                result = event_data['result']
                results.append(result)

            except Exception as ex:  # pylint: disable=broad-except
                if cmd.exception_handler:
                    cmd.exception_handler(ex)
                    return None
                else:
                    six.reraise(*sys.exc_info())

        if results and len(results) == 1:
            results = results[0]

        return CommandResultItem(
            results,
            table_transformer=self.commands_loader.command_table[parsed_args.command].table_transformer,
            is_query_active=self.data['query_active'])

    def _build_kwargs(self, func, ns):  # pylint: disable=no-self-use
        from azure.cli.core.util import get_arg_list
        arg_list = get_arg_list(func)
        kwargs = {}
        if 'cmd' in arg_list:
            kwargs['cmd'] = ns._cmd  # pylint: disable=protected-access
        if 'namespace' in arg_list:
            kwargs['namespace'] = ns
        if 'ns' in arg_list:
            kwargs['ns'] = ns
        return kwargs

    def _validate_cmd_level(self, ns, cmd_validator):  # pylint: disable=no-self-use
        if cmd_validator:
            cmd_validator(**self._build_kwargs(cmd_validator, ns))
        try:
            delattr(ns, '_command_validator')
        except AttributeError:
            pass

    def _validate_arg_level(self, ns, **_):  # pylint: disable=no-self-use
        from msrest.exceptions import ValidationError
        for validator in getattr(ns, '_argument_validators', []):
            try:
                validator(**self._build_kwargs(validator, ns))
            except ValidationError:
                logger.debug('Validation error in %s.', str(validator))
                raise
        try:
            delattr(ns, '_argument_validators')
        except AttributeError:
            pass


class LongRunningOperation(object):  # pylint: disable=too-few-public-methods
    def __init__(self, cli_ctx, start_msg='', finish_msg='', poller_done_interval_ms=1000.0):

        self.cli_ctx = cli_ctx
        self.start_msg = start_msg
        self.finish_msg = finish_msg
        self.poller_done_interval_ms = poller_done_interval_ms
        self.deploy_dict = {}
        self.last_progress_report = datetime.datetime.now()

    def _delay(self):
        time.sleep(self.poller_done_interval_ms / 1000.0)

    def _generate_template_progress(self, correlation_id):  # pylint: disable=no-self-use
        """ gets the progress for template deployments """
        from azure.cli.core.commands.client_factory import get_mgmt_service_client
        from azure.mgmt.monitor import MonitorManagementClient

        if correlation_id is not None:  # pylint: disable=too-many-nested-blocks
            formatter = "eventTimestamp ge {}"

            end_time = datetime.datetime.utcnow()
            start_time = end_time - datetime.timedelta(seconds=DEFAULT_QUERY_TIME_RANGE)
            odata_filters = formatter.format(start_time.strftime('%Y-%m-%dT%H:%M:%SZ'))

            odata_filters = "{} and {} eq '{}'".format(odata_filters, 'correlationId', correlation_id)

            activity_log = get_mgmt_service_client(
                self.cli_ctx, MonitorManagementClient).activity_logs.list(filter=odata_filters)

            results = []
            max_events = 50  # default max value for events in list_activity_log
            for index, item in enumerate(activity_log):
                if index < max_events:
                    results.append(item)
                else:
                    break

            if results:
                for event in results:
                    update = False
                    long_name = event.resource_id.split('/')[-1]
                    if long_name not in self.deploy_dict:
                        self.deploy_dict[long_name] = {}
                        update = True
                    deploy_values = self.deploy_dict[long_name]

                    checked_values = {
                        str(event.resource_type.value): 'type',
                        str(event.status.value): 'status value',
                        str(event.event_name.value): 'request',
                    }
                    try:
                        checked_values[str(event.properties.get('statusCode', ''))] = 'status'
                    except AttributeError:
                        pass

                    if deploy_values.get('timestamp', None) is None or \
                            event.event_timestamp > deploy_values.get('timestamp'):
                        for value in checked_values:
                            if deploy_values.get(checked_values[value], None) != value:
                                update = True
                            deploy_values[checked_values[value]] = value
                        deploy_values['timestamp'] = event.event_timestamp

                        # don't want to show the timestamp
                        json_val = deploy_values.copy()
                        json_val.pop('timestamp', None)
                        status_val = deploy_values.get('status value', None)
                        if status_val and status_val != 'Started':
                            result = deploy_values['status value'] + ': ' + long_name
                            result += ' (' + deploy_values.get('type', '') + ')'

                            if update:
                                logger.info(result)

    def __call__(self, poller):
        import colorama
        from msrest.exceptions import ClientException

        # https://github.com/azure/azure-cli/issues/3555
        colorama.init()

        correlation_message = ''
        self.cli_ctx.get_progress_controller().begin()
        correlation_id = None

        cli_logger = get_logger()  # get CLI logger which has the level set through command lines
        is_verbose = any(handler.level <= logs.INFO for handler in cli_logger.handlers)

        while not poller.done():
            self.cli_ctx.get_progress_controller().add(message='Running')
            try:
                # pylint: disable=protected-access
                correlation_id = json.loads(
                    poller._response.__dict__['_content'].decode())['properties']['correlationId']

                correlation_message = 'Correlation ID: {}'.format(correlation_id)
            except:  # pylint: disable=bare-except
                pass

            current_time = datetime.datetime.now()
            if is_verbose and current_time - self.last_progress_report >= datetime.timedelta(seconds=10):
                self.last_progress_report = current_time
                try:
                    self._generate_template_progress(correlation_id)
                except Exception as ex:  # pylint: disable=broad-except
                    logger.warning('%s during progress reporting: %s', getattr(type(ex), '__name__', type(ex)), ex)
            try:
                self._delay()
            except KeyboardInterrupt:
                self.cli_ctx.get_progress_controller().stop()
                logger.error('Long-running operation wait cancelled.  %s', correlation_message)
                raise

        try:
            result = poller.result()
        except ClientException as client_exception:
            from azure.cli.core.commands.arm import handle_long_running_operation_exception
            self.cli_ctx.get_progress_controller().stop()
            handle_long_running_operation_exception(client_exception)

        self.cli_ctx.get_progress_controller().end()
        colorama.deinit()

        return result


# pylint: disable=too-few-public-methods
class DeploymentOutputLongRunningOperation(LongRunningOperation):
    def __call__(self, result):
        from msrest.pipeline import ClientRawResponse
        from azure.cli.core.util import poller_classes

        if isinstance(result, poller_classes()):
            # most deployment operations return a poller
            result = super(DeploymentOutputLongRunningOperation, self).__call__(result)
            outputs = result.properties.outputs
            return {key: val['value'] for key, val in outputs.items()} if outputs else {}
        elif isinstance(result, ClientRawResponse):
            # --no-wait returns a ClientRawResponse
            return None

        # --validate returns a 'normal' response
        return result


def _load_command_loader(loader, args, name, prefix):
    module = import_module(prefix + name)
    loader_cls = getattr(module, 'COMMAND_LOADER_CLS', None)
    command_table = {}

    if loader_cls:
        command_loader = loader_cls(cli_ctx=loader.cli_ctx)
        loader.loaders.append(command_loader)  # This will be used by interactive
        if command_loader.supported_api_version():
            command_table = command_loader.load_command_table(args)
            if command_table:
                for cmd in list(command_table.keys()):
                    # TODO: If desired to for extension to patch module, this can be uncommented
                    # if loader.cmd_to_loader_map.get(cmd):
                    #    loader.cmd_to_loader_map[cmd].append(command_loader)
                    # else:
                    loader.cmd_to_loader_map[cmd] = [command_loader]
    else:
        logger.debug("Module '%s' is missing `COMMAND_LOADER_CLS` entry.", name)
    return command_table


def _load_extension_command_loader(loader, args, ext):
    return _load_command_loader(loader, args, ext, '')


def _load_module_command_loader(loader, args, mod):
    return _load_command_loader(loader, args, mod, 'azure.cli.command_modules.')


class ExtensionCommandSource(object):
    """ Class for commands contributed by an extension """

    def __init__(self, overrides_command=False, extension_name=None):
        super(ExtensionCommandSource, self).__init__()
        # True if the command overrides a CLI command
        self.overrides_command = overrides_command
        self.extension_name = extension_name

    def get_command_warn_msg(self):
        if self.overrides_command:
            if self.extension_name:
                return "The behavior of this command has been altered by the following extension: " \
                       "{}".format(self.extension_name)
            return "The behavior of this command has been altered by an extension."
        else:
            if self.extension_name:
                return "This command is from the following extension: {}".format(self.extension_name)
            return "This command is from an extension."


def _load_client_exception_class():
    # Since loading msrest is expensive, we avoid it until we have to
    from msrest.exceptions import ClientException
    return ClientException


def _load_validation_error_class():
    # Since loading msrest is expensive, we avoid it until we have to
    from msrest.exceptions import ValidationError
    return ValidationError


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
    if obj.__class__.__name__ in ['AzureOperationPoller', 'LROPoller']:
        from azure.cli.core.util import poller_classes
        return isinstance(obj, poller_classes())
    return False


def _merge_kwargs(patch_kwargs, base_kwargs, supported_kwargs=None):
    merged_kwargs = base_kwargs.copy()
    merged_kwargs.update(patch_kwargs)
    unrecognized_kwargs = [x for x in merged_kwargs if x not in (supported_kwargs or CLI_COMMON_KWARGS)]
    if unrecognized_kwargs:
        raise TypeError('unrecognized kwargs: {}'.format(unrecognized_kwargs))
    return merged_kwargs


# pylint: disable=too-few-public-methods
class CliCommandType(object):

    def __init__(self, overrides=None, **kwargs):
        if isinstance(overrides, str):
            raise ValueError("Overrides has to be a {} (cannot be a string)".format(CliCommandType.__name__))
        self.settings = {}
        self.update(overrides, **kwargs)

    def __repr__(self):
        return str(vars(self))

    def update(self, other=None, **kwargs):
        if other:
            self.settings.update(**other.settings)
        self.settings.update(**kwargs)


class AzCommandGroup(CommandGroup):

    def __init__(self, command_loader, group_name, **kwargs):
        merged_kwargs = self._merge_kwargs(kwargs, base_kwargs=command_loader.module_kwargs)
        operations_tmpl = merged_kwargs.pop('operations_tmpl', None)
        super(AzCommandGroup, self).__init__(command_loader, group_name,
                                             operations_tmpl, **merged_kwargs)
        self.group_kwargs = merged_kwargs
        if operations_tmpl:
            self.group_kwargs['operations_tmpl'] = operations_tmpl
        self.is_stale = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.is_stale = True

    def _check_stale(self):
        if self.is_stale:
            message = "command authoring error: command group '{}' is stale! " \
                      "Check that the subsequent block for has a corresponding `as` statement.".format(self.group_name)
            logger.error(message)
            raise CLIError(message)

    def _merge_kwargs(self, kwargs, base_kwargs=None):
        base = base_kwargs if base_kwargs is not None else getattr(self, 'group_kwargs')
        return _merge_kwargs(kwargs, base, CLI_COMMAND_KWARGS)

    def _flatten_kwargs(self, kwargs, default_source_name):
        merged_kwargs = self._merge_kwargs(kwargs)
        default_source = merged_kwargs.get(default_source_name, None)
        if default_source:
            arg_source_copy = default_source.settings.copy()
            arg_source_copy.update(merged_kwargs)
            return arg_source_copy
        return merged_kwargs

    # pylint: disable=arguments-differ
    def command(self, name, method_name=None, **kwargs):
        """
        Register a CLI command
        :param name: Name of the command as it will be called on the command line
        :type name: str
        :param method_name: Name of the method the command maps to
        :type method_name: str
        :param kwargs: Keyword arguments. Supported keyword arguments include:
            - client_factory: Callable which returns a client needed to access the underlying command method. (function)
            - confirmation: Prompt prior to the action being executed. This is useful if the action
                            would cause a loss of data. (bool)
            - exception_handler: Exception handler for handling non-standard exceptions (function)
            - supports_no_wait: The command supports no wait. (bool)
            - no_wait_param: [deprecated] The name of a boolean parameter that will be exposed as `--no-wait`
              to skip long-running operation polling. (string)
            - transform: Transform function for transforming the output of the command (function)
            - table_transformer: Transform function or JMESPath query to be applied to table output to create a
                                 better output format for tables. (function or string)
            - resource_type: The ResourceType enum value to use with min or max API. (ResourceType)
            - min_api: Minimum API version required for commands within the group (string)
            - max_api: Maximum API version required for commands within the group (string)
        :rtype: None
        """
        self._check_stale()
        merged_kwargs = self._flatten_kwargs(kwargs, 'command_type')
        operations_tmpl = merged_kwargs['operations_tmpl']
        command_name = '{} {}'.format(self.group_name, name) if self.group_name else name
        operation = operations_tmpl.format(method_name) if operations_tmpl else None
        self.command_loader._cli_command(command_name, operation, **merged_kwargs)  # pylint: disable=protected-access

        return command_name

    def custom_command(self, name, method_name, **kwargs):
        """
        Register a custom CLI command.
        :param name: Name of the command as it will be called on the command line
        :type name: str
        :param method_name: Name of the method the command maps to
        :type method_name: str
        :param kwargs: Keyword arguments. Supported keyword arguments include:
            - client_factory: Callable which returns a client needed to access the underlying command method. (function)
            - confirmation: Prompt prior to the action being executed. This is useful if the action
                            would cause a loss of data. (bool)
            - exception_handler: Exception handler for handling non-standard exceptions (function)
            - supports_no_wait: The command supports no wait. (bool)
            - no_wait_param: [deprecated] The name of a boolean parameter that will be exposed as `--no-wait`
              to skip long running operation polling. (string)
            - transform: Transform function for transforming the output of the command (function)
            - table_transformer: Transform function or JMESPath query to be applied to table output to create a
                                 better output format for tables. (function or string)
            - resource_type: The ResourceType enum value to use with min or max API. (ResourceType)
            - min_api: Minimum API version required for commands within the group (string)
            - max_api: Maximum API version required for commands within the group (string)
        :rtype: None
        """
        self._check_stale()
        merged_kwargs = self._flatten_kwargs(kwargs, 'custom_command_type')
        operations_tmpl = merged_kwargs['operations_tmpl']
        command_name = '{} {}'.format(self.group_name, name) if self.group_name else name
        self.command_loader._cli_command(command_name,  # pylint: disable=protected-access
                                         operation=operations_tmpl.format(method_name),
                                         **merged_kwargs)

        return command_name

    # pylint: disable=no-self-use
    def _resolve_operation(self, kwargs, name, command_type=None, source_kwarg='command_type'):

        allowed_source_kwargs = ['command_type', 'custom_command_type']
        if source_kwarg not in allowed_source_kwargs:
            raise ValueError("command authoring error: 'source_kwarg' value '{}'. Allowed values: {}".format(
                source_kwarg, ' '.join(allowed_source_kwargs)))

        operations_tmpl = None
        if command_type:
            # Top priority: specified command_type for the parameter
            operations_tmpl = command_type.settings.get('operations_tmpl', None)

        if not operations_tmpl:
            # Second source: general operations_tmpl set for the command kwargs
            operations_tmpl = kwargs.get('operations_tmpl', None)

        if not operations_tmpl:
            # Final source: retrieve the operations_tmpl from the relevant 'command_type' or 'custom_command_type'
            command_type = kwargs.get(source_kwarg, None)
            operations_tmpl = command_type.settings.get('operations_tmpl', None)

        if not operations_tmpl:
            raise ValueError("command authoring error: unable to resolve 'operations_tmpl'")

        return operations_tmpl.format(name)

    def generic_update_command(self, name,
                               getter_name='get', getter_type=None,
                               setter_name='create_or_update', setter_type=None, setter_arg_name='parameters',
                               child_collection_prop_name=None, child_collection_key='name', child_arg_name='item_name',
                               custom_func_name=None, custom_func_type=None, **kwargs):
        from azure.cli.core.commands.arm import _cli_generic_update_command

        self._check_stale()
        merged_kwargs = _merge_kwargs(kwargs, self.group_kwargs, CLI_COMMAND_KWARGS)

        getter_op = self._resolve_operation(merged_kwargs, getter_name, getter_type)
        setter_op = self._resolve_operation(merged_kwargs, setter_name, setter_type)
        custom_func_op = self._resolve_operation(merged_kwargs, custom_func_name, custom_func_type,
                                                 source_kwarg='custom_command_type') if custom_func_name else None

        _cli_generic_update_command(
            self.command_loader,
            '{} {}'.format(self.group_name, name),
            getter_op=getter_op,
            setter_op=setter_op,
            setter_arg_name=setter_arg_name,
            custom_function_op=custom_func_op,
            child_collection_prop_name=child_collection_prop_name,
            child_collection_key=child_collection_key,
            child_arg_name=child_arg_name,
            **merged_kwargs)

    def generic_wait_command(self, name, getter_name='get', getter_type=None, **kwargs):
        from azure.cli.core.commands.arm import _cli_generic_update_command, _cli_generic_wait_command
        self._check_stale()
        merged_kwargs = _merge_kwargs(kwargs, self.group_kwargs, CLI_COMMAND_KWARGS)
        if getter_type:
            merged_kwargs = _merge_kwargs(getter_type.settings, merged_kwargs, CLI_COMMAND_KWARGS)
        getter_op = self._resolve_operation(merged_kwargs, getter_name, getter_type)
        _cli_generic_wait_command(
            self.command_loader,
            '{} {}'.format(self.group_name, name),
            getter_op=getter_op,
            **merged_kwargs)


# PARAMETERS UTILITIES

def patch_arg_make_required(argument):
    argument.settings['required'] = True


def patch_arg_make_optional(argument):
    argument.settings['required'] = False


def patch_arg_update_description(description):
    def _patch_action(argument):
        argument.settings['help'] = description

    return _patch_action


class AzArgumentContext(ArgumentsContext):

    def __init__(self, command_loader, scope, **kwargs):
        super(AzArgumentContext, self).__init__(command_loader, scope)
        self.scope = scope  # this is called "command" in knack, but that is not an accurate name
        self.group_kwargs = _merge_kwargs(kwargs, command_loader.module_kwargs, CLI_PARAM_KWARGS)
        self.is_stale = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.is_stale = True

    def _applicable(self):
        if self.command_loader.skip_applicability:
            return True
        command_name = self.command_loader.command_name
        scope = self.scope
        return command_name.startswith(scope)

    def _check_stale(self):
        if self.is_stale:
            message = "command authoring error: argument context '{}' is stale! " \
                      "Check that the subsequent block for has a corresponding `as` statement.".format(self.scope)
            logger.error(message)
            raise CLIError(message)

    def _flatten_kwargs(self, kwargs, arg_type):
        merged_kwargs = self._merge_kwargs(kwargs)
        if arg_type:
            arg_type_copy = arg_type.settings.copy()
            arg_type_copy.update(merged_kwargs)
            return arg_type_copy
        return merged_kwargs

    def _merge_kwargs(self, kwargs, base_kwargs=None):
        base = base_kwargs if base_kwargs is not None else getattr(self, 'group_kwargs')
        return _merge_kwargs(kwargs, base, CLI_PARAM_KWARGS)

    # pylint: disable=arguments-differ
    def argument(self, dest, arg_type=None, **kwargs):
        self._check_stale()
        if not self._applicable():
            return

        merged_kwargs = self._flatten_kwargs(kwargs, arg_type)
        resource_type = merged_kwargs.get('resource_type', None)
        min_api = merged_kwargs.get('min_api', None)
        max_api = merged_kwargs.get('max_api', None)
        operation_group = merged_kwargs.get('operation_group', None)
        if self.command_loader.supported_api_version(resource_type=resource_type,
                                                     min_api=min_api,
                                                     max_api=max_api,
                                                     operation_group=operation_group):
            super(AzArgumentContext, self).argument(dest, **merged_kwargs)
        else:
            super(AzArgumentContext, self).argument(dest, arg_type=ignore_type)

    def expand(self, dest, model_type, group_name=None, patches=None):
        # TODO:
        # two privates symbols are imported here. they should be made public or this utility class
        # should be moved into azure.cli.core
        from knack.introspection import extract_args_from_signature, option_descriptions

        self._check_stale()
        if not self._applicable():
            return

        if not patches:
            patches = dict()

        # fetch the documentation for model parameters first. for models, which are the classes
        # derive from msrest.serialization.Model and used in the SDK API to carry parameters, the
        # document of their properties are attached to the classes instead of constructors.
        parameter_docs = option_descriptions(model_type)

        def get_complex_argument_processor(expanded_arguments, assigned_arg, model_type):
            """
            Return a validator which will aggregate multiple arguments to one complex argument.
            """

            def _expansion_validator_impl(namespace):
                """
                The validator create a argument of a given type from a specific set of arguments from CLI
                command.
                :param namespace: The argparse namespace represents the CLI arguments.
                :return: The argument of specific type.
                """
                ns = vars(namespace)
                kwargs = dict((k, ns[k]) for k in ns if k in set(expanded_arguments))

                setattr(namespace, assigned_arg, model_type(**kwargs))

            return _expansion_validator_impl

        expanded_arguments = []
        for name, arg in extract_args_from_signature(model_type.__init__, excluded_params=EXCLUDED_PARAMS):
            arg = arg.type
            if name in parameter_docs:
                arg.settings['help'] = parameter_docs[name]

            if group_name:
                arg.settings['arg_group'] = group_name

            if name in patches:
                patches[name](arg)

            self.extra(name, arg_type=arg)
            expanded_arguments.append(name)

        self.argument(dest,
                      arg_type=ignore_type,
                      validator=get_complex_argument_processor(expanded_arguments, dest, model_type))

    def ignore(self, *args):
        self._check_stale()
        if not self._applicable():
            return

        for arg in args:
            super(AzArgumentContext, self).ignore(arg)

    def extra(self, dest, arg_type=None, **kwargs):
        self._check_stale()
        if not self._applicable():
            return

        if self.scope not in self.command_loader.command_table:
            raise ValueError("command authoring error: extra argument '{}' cannot be registered to a group-level "
                             "scope '{}'. It must be registered to a specific command.".format(dest, self.scope))

        merged_kwargs = self._flatten_kwargs(kwargs, arg_type)
        resource_type = merged_kwargs.get('resource_type', None)
        min_api = merged_kwargs.get('min_api', None)
        max_api = merged_kwargs.get('max_api', None)
        operation_group = merged_kwargs.get('operation_group', None)
        if self.command_loader.supported_api_version(resource_type=resource_type,
                                                     min_api=min_api,
                                                     max_api=max_api,
                                                     operation_group=operation_group):
            merged_kwargs.pop('dest', None)
            super(AzArgumentContext, self).extra(argument_dest=dest, **merged_kwargs)
