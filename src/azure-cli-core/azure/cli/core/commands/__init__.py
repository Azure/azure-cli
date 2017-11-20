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

from knack.arguments import CLICommandArgument
from knack.commands import CLICommand
from knack.invocation import CommandInvoker
from knack.log import get_logger

import six

import azure.cli.core.telemetry as telemetry

logger = get_logger(__name__)

CONFIRM_PARAM_NAME = 'yes'

# 1 hour in milliseconds
DEFAULT_QUERY_TIME_RANGE = 3600000

BLACKLISTED_MODS = ['context', 'shell', 'documentdb']


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
                logger.warning("Using default '%s' for arg %s", config_value, arg.name)
                overrides.settings['default'] = config_value
                overrides.settings['required'] = False

    def load_arguments(self):
        from azure.cli.core.commands.validators import DefaultStr, DefaultInt
        if self.arguments_loader:
            cmd_args = self.arguments_loader()
            if self.no_wait_param:
                cmd_args.append(
                    (self.no_wait_param,
                     CLICommandArgument(self.no_wait_param, options_list=['--no-wait'], action='store_true',
                                        help='Do not wait for the long running operation to finish.')))
            if self.confirmation:
                cmd_args.append(
                    (CONFIRM_PARAM_NAME,
                     CLICommandArgument(CONFIRM_PARAM_NAME, options_list=['--yes', '-y'], action='store_true',
                                        help='Do not prompt for confirmation.')))
            for (arg_name, arg) in cmd_args:
                arg_def = arg.type.settings.get('default', None)
                if isinstance(arg_def, str):
                    arg_def = DefaultStr(arg_def)
                elif isinstance(arg_def, int):
                    arg_def = DefaultInt(arg_def)
                if arg_def:
                    arg.type.settings['default'] = arg_def
            self.arguments.update(cmd_args)

    def update_argument(self, param_name, argtype):
        arg = self.arguments[param_name]
        self._resolve_default_value_from_cfg_file(arg, argtype)
        arg.type.update(other=argtype)

    def __call__(self, *args, **kwargs):

        from azure.cli.core import AzCommandsLoader
        cmd_args = args[0]

        if self.command_source and isinstance(self.command_source, ExtensionCommandSource) and\
           self.command_source.overrides_command:
            logger.warning(self.command_source.get_command_warn_msg())
        if self.deprecate_info is not None:
            text = 'This command is deprecating and will be removed in future releases.'
            if self.deprecate_info:
                text += " Use '{}' instead.".format(self.deprecate_info)
            logger.warning(text)

        confirm = CONFIRM_PARAM_NAME in cmd_args and not cmd_args.get(CONFIRM_PARAM_NAME) and \
            not self.cli_ctx.config.getboolean('core', 'disable_confirm_prompt', fallback=False)

        if confirm and not AzCommandsLoader.user_confirmed(confirm, cmd_args):
            from knack.events import EVENT_COMMAND_CANCELLED
            from knack.util import CLIError

            self.cli_ctx.raise_event(EVENT_COMMAND_CANCELLED, command=self.name, command_args=cmd_args)
            raise CLIError('Operation cancelled.')

        return self.handler(*args, **kwargs)

    def get_api_version(self, resource_type=None):
        resource_type = resource_type or self.command_kwargs.get('resource_type', None)
        return self.loader.get_api_version(resource_type=resource_type)

    def supported_api_version(self, resource_type=None, min_api=None, max_api=None):
        resource_type = resource_type or self.command_kwargs.get('resource_type', None)
        return self.loader.supported_api_version(resource_type=resource_type, min_api=min_api, max_api=max_api)

    def get_models(self, *attr_args, **kwargs):
        resource_type = kwargs.get('resource_type', self.command_kwargs.get('resource_type', None))
        return self.loader.get_sdk(*attr_args, resource_type=resource_type, mod='models')


# pylint: disable=too-few-public-methods
class AzCliCommandInvoker(CommandInvoker):

    # pylint: disable=too-many-statements
    def execute(self, args):
        import knack.events as events
        from knack.util import CommandResultItem, todict

        # TODO: Can't simply be invoked as an event because args are transformed
        args = _pre_command_table_create(self.cli_ctx, args)

        self.cli_ctx.raise_event(events.EVENT_INVOKER_PRE_CMD_TBL_CREATE, args=args)
        self.commands_loader.load_command_table(args)
        command = self._rudimentary_get_command(args)

        try:
            cmd_tbl = {command: self.commands_loader.command_table[command]}
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

            cmd_tbl = {}
            group_names = set()
            for cmd_name, cmd in self.commands_loader.command_table.items():
                if command and not cmd_name.startswith(command):
                    continue

                cmd_stub = cmd_name[len(command):].strip()
                group_name = cmd_stub.split(' ', 1)[0]
                if group_name not in group_names:
                    cmd_tbl[cmd_name] = cmd
                    group_names.add(group_name)

        self.commands_loader.load_arguments(command)
        self.commands_loader._update_command_definitions()  # pylint: disable=protected-access
        self.cli_ctx.raise_event(events.EVENT_INVOKER_POST_CMD_TBL_CREATE, cmd_tbl=cmd_tbl)
        self.parser.cli_ctx = self.cli_ctx
        self.parser.load_command_table(cmd_tbl)

        self.cli_ctx.raise_event(events.EVENT_INVOKER_CMD_TBL_LOADED, cmd_tbl=cmd_tbl, parser=self.parser)

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

        self.cli_ctx.raise_event(events.EVENT_INVOKER_PRE_PARSE_ARGS, args=args)
        parsed_args = self.parser.parse_args(args)
        self.cli_ctx.raise_event(events.EVENT_INVOKER_POST_PARSE_ARGS, command=parsed_args.command, args=parsed_args)

        # TODO: This fundamentally alters the way Knack.invocation works here. Cannot be customized
        # with an event. Would need to be customized via inheritance.
        results = []
        for expanded_arg in _explode_list_args(parsed_args):

            cmd = expanded_arg.func
            if hasattr(expanded_arg, 'cmd'):
                expanded_arg.cmd = cmd

            self._validation(expanded_arg)

            self.data['command'] = expanded_arg.command

            params = self._filter_params(expanded_arg)

            command_source = cmd_tbl[command].command_source
            telemetry.set_command_details(self.data['command'],
                                          self.data['output'],
                                          [p for p in args if p.startswith('-')],
                                          extension_name=command_source.extension_name if command_source else None)

            try:
                result = cmd(params)
                no_wait_param = cmd.no_wait_param
                if no_wait_param and getattr(expanded_arg, no_wait_param, False):
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
                self.cli_ctx.raise_event(events.EVENT_INVOKER_TRANSFORM_RESULT, event_data=event_data)
                self.cli_ctx.raise_event(events.EVENT_INVOKER_FILTER_RESULT, event_data=event_data)
                result = event_data['result']

                if result:
                    results.append(result)

            except Exception as ex:  # pylint: disable=broad-except
                if cmd.exception_handler:
                    cmd.exception_handler(ex)
                    return
                else:
                    six.reraise(*sys.exc_info())

        if results and len(results) == 1:
            results = results[0]

        return CommandResultItem(results,
                                 table_transformer=cmd_tbl[parsed_args.command].table_transformer,
                                 is_query_active=self.data['query_active'])

    def _build_kwargs(self, func, ns):  # pylint: disable=no-self-use
        import inspect
        arg_spec = inspect.getargspec(func).args  # pylint: disable=deprecated-method
        kwargs = {}
        if 'cmd' in arg_spec:
            kwargs['cmd'] = ns._cmd  # pylint: disable=protected-access
        if 'namespace' in arg_spec:
            kwargs['namespace'] = ns
        if 'ns' in arg_spec:
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
        for validator in getattr(ns, '_argument_validators', []):
            validator(**self._build_kwargs(validator, ns))
        try:
            delattr(ns, '_argument_validators')
        except AttributeError:
            pass


class LongRunningOperation(object):  # pylint: disable=too-few-public-methods

    def __init__(self, cli_ctx, start_msg='', finish_msg='',
                 poller_done_interval_ms=1000.0, progress_controller=None):

        self.cli_ctx = cli_ctx
        self.start_msg = start_msg
        self.finish_msg = finish_msg
        self.poller_done_interval_ms = poller_done_interval_ms
        self.progress_controller = progress_controller or cli_ctx.get_progress_controller()
        self.deploy_dict = {}
        self.last_progress_report = datetime.datetime.now()

    def _delay(self):
        time.sleep(self.poller_done_interval_ms / 1000.0)

    def _generate_template_progress(self, correlation_id):  # pylint: disable=no-self-use
        """ gets the progress for template deployments """
        from azure.cli.core.commands.client_factory import get_mgmt_service_client
        from azure.monitor import MonitorClient

        if correlation_id is not None:  # pylint: disable=too-many-nested-blocks
            formatter = "eventTimestamp ge {}"

            end_time = datetime.datetime.utcnow()
            start_time = end_time - datetime.timedelta(seconds=DEFAULT_QUERY_TIME_RANGE)
            odata_filters = formatter.format(start_time.strftime('%Y-%m-%dT%H:%M:%SZ'))

            odata_filters = "{} and {} eq '{}'".format(odata_filters, 'correlationId', correlation_id)

            activity_log = get_mgmt_service_client(self.cli_ctx, MonitorClient).activity_logs.list(filter=odata_filters)

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
        from msrest.exceptions import ClientException

        correlation_message = ''
        self.progress_controller.begin()
        correlation_id = None

        is_verbose = any(handler.level <= logs.INFO for handler in logger.handlers)

        while not poller.done():
            self.progress_controller.add(message='Running')
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
                self.progress_controller.stop()
                logger.error('Long running operation wait cancelled.  %s', correlation_message)
                raise

        try:
            result = poller.result()
        except ClientException as client_exception:
            from azure.cli.core.commands.arm import handle_long_running_operation_exception
            self.progress_controller.stop()
            handle_long_running_operation_exception(client_exception)

        self.progress_controller.end()
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

        # --validate returns a 'normal' response
        return result


def _load_command_loader(loader, args, name, prefix):
    module = import_module(prefix + name)
    loader_cls = getattr(module, 'COMMAND_LOADER_CLS', None)
    command_table = {}

    if loader_cls:
        command_loader = loader_cls(cli_ctx=loader.cli_ctx)
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
        logger.debug("Command module '%s' is missing `COMMAND_LOADER_CLS` entry.", name)
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
    if obj.__class__.__name__ == 'AzureOperationPoller':
        from msrestazure.azure_operation import AzureOperationPoller
        return isinstance(obj, AzureOperationPoller)
    return False
