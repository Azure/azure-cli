# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=too-many-lines

import argparse
import datetime
import json
import logging as logs
import os
import re
import sys
import time
import copy
from importlib import import_module

# pylint: disable=unused-import
from azure.cli.core.commands.constants import (
    BLOCKED_MODS, DEFAULT_QUERY_TIME_RANGE, CLI_COMMON_KWARGS, CLI_COMMAND_KWARGS, CLI_PARAM_KWARGS,
    CLI_POSITIONAL_PARAM_KWARGS, CONFIRM_PARAM_NAME)
from azure.cli.core.commands.parameters import (
    AzArgumentContext, patch_arg_make_required, patch_arg_make_optional)
from azure.cli.core.extension import get_extension
from azure.cli.core.util import (
    get_command_type_kwarg, read_file_content, get_arg_list, poller_classes)
from azure.cli.core.local_context import LocalContextAction
from azure.cli.core import telemetry
from azure.cli.core.commands.progress import IndeterminateProgressBar

from knack.arguments import CLICommandArgument
from knack.commands import CLICommand, CommandGroup, PREVIEW_EXPERIMENTAL_CONFLICT_ERROR
from knack.deprecation import ImplicitDeprecated, resolve_deprecate_info
from knack.invocation import CommandInvoker
from knack.preview import ImplicitPreviewItem, PreviewItem, resolve_preview_info
from knack.experimental import ImplicitExperimentalItem, ExperimentalItem, resolve_experimental_info
from knack.log import get_logger, CLILogging
from knack.util import CLIError, CommandResultItem, todict
from knack.events import EVENT_INVOKER_TRANSFORM_RESULT
from knack.validators import DefaultStr

try:
    t_JSONDecodeError = json.JSONDecodeError
except AttributeError:  # in Python 2.7
    t_JSONDecodeError = ValueError

logger = get_logger(__name__)
DEFAULT_CACHE_TTL = '10'


def _explode_list_args(args):
    '''Iterate through each attribute member of args and create a copy with
    the IterateValues 'flattened' to only contain a single value

    Ex.
        { a1:'x', a2:IterateValue(['y', 'z']) } => [{ a1:'x', a2:'y'),{ a1:'x', a2:'z'}]
    '''
    from azure.cli.core.commands.validators import IterateValue
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
        if ix == 0:
            try:
                return _load_file(poss_file)
            except IOError:
                logger.debug("Failed to load '%s', assume not a file", arg)
                return arg

        # if @ not at the start it can't be a file
        return arg

    def _expand_file_prefix(arg):
        arg_split = arg.split('=', 1)
        try:
            return '='.join([arg_split[0], _maybe_load_file(arg_split[1])])
        except IndexError:
            return _maybe_load_file(arg_split[0])

    return [_expand_file_prefix(arg) for arg in args]


def _pre_command_table_create(cli_ctx, args):
    cli_ctx.refresh_request_id()
    return _expand_file_prefixed_files(args)


# pylint: disable=too-many-instance-attributes
class CacheObject:

    def path(self, args, kwargs):
        from azure.cli.core._environment import get_config_dir
        from azure.cli.core.commands.client_factory import get_subscription_id

        cli_ctx = self._cmd.cli_ctx
        subscription_id = get_subscription_id(cli_ctx)
        if not subscription_id:
            raise CLIError('subscription ID unexpectedly empty')
        if not cli_ctx.cloud.name:
            raise CLIError('cloud name unexpectedly empty')
        copy_kwargs = kwargs.copy()
        copy_kwargs.pop('self', None)
        resource_group = copy_kwargs.pop('resource_group_name', None) or args[0]

        if len(args) > 2:
            raise CLIError('expected 2 args, got {}: {}'.format(len(args), args))
        if len(copy_kwargs) > 1:
            raise CLIError('expected 1 kwarg, got {}: {}'.format(len(copy_kwargs), copy_kwargs))

        try:
            resource_name = args[-1]
        except IndexError:
            resource_name = list(copy_kwargs.values())[0]

        self._resource_group = resource_group
        self._resource_name = resource_name

        directory = os.path.join(
            get_config_dir(),
            'object_cache',
            cli_ctx.cloud.name,
            subscription_id,
            self._resource_group,
            self._model_name
        )
        filename = '{}.json'.format(resource_name)
        return directory, filename

    def _resolve_model(self):
        if self._model_name and self._model_path:
            return

        import inspect
        op_metadata = inspect.getmembers(self._operation)
        doc_string = ''
        for key, value in op_metadata:
            if key == '__doc__':
                doc_string = value or ''
                break

        doc_string = doc_string.replace('\r', '').replace('\n', ' ')
        doc_string = re.sub(' +', ' ', doc_string)

        # pylint: disable=line-too-long
        # In track1, the doc_string for return type is like ':return: An instance of LROPoller that returns ConnectionSharedKey or ClientRawResponse<ConnectionSharedKey>'
        # In track2, the doc_string for return type is like ':return: An instance of LROPoller that returns either ConnectionSharedKey or the result of cls(response)'
        # Add '(?:either )?' to match 'either' zero or one times to support track2.
        model_name_regex = re.compile(r':return: (?:.*?that returns (?:either )?)?(?P<model>[a-zA-Z]*)')
        model_path_regex = re.compile(r':rtype:.*(?P<path>azure.mgmt[a-zA-Z0-9_\.]*)')
        try:
            self._model_name = model_name_regex.search(doc_string).group('model')
            if not self._model_path:
                self._model_path = model_path_regex.search(doc_string).group('path').rsplit('.', 1)[0]
        except AttributeError:
            return

    def _dump_to_file(self, open_file):
        cache_obj_dump = json.dumps({
            'last_saved': self.last_saved,
            '_payload': self._payload
        })
        open_file.write(cache_obj_dump)

    def load(self, args, kwargs):
        directory, filename = self.path(args, kwargs)
        with open(os.path.join(directory, filename), 'r') as f:
            logger.info(
                "Loading %s '%s' from cache: %s", self._model_name, self._resource_name,
                os.path.join(directory, filename)
            )
            obj_data = json.loads(f.read())
            self._payload = obj_data['_payload']
            self.last_saved = obj_data['last_saved']
        self._payload = self.result()

    def save(self, args, kwargs):
        from knack.util import ensure_dir
        directory, filename = self.path(args, kwargs)
        ensure_dir(directory)
        with open(os.path.join(directory, filename), 'w') as f:
            logger.info(
                "Caching %s '%s' as: %s", self._model_name, self._resource_name,
                os.path.join(directory, filename)
            )
            self.last_saved = str(datetime.datetime.now())
            self._dump_to_file(f)

    def result(self):
        module = import_module(self._model_path)
        model_cls = getattr(module, self._model_name)
        # model_cls = self._cmd.get_models(self._model_type)
        # todo: Remove temp work around!!!
        if model_cls is None:
            from azure.mgmt.imagebuilder.models import ImageTemplate
            model_cls = ImageTemplate
        return model_cls.deserialize(self._payload)

    def prop_dict(self):
        return {
            'model': self._model_name,
            'name': self._resource_name,
            'group': self._resource_group
        }

    def __init__(self, cmd, payload, operation, model_path=None):
        self._cmd = cmd
        self._operation = operation
        self._resource_group = None
        self._resource_name = None
        self._model_name = None
        self._model_path = model_path
        self._payload = payload
        self.last_saved = None
        self._resolve_model()

    def __getattribute__(self, key):
        try:
            payload = object.__getattribute__(self, '_payload')
            return payload.__getattribute__(key)
        except AttributeError:
            return super(CacheObject, self).__getattribute__(key)

    def __setattr__(self, key, value):
        try:
            return self._payload.__setattr__(key, value)
        except AttributeError:
            return super(CacheObject, self).__setattr__(key, value)


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

    # pylint: disable=no-self-use
    def _add_vscode_extension_metadata(self, arg, overrides):
        """ Adds metadata for use by the VSCode CLI extension. Do
            not remove or modify without contacting the VSCode team. """
        if not hasattr(arg.type, 'required_tooling'):
            required = arg.type.settings.get('required', False)
            setattr(arg.type, 'required_tooling', required)
        if 'configured_default' in overrides.settings:
            def_config = overrides.settings.get('configured_default', None)
            setattr(arg.type, 'default_name_tooling', def_config)

    def _resolve_default_value_from_config_file(self, arg, overrides):

        self._add_vscode_extension_metadata(arg, overrides)

        # same blunt mechanism like we handled id-parts, for create command, no name default
        if not (self.name.split()[-1] == 'create' and overrides.settings.get('metavar', None) == 'NAME'):
            super(AzCliCommand, self)._resolve_default_value_from_config_file(arg, overrides)

        self._resolve_default_value_from_local_context(arg, overrides)

    def _resolve_default_value_from_local_context(self, arg, overrides):
        if self.cli_ctx.local_context.is_on:
            lca = overrides.settings.get('local_context_attribute', None)
            if not lca or not lca.actions or LocalContextAction.GET not in lca.actions:
                return
            if lca.name:
                local_context = self.cli_ctx.local_context
                value = local_context.get(self.name, lca.name)
                if value:
                    logger.debug("parameter persistence '%s' for arg %s", value, arg.name)
                    overrides.settings['default'] = DefaultStr(value)
                    overrides.settings['required'] = False
                    overrides.settings['default_value_source'] = 'Local Context'

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

    def __call__(self, *args, **kwargs):
        return self.handler(*args, **kwargs)

    def _merge_kwargs(self, kwargs, base_kwargs=None):
        base = base_kwargs if base_kwargs is not None else getattr(self, 'command_kwargs')
        return _merge_kwargs(kwargs, base)

    def get_api_version(self, resource_type=None, operation_group=None):
        resource_type = resource_type or self.command_kwargs.get('resource_type', None)
        return self.loader.get_api_version(resource_type=resource_type, operation_group=operation_group)

    def supported_api_version(self, resource_type=None, min_api=None, max_api=None,
                              operation_group=None, parameter_name=None):
        if min_api and parameter_name:
            parameter_name = None
        if parameter_name is not None and parameter_name in self.arguments:
            min_api = self.arguments[parameter_name].type.settings.get('min_api', None)
        resource_type = resource_type or self.command_kwargs.get('resource_type', None)
        return self.loader.supported_api_version(resource_type=resource_type, min_api=min_api, max_api=max_api,
                                                 operation_group=operation_group)

    def get_models(self, *attr_args, **kwargs):
        resource_type = kwargs.get('resource_type', self.command_kwargs.get('resource_type', None))
        operation_group = kwargs.get('operation_group', self.command_kwargs.get('operation_group', None))
        return self.loader.get_sdk(*attr_args, resource_type=resource_type, mod='models',
                                   operation_group=operation_group)

    def update_context(self, obj_inst):
        class UpdateContext:
            def __init__(self, instance):
                self.instance = instance

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                pass

            def set_param(self, prop, value, allow_clear=True, curr_obj=None):
                curr_obj = curr_obj or self.instance
                if '.' in prop:
                    prop, path = prop.split('.', 1)
                    curr_obj = getattr(curr_obj, prop)
                    self.set_param(path, value, allow_clear=allow_clear, curr_obj=curr_obj)
                elif value == '' and allow_clear:
                    setattr(curr_obj, prop, None)
                elif value is not None:
                    setattr(curr_obj, prop, value)
        return UpdateContext(obj_inst)


def _is_stale(cli_ctx, cache_obj):
    cache_ttl = None
    try:
        cache_ttl = cli_ctx.config.get('core', 'cache_ttl')
    except Exception as ex:  # pylint: disable=broad-except
        # TODO: No idea why Python2's except clause fails to catch NoOptionError, but this
        # is a temp workaround
        cls_str = str(ex.__class__)
        if 'NoOptionError' in cls_str or 'NoSectionError' in cls_str:
            # ensure a default value exists even if not previously set
            cli_ctx.config.set_value('core', 'cache_ttl', DEFAULT_CACHE_TTL)
            cache_ttl = DEFAULT_CACHE_TTL
        else:
            raise ex
    time_now = datetime.datetime.now()
    time_cache = datetime.datetime.strptime(cache_obj.last_saved, '%Y-%m-%d %H:%M:%S.%f')
    return time_now - time_cache > datetime.timedelta(minutes=int(cache_ttl))


def cached_get(cmd_obj, operation, *args, **kwargs):

    def _get_operation():
        result = None
        if args:
            result = operation(*args)
        elif kwargs is not None:
            result = operation(**kwargs)
        return result

    # early out if the command does not use the cache
    if not cmd_obj.command_kwargs.get('supports_local_cache', False):
        return _get_operation()

    # allow overriding model path, e.g. for extensions
    model_path = cmd_obj.command_kwargs.get('model_path', None)

    cache_obj = CacheObject(cmd_obj, None, operation, model_path=model_path)
    try:
        cache_obj.load(args, kwargs)
        if _is_stale(cmd_obj.cli_ctx, cache_obj):
            message = "{model} '{name}' stale in cache. Retrieving from Azure...".format(**cache_obj.prop_dict())
            logger.warning(message)
            return _get_operation()
        return cache_obj
    except Exception:  # pylint: disable=broad-except
        message = "{model} '{name}' not found in cache. Retrieving from Azure...".format(**cache_obj.prop_dict())
        logger.debug(message)
        return _get_operation()


def cached_put(cmd_obj, operation, parameters, *args, setter_arg_name='parameters', **kwargs):
    """
    setter_arg_name: The name of the argument in the setter which corresponds to the object being updated.
    In track2, unknown kwargs will raise, so we should not pass 'parameters" for operation when the name of the argument
    in the setter which corresponds to the object being updated is not 'parameters'.
    """
    def _put_operation():
        result = None
        if args:
            extended_args = args + (parameters,)
            result = operation(*extended_args)
        elif kwargs is not None:
            kwargs[setter_arg_name] = parameters
            result = operation(**kwargs)
            del kwargs[setter_arg_name]
        return result

    # early out if the command does not use the cache
    if not cmd_obj.command_kwargs.get('supports_local_cache', False):
        return _put_operation()

    use_cache = cmd_obj.cli_ctx.data.get('_cache', False)
    if not use_cache:
        result = _put_operation()

    # allow overriding model path, e.g. for extensions
    model_path = cmd_obj.command_kwargs.get('model_path', None)

    cache_obj = CacheObject(cmd_obj, parameters.serialize(), operation, model_path=model_path)
    if use_cache:
        cache_obj.save(args, kwargs)
        return cache_obj

    # for a successful PUT, attempt to delete the cache file
    obj_dir, obj_file = cache_obj.path(args, kwargs)
    obj_path = os.path.join(obj_dir, obj_file)
    try:
        os.remove(obj_path)
    except (OSError, IOError):  # FileNotFoundError introduced in Python 3
        pass
    return result


def upsert_to_collection(parent, collection_name, obj_to_add, key_name, warn=True):

    if not getattr(parent, collection_name, None):
        setattr(parent, collection_name, [])
    collection = getattr(parent, collection_name, None)

    value = getattr(obj_to_add, key_name)
    if value is None:
        raise CLIError(
            "Unable to resolve a value for key '{}' with which to match.".format(key_name))
    match = next((x for x in collection if getattr(x, key_name, None) == value), None)
    if match:
        if warn:
            logger.warning("Item '%s' already exists. Replacing with new values.", value)
        collection.remove(match)
    collection.append(obj_to_add)


def get_property(items, name):
    result = next((x for x in items if x.name.lower() == name.lower()), None)
    if not result:
        raise CLIError("Property '{}' does not exist".format(name))
    return result


# pylint: disable=too-few-public-methods
class AzCliCommandInvoker(CommandInvoker):

    # pylint: disable=too-many-statements,too-many-locals,too-many-branches
    def execute(self, args):
        from knack.events import (EVENT_INVOKER_PRE_CMD_TBL_CREATE, EVENT_INVOKER_POST_CMD_TBL_CREATE,
                                  EVENT_INVOKER_CMD_TBL_LOADED, EVENT_INVOKER_PRE_PARSE_ARGS,
                                  EVENT_INVOKER_POST_PARSE_ARGS,
                                  EVENT_INVOKER_FILTER_RESULT)
        from azure.cli.core.commands.events import (
            EVENT_INVOKER_PRE_CMD_TBL_TRUNCATE, EVENT_INVOKER_PRE_LOAD_ARGUMENTS, EVENT_INVOKER_POST_LOAD_ARGUMENTS)

        # TODO: Can't simply be invoked as an event because args are transformed
        args = _pre_command_table_create(self.cli_ctx, args)

        self.cli_ctx.raise_event(EVENT_INVOKER_PRE_CMD_TBL_CREATE, args=args)
        self.commands_loader.load_command_table(args)
        self.cli_ctx.raise_event(EVENT_INVOKER_PRE_CMD_TBL_TRUNCATE,
                                 load_cmd_tbl_func=self.commands_loader.load_command_table, args=args)
        command = self._rudimentary_get_command(args)
        self.cli_ctx.invocation.data['command_string'] = command
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
        self.cli_ctx.raise_event(EVENT_INVOKER_PRE_LOAD_ARGUMENTS, commands_loader=self.commands_loader)
        self.commands_loader.load_arguments(command)
        self.cli_ctx.raise_event(EVENT_INVOKER_POST_LOAD_ARGUMENTS, commands_loader=self.commands_loader)
        self.cli_ctx.raise_event(EVENT_INVOKER_POST_CMD_TBL_CREATE, commands_loader=self.commands_loader)
        self.parser.cli_ctx = self.cli_ctx
        self.parser.load_command_table(self.commands_loader)

        self.cli_ctx.raise_event(EVENT_INVOKER_CMD_TBL_LOADED, cmd_tbl=self.commands_loader.command_table,
                                 parser=self.parser)

        arg_check = [a for a in args if a not in
                     (CLILogging.DEBUG_FLAG, CLILogging.VERBOSE_FLAG, CLILogging.ONLY_SHOW_ERRORS_FLAG)]
        if not arg_check:
            self.parser.enable_autocomplete()
            subparser = self.parser.subparsers[tuple()]
            self.help.show_welcome(subparser)

            # TODO: No event in base with which to target
            telemetry.set_command_details('az')
            telemetry.set_success(summary='welcome')
            return CommandResultItem(None, exit_code=0)

        if args[0].lower() == 'help':
            args[0] = '--help'

        self.parser.enable_autocomplete()

        self.cli_ctx.raise_event(EVENT_INVOKER_PRE_PARSE_ARGS, args=args)
        parsed_args = self.parser.parse_args(args)
        self.cli_ctx.raise_event(EVENT_INVOKER_POST_PARSE_ARGS, command=parsed_args.command, args=parsed_args)

        # print local context warning
        if self.cli_ctx.local_context.is_on and command and command in self.commands_loader.command_table:
            local_context_args = []
            arguments = self.commands_loader.command_table[command].arguments
            specified_arguments = self.parser.subparser_map[command].specified_arguments \
                if command in self.parser.subparser_map else []
            for name, argument in arguments.items():
                default_value_source = argument.type.settings.get('default_value_source', None)
                dest_name = argument.type.settings.get('dest', None)
                options = argument.type.settings.get('options_list', None)
                if default_value_source == 'Local Context' and dest_name not in specified_arguments and options:
                    value = getattr(parsed_args, name)
                    local_context_args.append((options[0], value))
            if local_context_args:
                logger.warning('Parameter persistence is turned on. Its information is saved in working directory %s. '
                               'You can run `az config param-persist off` to turn it off.',
                               self.cli_ctx.local_context.effective_working_directory())
                args_str = []
                for name, value in local_context_args:
                    args_str.append('{}: {}'.format(name, value))
                logger.warning('Command argument values from persistent parameters: %s', ', '.join(args_str))

        # TODO: This fundamentally alters the way Knack.invocation works here. Cannot be customized
        # with an event. Would need to be customized via inheritance.

        cmd = parsed_args.func
        self.cli_ctx.data['command'] = parsed_args.command

        self.cli_ctx.data['safe_params'] = AzCliCommandInvoker._extract_parameter_names(args)

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
                                      self.cli_ctx.data['safe_params'],
                                      extension_name=extension_name, extension_version=extension_version)
        if extension_name:
            self.data['command_extension_name'] = extension_name
            self.cli_ctx.logging.log_cmd_metadata_extension_info(extension_name, extension_version)

        self.resolve_warnings(cmd, parsed_args)
        self.resolve_confirmation(cmd, parsed_args)

        jobs = []
        for expanded_arg in _explode_list_args(parsed_args):
            cmd_copy = copy.copy(cmd)
            cmd_copy.cli_ctx = copy.copy(cmd.cli_ctx)
            cmd_copy.cli_ctx.data = copy.deepcopy(cmd.cli_ctx.data)
            expanded_arg.cmd = expanded_arg._cmd = cmd_copy

            if hasattr(expanded_arg, '_subscription'):
                cmd_copy.cli_ctx.data['subscription_id'] = expanded_arg._subscription  # pylint: disable=protected-access

            self._validation(expanded_arg)
            jobs.append((expanded_arg, cmd_copy))

        ids = getattr(parsed_args, '_ids', None) or [None] * len(jobs)
        if self.cli_ctx.config.getboolean('core', 'disable_concurrent_ids', False) or len(ids) < 2:
            results, exceptions = self._run_jobs_serially(jobs, ids)
        else:
            results, exceptions = self._run_jobs_concurrently(jobs, ids)

        # handle exceptions
        if len(exceptions) == 1 and not results:
            ex, id_arg = exceptions[0]
            raise ex
        if exceptions:
            for exception, id_arg in exceptions:
                logger.warning('%s: "%s"', id_arg, str(exception))
            if not results:
                return CommandResultItem(None, exit_code=1, error=CLIError('Encountered more than one exception.'))
            logger.warning('Encountered more than one exception.')

        if results and len(results) == 1:
            results = results[0]

        event_data = {'result': results}
        self.cli_ctx.raise_event(EVENT_INVOKER_FILTER_RESULT, event_data=event_data)

        # save to local context if it is turned on after command executed successfully
        if self.cli_ctx.local_context.is_on and command and command in self.commands_loader.command_table and \
                command in self.parser.subparser_map and self.parser.subparser_map[command].specified_arguments:
            self.cli_ctx.save_local_context(parsed_args, self.commands_loader.command_table[command].arguments,
                                            self.parser.subparser_map[command].specified_arguments)

        return CommandResultItem(
            event_data['result'],
            table_transformer=self.commands_loader.command_table[parsed_args.command].table_transformer,
            is_query_active=self.data['query_active'])

    @staticmethod
    def _extract_parameter_names(args):
        # note: name start with more than 2 '-' will be treated as value e.g. certs in PEM format
        return [(p.split('=', 1)[0] if p.startswith('--') else p[:2]) for p in args if
                (p.startswith('-') and not p.startswith('---') and len(p) > 1)]

    def _run_job(self, expanded_arg, cmd_copy):
        params = self._filter_params(expanded_arg)
        try:
            result = cmd_copy(params)
            if cmd_copy.supports_no_wait and getattr(expanded_arg, 'no_wait', False):
                result = None
            elif cmd_copy.no_wait_param and getattr(expanded_arg, cmd_copy.no_wait_param, False):
                result = None

            transform_op = cmd_copy.command_kwargs.get('transform', None)
            if transform_op:
                result = transform_op(result)

            if _is_poller(result):
                result = LongRunningOperation(cmd_copy.cli_ctx, 'Starting {}'.format(cmd_copy.name))(result)
            elif _is_paged(result):
                result = list(result)

            result = todict(result, AzCliCommandInvoker.remove_additional_prop_layer)
            event_data = {'result': result}
            cmd_copy.cli_ctx.raise_event(EVENT_INVOKER_TRANSFORM_RESULT, event_data=event_data)
            return event_data['result']
        except Exception as ex:  # pylint: disable=broad-except
            if cmd_copy.exception_handler:
                return cmd_copy.exception_handler(ex)
            raise

    def _run_jobs_serially(self, jobs, ids):
        results, exceptions = [], []
        for job, id_arg in zip(jobs, ids):
            expanded_arg, cmd_copy = job
            try:
                results.append(self._run_job(expanded_arg, cmd_copy))
            except(Exception, SystemExit) as ex:  # pylint: disable=broad-except
                exceptions.append((ex, id_arg))
        return results, exceptions

    def _run_jobs_concurrently(self, jobs, ids):
        from concurrent.futures import ThreadPoolExecutor, as_completed
        tasks, results, exceptions = [], [], []
        with ThreadPoolExecutor(max_workers=10) as executor:
            for expanded_arg, cmd_copy in jobs:
                tasks.append(executor.submit(self._run_job, expanded_arg, cmd_copy))
            for index, task in enumerate(as_completed(tasks)):
                try:
                    results.append(task.result())
                except (Exception, SystemExit) as ex:  # pylint: disable=broad-except
                    exceptions.append((ex, ids[index]))
        return results, exceptions

    def resolve_warnings(self, cmd, parsed_args):
        self._resolve_preview_and_deprecation_warnings(cmd, parsed_args)
        self._resolve_extension_override_warning(cmd)

    def _resolve_preview_and_deprecation_warnings(self, cmd, parsed_args):
        deprecations = [] + getattr(parsed_args, '_argument_deprecations', [])
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
            deprecations.append(ImplicitDeprecated(cli_ctx=self.cli_ctx, **deprecate_kwargs))

        previews = [] + getattr(parsed_args, '_argument_previews', [])
        if cmd.preview_info:
            previews.append(cmd.preview_info)
        else:
            # search for implicit command preview status
            path_comps = cmd.name.split()[:-1]
            implicit_preview_info = None
            while path_comps and not implicit_preview_info:
                implicit_preview_info = resolve_preview_info(self.cli_ctx, ' '.join(path_comps))
                del path_comps[-1]

            if implicit_preview_info:
                preview_kwargs = implicit_preview_info.__dict__.copy()
                preview_kwargs['object_type'] = 'command'
                del preview_kwargs['_get_tag']
                del preview_kwargs['_get_message']
                previews.append(ImplicitPreviewItem(cli_ctx=self.cli_ctx, **preview_kwargs))

        experimentals = [] + getattr(parsed_args, '_argument_experimentals', [])
        if cmd.experimental_info:
            experimentals.append(cmd.experimental_info)
        else:
            # search for implicit command experimental status
            path_comps = cmd.name.split()[:-1]
            implicit_experimental_info = None
            while path_comps and not implicit_experimental_info:
                implicit_experimental_info = resolve_experimental_info(self.cli_ctx, ' '.join(path_comps))
                del path_comps[-1]

            if implicit_experimental_info:
                experimental_kwargs = implicit_experimental_info.__dict__.copy()
                experimental_kwargs['object_type'] = 'command'
                del experimental_kwargs['_get_tag']
                del experimental_kwargs['_get_message']
                experimentals.append(ImplicitExperimentalItem(cli_ctx=self.cli_ctx, **experimental_kwargs))

        if not self.cli_ctx.only_show_errors:
            for d in deprecations:
                print(d.message, file=sys.stderr)
            for p in previews:
                print(p.message, file=sys.stderr)
            for e in experimentals:
                print(e.message, file=sys.stderr)

    def _resolve_extension_override_warning(self, cmd):  # pylint: disable=no-self-use
        if isinstance(cmd.command_source, ExtensionCommandSource) and cmd.command_source.overrides_command:
            logger.warning(cmd.command_source.get_command_warn_msg())

    def resolve_confirmation(self, cmd, parsed_args):
        confirm = cmd.confirmation and not parsed_args.__dict__.pop('yes', None) \
            and not cmd.cli_ctx.config.getboolean('core', 'disable_confirm_prompt', fallback=False)

        parsed_args = self._filter_params(parsed_args)
        if confirm and not cmd._user_confirmed(cmd.confirmation, parsed_args):  # pylint: disable=protected-access
            from knack.events import EVENT_COMMAND_CANCELLED
            cmd.cli_ctx.raise_event(EVENT_COMMAND_CANCELLED, command=cmd.name, command_args=parsed_args)
            raise CLIError('Operation cancelled.')

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
        # Follow EAFP to flatten `additional_properties` auto-generated by SDK
        # See https://docs.python.org/3/glossary.html#term-eafp
        try:
            if 'additionalProperties' in converted_dic and isinstance(obj.additional_properties, dict):
                converted_dic.update(converted_dic.pop('additionalProperties'))
        except AttributeError:
            pass
        return converted_dic

    def _validate_cmd_level(self, ns, cmd_validator):  # pylint: disable=no-self-use
        if cmd_validator:
            cmd_validator(**self._build_kwargs(cmd_validator, ns))
        try:
            delattr(ns, '_command_validator')
        except AttributeError:
            pass

    def _validate_arg_level(self, ns, **_):  # pylint: disable=no-self-use
        from azure.cli.core.azclierror import AzCLIError
        for validator in getattr(ns, '_argument_validators', []):
            try:
                validator(**self._build_kwargs(validator, ns))
            except AzCLIError:
                raise
            except Exception as ex:
                # Delay the import and mimic an exception handler
                from msrest.exceptions import ValidationError
                if isinstance(ex, ValidationError):
                    logger.debug('Validation error in %s.', str(validator))
                raise
        try:
            delattr(ns, '_argument_validators')
        except AttributeError:
            pass


class LongRunningOperation:  # pylint: disable=too-few-public-methods
    def __init__(self, cli_ctx, start_msg='', finish_msg='', poller_done_interval_ms=500.0,
                 progress_bar=None):

        self.cli_ctx = cli_ctx
        self.start_msg = start_msg
        self.finish_msg = finish_msg
        self.poller_done_interval_ms = poller_done_interval_ms
        self.deploy_dict = {}
        self.last_progress_report = datetime.datetime.now()

        self.progress_bar = None
        disable_progress_bar = self.cli_ctx.config.getboolean('core', 'disable_progress_bar', False)
        if not disable_progress_bar and not cli_ctx.only_show_errors:
            self.progress_bar = progress_bar if progress_bar is not None else IndeterminateProgressBar(cli_ctx)

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

    def __call__(self, poller):  # pylint: disable=too-many-statements
        from msrest.exceptions import ClientException
        from azure.core.exceptions import HttpResponseError

        correlation_message = ''
        if self.progress_bar:
            self.progress_bar.begin()
        correlation_id = None

        cli_logger = get_logger()  # get CLI logger which has the level set through command lines
        is_verbose = any(handler.level <= logs.INFO for handler in cli_logger.handlers)

        telemetry.poll_start()
        poll_flag = False
        while not poller.done():
            poll_flag = True

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
                if self.progress_bar:
                    self.progress_bar.update_progress()
                self._delay()
            except KeyboardInterrupt:
                if self.progress_bar:
                    self.progress_bar.stop()
                logger.error('Long-running operation wait cancelled.  %s', correlation_message)
                raise

        try:
            result = poller.result()
        except (ClientException, HttpResponseError) as exception:
            from azure.cli.core.commands.arm import handle_long_running_operation_exception
            if self.progress_bar:
                self.progress_bar.stop()
            if getattr(exception, 'status_code', None) == 404 and \
               ('delete' in self.cli_ctx.data['command'] or 'purge' in self.cli_ctx.data['command']):
                logger.debug('Service returned 404 on the long-running delete or purge operation. CLI treats it as '
                             'delete or purge successfully but service should fix this behavior.')
                return None
            if isinstance(exception, ClientException):
                handle_long_running_operation_exception(exception)
            else:
                raise exception
        finally:
            if self.progress_bar:
                self.progress_bar.end()
            if poll_flag:
                telemetry.poll_end()

        return result


# pylint: disable=too-few-public-methods
class DeploymentOutputLongRunningOperation(LongRunningOperation):
    def __call__(self, result):
        from msrest.pipeline import ClientRawResponse

        if isinstance(result, poller_classes()):
            # most deployment operations return a poller
            result = super(DeploymentOutputLongRunningOperation, self).__call__(result)
            outputs = None
            try:
                if isinstance(result, str) and result:
                    try:
                        obj = json.loads(result)
                        return obj
                    except json.decoder.JSONDecodeError:
                        logger.info("Fail to transform result \"%s\" to dictionary", result)
                else:
                    outputs = result.properties.outputs
            except AttributeError:  # super.__call__ might return a ClientRawResponse
                pass
            return {key: val['value'] for key, val in outputs.items()} if outputs else {}
        if isinstance(result, ClientRawResponse):
            # --no-wait returns a ClientRawResponse
            return {}
        # --validate returns a 'normal' response
        return result


def _load_command_loader(loader, args, name, prefix):
    module = import_module(prefix + name)
    loader_cls = getattr(module, 'COMMAND_LOADER_CLS', None)
    if not loader_cls:
        try:
            get_command_loader = getattr(module, 'get_command_loader', None)
            loader_cls = get_command_loader(loader.cli_ctx)
        except (ImportError, AttributeError, TypeError):
            logger.debug("Module '%s' is missing `get_command_loader` entry.", name)

    command_table = {}

    if loader_cls:
        command_loader = loader_cls(cli_ctx=loader.cli_ctx)
        loader.loaders.append(command_loader)  # This will be used by interactive
        if command_loader.supported_resource_type():
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


class ExtensionCommandSource:
    """ Class for commands contributed by an extension """

    def __init__(self, overrides_command=False, extension_name=None, preview=False, experimental=False):
        super(ExtensionCommandSource, self).__init__()
        # True if the command overrides a CLI command
        self.overrides_command = overrides_command
        self.extension_name = extension_name
        self.preview = preview
        self.experimental = experimental

    def get_command_warn_msg(self):
        if self.overrides_command:
            if self.extension_name:
                return "The behavior of this command has been altered by the following extension: " \
                       "{}".format(self.extension_name)
            return "The behavior of this command has been altered by an extension."
        if self.extension_name:
            return "This command is from the following extension: {}".format(self.extension_name)
        return "This command is from an extension."

    def get_preview_warn_msg(self):
        if self.preview:
            return "The extension is in preview"
        return None

    def get_experimental_warn_msg(self):
        if self.experimental:
            return "The extension is experimental and not covered by customer support. " \
                   "Please use with discretion."
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


# pylint: disable=no-member
def _is_paged(obj):
    # Since loading msrest is expensive, we avoid it until we have to
    from collections.abc import Iterable
    if isinstance(obj, Iterable) \
            and not isinstance(obj, list) \
            and not isinstance(obj, dict):
        from msrest.paging import Paged
        from azure.core.paging import ItemPaged as AzureCorePaged
        from azure.cli.core.aaz._paging import AAZPaged
        return isinstance(obj, (AzureCorePaged, Paged, AAZPaged))
    return False


def _is_poller(obj):
    # Since loading msrest is expensive, we avoid it until we have to
    if obj.__class__.__name__ in ['AzureOperationPoller', 'LROPoller', 'AAZLROPoller']:
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
class CliCommandType:

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
        """
        :param command_loader: The command loader that commands will be registered into
        :type command_loader: azure.cli.core.AzCommandsLoader
        :param group_name: The name of the group of commands in the command hierarchy
        :type group_name: str
        """
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
        from .command_operation import CommandOperation

        self._check_stale()
        merged_kwargs = self._flatten_kwargs(kwargs, get_command_type_kwarg(custom_command))
        self._apply_tags(merged_kwargs, kwargs, name)

        operations_tmpl = merged_kwargs['operations_tmpl']
        op_path = operations_tmpl.format(method_name)

        command_name = '{} {}'.format(self.group_name, name) if self.group_name else name
        command_operation = CommandOperation(
            command_loader=self.command_loader,
            op_path=op_path,
            **merged_kwargs
        )
        self.command_loader.add_cli_command(command_name,
                                            command_operation=command_operation,
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
        from azure.cli.core.commands.command_operation import GenericUpdateCommandOperation
        self._check_stale()
        merged_kwargs = self._flatten_kwargs(kwargs, get_command_type_kwarg())
        merged_kwargs_custom = self._flatten_kwargs(kwargs, get_command_type_kwarg(custom_command=True))
        self._apply_tags(merged_kwargs, kwargs, name)

        getter_op_path = self._resolve_operation(merged_kwargs, getter_name, getter_type)
        setter_op_path = self._resolve_operation(merged_kwargs, setter_name, setter_type)
        custom_function_op_path = self._resolve_operation(merged_kwargs_custom, custom_func_name, custom_func_type,
                                                          custom_command=True) if custom_func_name else None
        command_name = '{} {}'.format(self.group_name, name) if self.group_name else name
        command_operation = GenericUpdateCommandOperation(
            command_loader=self.command_loader,
            getter_op_path=getter_op_path,
            setter_op_path=setter_op_path,
            setter_arg_name=setter_arg_name,
            custom_function_op_path=custom_function_op_path,
            child_collection_prop_name=child_collection_prop_name,
            child_collection_key=child_collection_key,
            child_arg_name=child_arg_name,
            **merged_kwargs
        )
        self.command_loader.add_cli_command(command_name,
                                            command_operation=command_operation,
                                            **merged_kwargs)

    def wait_command(self, name, getter_name='get', **kwargs):
        self._wait_command(name, getter_name=getter_name, custom_command=False, **kwargs)

    def custom_wait_command(self, name, getter_name='get', **kwargs):
        self._wait_command(name, getter_name=getter_name, custom_command=True, **kwargs)

    def generic_wait_command(self, name, getter_name='get', getter_type=None, **kwargs):
        self._wait_command(name, getter_name=getter_name, getter_type=getter_type, **kwargs)

    def _wait_command(self, name, getter_name='get', getter_type=None, custom_command=False, **kwargs):
        from azure.cli.core.commands.command_operation import WaitCommandOperation
        self._check_stale()
        merged_kwargs = self._flatten_kwargs(kwargs, get_command_type_kwarg(custom_command))
        self._apply_tags(merged_kwargs, kwargs, name)

        if getter_type:
            merged_kwargs = _merge_kwargs(getter_type.settings, merged_kwargs, CLI_COMMAND_KWARGS)
        getter_op_path = self._resolve_operation(merged_kwargs, getter_name, getter_type, custom_command=custom_command)

        command_name = '{} {}'.format(self.group_name, name) if self.group_name else name
        command_operation = WaitCommandOperation(
            command_loader=self.command_loader,
            op_path=getter_op_path,
            **merged_kwargs
        )
        self.command_loader.add_cli_command(command_name,
                                            command_operation=command_operation,
                                            **merged_kwargs)

    def show_command(self, name, getter_name='get', **kwargs):
        self._show_command(name, getter_name=getter_name, custom_command=False, **kwargs)

    def custom_show_command(self, name, getter_name='get', **kwargs):
        self._show_command(name, getter_name=getter_name, custom_command=True, **kwargs)

    def _show_command(self, name, getter_name='get', getter_type=None, custom_command=False, **kwargs):
        from azure.cli.core.commands.command_operation import ShowCommandOperation
        self._check_stale()
        merged_kwargs = self._flatten_kwargs(kwargs, get_command_type_kwarg(custom_command))
        self._apply_tags(merged_kwargs, kwargs, name)

        if getter_type:
            merged_kwargs = _merge_kwargs(getter_type.settings, merged_kwargs, CLI_COMMAND_KWARGS)
        op_path = self._resolve_operation(merged_kwargs, getter_name, getter_type, custom_command=custom_command)

        command_name = '{} {}'.format(self.group_name, name) if self.group_name else name
        command_operation = ShowCommandOperation(
            command_loader=self.command_loader,
            op_path=op_path,
            **merged_kwargs
        )
        self.command_loader.add_cli_command(command_name,
                                            command_operation=command_operation,
                                            **merged_kwargs)

    def _apply_tags(self, merged_kwargs, kwargs, command_name):
        # don't inherit deprecation or preview info from command group
        merged_kwargs['deprecate_info'] = kwargs.get('deprecate_info', None)

        # transform is_preview and is_experimental to StatusTags
        merged_kwargs['preview_info'] = None
        merged_kwargs['experimental_info'] = None
        is_preview = kwargs.get('is_preview', False)
        is_experimental = kwargs.get('is_experimental', False)
        if is_preview and is_experimental:
            raise CLIError(PREVIEW_EXPERIMENTAL_CONFLICT_ERROR.format("command", self.group_name + " " + command_name))
        if is_preview:
            merged_kwargs['preview_info'] = PreviewItem(self.command_loader.cli_ctx, object_type='command')
        if is_experimental:
            merged_kwargs['experimental_info'] = ExperimentalItem(self.command_loader.cli_ctx, object_type='command')


def register_cache_arguments(cli_ctx):
    from knack import events

    cache_dest = '_cache'

    def add_cache_arguments(_, **kwargs):  # pylint: disable=unused-argument

        command_table = kwargs.get('commands_loader').command_table

        if not command_table:
            return

        class CacheAction(argparse.Action):  # pylint:disable=too-few-public-methods

            def __call__(self, parser, namespace, values, option_string=None):
                setattr(namespace, cache_dest, True)
                # save caching status to CLI context
                cmd = getattr(namespace, 'cmd', None) or getattr(namespace, '_cmd', None)
                cmd.cli_ctx.data[cache_dest] = True

        for command in command_table.values():
            supports_local_cache = command.command_kwargs.get('supports_local_cache')
            if supports_local_cache:
                command.arguments[cache_dest] = CLICommandArgument(
                    '_cache',
                    options_list='--defer',
                    nargs='?',
                    action=CacheAction,
                    help='Temporarily store the object in the local cache instead of sending to Azure. '
                         'Use `az cache` commands to view/clear.',
                    is_preview=True
                )

    cli_ctx.register_event(events.EVENT_INVOKER_POST_CMD_TBL_CREATE, add_cache_arguments)
