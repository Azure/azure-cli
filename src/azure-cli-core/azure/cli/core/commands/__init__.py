# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function

import datetime
import json
import logging as logs
import os
import sys
import time
from importlib import import_module
import six

from knack.arguments import CLICommandArgument
from knack.commands import CLICommand, CommandGroup
from knack.deprecation import ImplicitDeprecated, resolve_deprecate_info
from knack.invocation import CommandInvoker
from knack.log import get_logger
from knack.util import CLIError

# pylint: disable=unused-import
from azure.cli.core.commands.constants import (
    BLACKLISTED_MODS, DEFAULT_QUERY_TIME_RANGE, CLI_COMMON_KWARGS, CLI_COMMAND_KWARGS, CLI_PARAM_KWARGS,
    CLI_POSITIONAL_PARAM_KWARGS, CONFIRM_PARAM_NAME)
from azure.cli.core.commands.parameters import (
    AzArgumentContext, patch_arg_make_required, patch_arg_make_optional)
from azure.cli.core.extension import get_extension
from azure.cli.core.util import get_command_type_kwarg, read_file_content, get_arg_list, poller_classes
import azure.cli.core.telemetry as telemetry

logger = get_logger(__name__)


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
        if path == '-':
            content = sys.stdin.read()
        else:
            content = read_file_content(os.path.expanduser(path), allow_binary=True)

        return content.rstrip(os.linesep)

    def _maybe_load_file(arg):
        ix = arg.find('@')
        if ix == -1:  # no @ found
            return arg

        poss_file = arg[ix + 1:]
        if not poss_file:  # if nothing after @ then it can't be a file
            return arg
        elif ix == 0:
            try:
                return _load_file(poss_file)
            except IOError:
                logger.debug("Failed to load @'%s', assume not a file", arg)
                return arg

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
        if isinstance(self.command_source, ExtensionCommandSource) and self.command_source.overrides_command:
            logger.warning(self.command_source.get_command_warn_msg())

        cmd_args = args[0]

        confirm = self.confirmation and not cmd_args.pop('yes', None) \
            and not self.cli_ctx.config.getboolean('core', 'disable_confirm_prompt', fallback=False)

        if confirm and not self._user_confirmed(self.confirmation, cmd_args):
            from knack.events import EVENT_COMMAND_CANCELLED
            self.cli_ctx.raise_event(EVENT_COMMAND_CANCELLED, command=self.name, command_args=cmd_args)
            raise CLIError('Operation cancelled.')

        return self.handler(*args, **kwargs)

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
        self.cli_ctx.raise_event(EVENT_INVOKER_POST_CMD_TBL_CREATE, commands_loader=self.commands_loader)
        self.parser.cli_ctx = self.cli_ctx
        self.parser.load_command_table(self.commands_loader)

        self.cli_ctx.raise_event(EVENT_INVOKER_CMD_TBL_LOADED, cmd_tbl=self.commands_loader.command_table,
                                 parser=self.parser)

        if not args:
            self.parser.enable_autocomplete()
            subparser = self.parser.subparsers[tuple()]
            self.help.show_welcome(subparser)

            # TODO: No event in base with which to target
            telemetry.set_command_details('az')
            telemetry.set_success(summary='welcome')
            return None

        if args[0].lower() == 'help':
            args[0] = '--help'

        self.parser.enable_autocomplete()

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
            extension_name = None
            try:
                if isinstance(command_source, ExtensionCommandSource):
                    extension_name = command_source.extension_name
                    extension_version = get_extension(command_source.extension_name).version
            except Exception:  # pylint: disable=broad-except
                pass

            telemetry.set_command_details(self.cli_ctx.data['command'], self.data['output'],
                                          [(p.split('=', 1)[0] if p.startswith('--') else p[:2]) for p in args if
                                           (p.startswith('-') and len(p) > 1)],
                                          extension_name=extension_name, extension_version=extension_version)
            if extension_name:
                self.data['command_extension_name'] = extension_name

            deprecations = [] + getattr(expanded_arg, '_argument_deprecations', [])
            if cmd.deprecate_info:
                deprecations.append(cmd.deprecate_info)

            # search for implicit deprecation
            path_comps = cmd.name.split()[:-1]
            implicit_deprecate_info = None
            while path_comps and not implicit_deprecate_info:
                implicit_deprecate_info = resolve_deprecate_info(self.cli_ctx, ' '.join(path_comps))
                del path_comps[-1]

            if implicit_deprecate_info:
                deprecate_kwargs = implicit_deprecate_info.__dict__.copy()
                deprecate_kwargs['object_type'] = 'command'
                del deprecate_kwargs['_get_tag']
                del deprecate_kwargs['_get_message']
                deprecations.append(ImplicitDeprecated(**deprecate_kwargs))

            for d in deprecations:
                logger.warning(d.message)

            try:
                result = cmd(params)
                if cmd.supports_no_wait and getattr(expanded_arg, 'no_wait', False):
                    result = None
                elif cmd.no_wait_param and getattr(expanded_arg, cmd.no_wait_param, False):
                    result = None

                transform_op = cmd.command_kwargs.get('transform', None)
                if transform_op:
                    result = transform_op(result)

                if _is_poller(result):
                    result = LongRunningOperation(self.cli_ctx, 'Starting {}'.format(cmd.name))(result)
                elif _is_paged(result):
                    result = list(result)

                result = todict(result, AzCliCommandInvoker.remove_additional_prop_layer)
                event_data = {'result': result}
                self.cli_ctx.raise_event(EVENT_INVOKER_TRANSFORM_RESULT, event_data=event_data)
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

        event_data = {'result': results}
        self.cli_ctx.raise_event(EVENT_INVOKER_FILTER_RESULT, event_data=event_data)

        return CommandResultItem(
            event_data['result'],
            table_transformer=self.commands_loader.command_table[parsed_args.command].table_transformer,
            is_query_active=self.data['query_active'])

    def _build_kwargs(self, func, ns):  # pylint: disable=no-self-use
        arg_list = get_arg_list(func)
        kwargs = {}
        if 'cmd' in arg_list:
            kwargs['cmd'] = ns._cmd  # pylint: disable=protected-access
        if 'namespace' in arg_list:
            kwargs['namespace'] = ns
        if 'ns' in arg_list:
            kwargs['ns'] = ns
        return kwargs

    @staticmethod
    def remove_additional_prop_layer(obj, converted_dic):
        from msrest.serialization import Model
        if isinstance(obj, Model):
            # let us make sure this is the additional properties auto-generated by SDK
            if ('additionalProperties' in converted_dic and isinstance(obj.additional_properties, dict)):
                converted_dic.update(converted_dic.pop('additionalProperties'))
        return converted_dic

    def _rudimentary_get_command(self, args):  # pylint: disable=no-self-use
        """ Rudimentary parsing to get the command """
        nouns = []
        command_names = self.commands_loader.command_table.keys()
        for arg in args:
            if arg and arg[0] != '-':
                nouns.append(arg)
            else:
                break

        def _find_args(args):
            search = ' '.join(args)
            return next((x for x in command_names if x.startswith(search)), False)

        # since the command name may be immediately followed by a positional arg, strip those off
        while nouns and not _find_args(nouns):
            del nouns[-1]
        return ' '.join(nouns)

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
    from azure.cli.core.profiles import PROFILE_TYPE
    module = import_module(prefix + name)
    loader_cls = getattr(module, 'COMMAND_LOADER_CLS', None)
    command_table = {}

    if loader_cls:
        command_loader = loader_cls(cli_ctx=loader.cli_ctx)
        loader.loaders.append(command_loader)  # This will be used by interactive
        if command_loader.supported_api_version(min_api=command_loader.min_profile, max_api=command_loader.max_profile,
                                                resource_type=PROFILE_TYPE):
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
    return command_table, command_loader.command_group_table


def _load_extension_command_loader(loader, args, ext):
    return _load_command_loader(loader, args, ext, '')


def _load_module_command_loader(loader, args, mod):
    return _load_command_loader(loader, args, mod, 'azure.cli.command_modules.')


class ExtensionCommandSource(object):
    """ Class for commands contributed by an extension """

    def __init__(self, overrides_command=False, extension_name=None, preview=False):
        super(ExtensionCommandSource, self).__init__()
        # True if the command overrides a CLI command
        self.overrides_command = overrides_command
        self.extension_name = extension_name
        self.preview = preview

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

    def get_preview_warn_msg(self):
        if self.preview:
            return "The extension is in preview"
        return None


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
        Register a CLI command.
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
        return self._command(name, method_name=method_name, **kwargs)

    def custom_command(self, name, method_name=None, **kwargs):
        """
        Register a CLI command.
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
        return self._command(name, method_name=method_name, custom_command=True, **kwargs)

    def _command(self, name, method_name, custom_command=False, **kwargs):
        self._check_stale()
        merged_kwargs = self._flatten_kwargs(kwargs, get_command_type_kwarg(custom_command))
        # don't inherit deprecation info from command group
        merged_kwargs['deprecate_info'] = kwargs.get('deprecate_info', None)

        operations_tmpl = merged_kwargs['operations_tmpl']
        command_name = '{} {}'.format(self.group_name, name) if self.group_name else name
        self.command_loader._cli_command(command_name,  # pylint: disable=protected-access
                                         operation=operations_tmpl.format(method_name),
                                         **merged_kwargs)

        return command_name

    # pylint: disable=no-self-use
    def _resolve_operation(self, kwargs, name, command_type=None, custom_command=False):
        source_kwarg = get_command_type_kwarg(custom_command)

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

    def generic_update_command(self, name, getter_name='get', getter_type=None,
                               setter_name='create_or_update', setter_type=None, setter_arg_name='parameters',
                               child_collection_prop_name=None, child_collection_key='name', child_arg_name='item_name',
                               custom_func_name=None, custom_func_type=None, **kwargs):
        from azure.cli.core.commands.arm import _cli_generic_update_command
        self._check_stale()
        merged_kwargs = self._flatten_kwargs(kwargs, get_command_type_kwarg())
        merged_kwargs_custom = self._flatten_kwargs(kwargs, get_command_type_kwarg(custom_command=True))
        # don't inherit deprecation info from command group
        merged_kwargs['deprecate_info'] = kwargs.get('deprecate_info', None)

        getter_op = self._resolve_operation(merged_kwargs, getter_name, getter_type)
        setter_op = self._resolve_operation(merged_kwargs, setter_name, setter_type)
        custom_func_op = self._resolve_operation(merged_kwargs_custom, custom_func_name, custom_func_type,
                                                 custom_command=True) if custom_func_name else None
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

    def wait_command(self, name, getter_name='get', **kwargs):
        self._wait_command(name, getter_name=getter_name, custom_command=False, **kwargs)

    def custom_wait_command(self, name, getter_name='get', **kwargs):
        self._wait_command(name, getter_name=getter_name, custom_command=True, **kwargs)

    def generic_wait_command(self, name, getter_name='get', getter_type=None, **kwargs):
        self._wait_command(name, getter_name=getter_name, getter_type=getter_type, **kwargs)

    def _wait_command(self, name, getter_name='get', getter_type=None, custom_command=False, **kwargs):
        from azure.cli.core.commands.arm import _cli_wait_command
        self._check_stale()
        merged_kwargs = self._flatten_kwargs(kwargs, get_command_type_kwarg(custom_command))
        # don't inherit deprecation info from command group
        merged_kwargs['deprecate_info'] = kwargs.get('deprecate_info', None)

        if getter_type:
            merged_kwargs = _merge_kwargs(getter_type.settings, merged_kwargs, CLI_COMMAND_KWARGS)
        getter_op = self._resolve_operation(merged_kwargs, getter_name, getter_type, custom_command=custom_command)
        _cli_wait_command(self.command_loader, '{} {}'.format(self.group_name, name), getter_op=getter_op,
                          custom_command=custom_command, **merged_kwargs)

    def show_command(self, name, getter_name='get', **kwargs):
        self._show_command(name, getter_name=getter_name, custom_command=False, **kwargs)

    def custom_show_command(self, name, getter_name='get', **kwargs):
        self._show_command(name, getter_name=getter_name, custom_command=True, **kwargs)

    def _show_command(self, name, getter_name='get', getter_type=None, custom_command=False, **kwargs):
        from azure.cli.core.commands.arm import _cli_show_command
        self._check_stale()
        merged_kwargs = self._flatten_kwargs(kwargs, get_command_type_kwarg(custom_command))
        # don't inherit deprecation info from command group
        merged_kwargs['deprecate_info'] = kwargs.get('deprecate_info', None)

        if getter_type:
            merged_kwargs = _merge_kwargs(getter_type.settings, merged_kwargs, CLI_COMMAND_KWARGS)
        getter_op = self._resolve_operation(merged_kwargs, getter_name, getter_type, custom_command=custom_command)
        _cli_show_command(self.command_loader, '{} {}'.format(self.group_name, name), getter_op=getter_op,
                          custom_command=custom_command, **merged_kwargs)
