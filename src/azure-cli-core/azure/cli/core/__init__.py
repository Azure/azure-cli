# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

__version__ = "2.0.11+dev"

import configparser
import os
import sys

from knack.cli import CLI
from knack.commands import CLICommandsLoader, CLICommand
from knack.completion import ARGCOMPLETE_ENV_NAME
from knack.introspection import extract_args_from_signature, extract_full_summary_from_signature
from knack.invocation import CommandInvoker
from knack.log import get_logger
import six

logger = get_logger(__name__)


def _pre_command_table_create(ctx, args):

    def _load_file(path):
        from azure.cli.core.util import read_file_content
        if path == '-':
            content = sys.stdin.read()
        else:
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

    def _expand_file_prefixed_files(args):
        return list([_expand_file_prefix(arg) for arg in args])

    ctx.refresh_request_id()
    return _expand_file_prefixed_files(args)


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


def _validate_arguments(args, **_):
    for validator in getattr(args, '_validators', []):
        validator(args)
    try:
        delattr(args, '_validators')
    except AttributeError:
        pass


class AzCli(CLI):

    def __init__(self, **kwargs):
        super(AzCli, self).__init__(**kwargs)

        from azure.cli.core.commands.arm import add_id_parameters
        from azure.cli.core.cloud import get_active_cloud
        import azure.cli.core.commands.progress as progress
        from azure.cli.core.extensions import register_extensions
        from azure.cli.core._profile import Profile
        from azure.cli.core._session import ACCOUNT, CONFIG, SESSION

        import knack.events as events

        self.data['headers'] = {}
        self.data['command'] = 'unknown'
        self.data['completer_active'] = ARGCOMPLETE_ENV_NAME in os.environ
        self.data['query_active'] = False

        azure_folder = self.config.config_dir
        ACCOUNT.load(os.path.join(azure_folder, 'azureProfile.json'))
        CONFIG.load(os.path.join(azure_folder, 'az.json'))
        SESSION.load(os.path.join(azure_folder, 'az.sess'), max_age=3600)
        self.cloud = get_active_cloud(self)
        logger.debug('Current cloud config:\n%s', str(self.cloud.name))

        self.progress_controller = progress.ProgressHook()

        register_extensions(self)
        self.register_event(events.EVENT_INVOKER_POST_CMD_TBL_CREATE, add_id_parameters)
        # TODO: Doesn't work because args get copied
        # self.register_event(events.EVENT_INVOKER_PRE_CMD_TBL_CREATE, _pre_command_table_create)

    def refresh_request_id(self):
        """Assign a new random GUID as x-ms-client-request-id

        The method must be invoked before each command execution in order to ensure
        unique client-side request ID is generated.
        """
        import uuid
        self.data['headers']['x-ms-client-request-id'] = str(uuid.uuid1())

    def get_progress_controller(self, det=False):
        import azure.cli.core.commands.progress as progress
        self.progress_controller.init_progress(progress.get_progress_view(det))
        return self.progress_controller

    def get_cli_version(cli):
        from azure.cli.core.util import get_az_version_string
        return get_az_version_string(cli.output)


class AzCliCommand(CLICommand):

    def _resolve_default_value_from_cfg_file(self, arg, overrides):
        from azure.cli.core._config import DEFAULTS_SECTION

        if not hasattr(arg.type, 'required_tooling'):
            required = arg.type.settings.get('required', False)
            setattr(arg.type, 'required_tooling', required)
        if 'configured_default' in overrides.settings:
            def_config = overrides.settings.pop('configured_default', None)
            setattr(arg.type, 'default_name_tooling', def_config)
            # same blunt mechanism like we handled id-parts, for create command, no name default
            if (self.name.split()[-1] == 'create' and overrides.settings.get('metavar', None) == 'NAME'):
                return
            setattr(arg.type, 'configured_default_applied', True)
            config_value = self.ctx.config.get(DEFAULTS_SECTION, def_config, None)
            if config_value:
                logger.warning("Using default '%s' for arg %s", config_value, arg.name)
                overrides.settings['default'] = config_value
                overrides.settings['required'] = False


    def update_argument(self, param_name, argtype):
        arg = self.arguments[param_name]
        self._resolve_default_value_from_cfg_file(arg, argtype)
        arg.type.update(other=argtype)


class MainCommandsLoader(CLICommandsLoader):

    def __init__(self, ctx=None):
        import knack.events as events
        super(MainCommandsLoader, self).__init__(ctx)
        self.loaders = []

    def load_command_table(self, args):
        from azure.cli.core.commands import get_command_table
        self.command_table = get_command_table(self, args)
        return self.command_table

    def load_arguments(self, command):
        from azure.cli.core.commands.parameters import resource_group_name_type, location_type, deployment_name_type
        from knack.arguments import ignore_type

        for loader in self.loaders:
            loader.load_arguments(command)
            self.argument_registry.arguments.update(loader.argument_registry.arguments)

        self.register_cli_argument('', 'resource_group_name', resource_group_name_type)
        self.register_cli_argument('', 'location', location_type)
        self.register_cli_argument('', 'deployment_name', deployment_name_type)
        self.register_cli_argument('', 'cli_ctx', ignore_type, default=self.ctx)
        super(MainCommandsLoader, self).load_arguments(command)


class AzCommandsLoader(CLICommandsLoader):

    def __init__(self, ctx=None):
        super(AzCommandsLoader, self).__init__(ctx=ctx)
        self.command_module_map = {}

    def cli_generic_update_command(self, *args, **kwargs):
        from azure.cli.core.commands.arm import cli_generic_update_command as command
        return command(self, *args, **kwargs)

    def cli_generic_wait_command(self, *args, **kwargs):
        from azure.cli.core.commands.arm import cli_generic_wait_command as command
        return command(self, *args, **kwargs)

    # TODO: should not have to duplicate this logic just to use a derived CLICommand class
    def create_command(self, module_name, name, operation, **kwargs):  # pylint: disable=unused-argument
        if not isinstance(operation, six.string_types):
            raise ValueError("Operation must be a string. Got '{}'".format(operation))

        name = ' '.join(name.split())

        confirmation = kwargs.get('confirmation', False)
        client_factory = kwargs.get('client_factory', None)

        def _command_handler(command_args):
            from knack.events import EVENT_COMMAND_CANCELLED
            from knack.util import CLIError

            from azure.cli.core.commands import _is_poller, _is_paged, LongRunningOperation

            if confirmation \
                and not command_args.get('_confirm_yes') \
                and not self.ctx.config.getboolean('core', 'disable_confirm_prompt', fallback=False) \
                    and not CLICommandsLoader.user_confirmed(confirmation, command_args):
                self.ctx.raise_event(EVENT_COMMAND_CANCELLED, command=name, command_args=command_args)
                raise CLIError('Operation cancelled.')
            op = self.get_op_handler(operation)
            client = client_factory(self.ctx, command_args) if client_factory else None
            for _ in range(2):  # for possible retry, we do maximum 2 times
                try:
                    result = op(client, **command_args) if client else op(**command_args)
                    no_wait_param = kwargs.get('no_wait_param', None)
                    if no_wait_param and command_args.get(no_wait_param, None):
                        return None  # return None for 'no-wait'

                    if _is_poller(result):
                        return LongRunningOperation(self.ctx, 'Starting {}'.format(name))(result)
                    elif _is_paged(result):
                        return list(result)
                    return result
                except Exception as ex:  # pylint: disable=broad-except
                    from azure.cli.core.commands import _check_rp_not_registered_err, _register_rp
                    rp = _check_rp_not_registered_err(ex)
                    exception_handler = kwargs.get('exception_handler', None)
                    if rp:
                        _register_rp(rp)
                        continue  # retry
                    if exception_handler:
                        exception_handler(ex)
                        return
                    else:
                        six.reraise(*sys.exc_info())

        def arguments_loader():
            return extract_args_from_signature(self.get_op_handler(operation), kwargs.get('no_wait_param', None))

        def description_loader():
            return extract_full_summary_from_signature(self.get_op_handler(operation))

        kwargs['arguments_loader'] = arguments_loader
        kwargs['description_loader'] = description_loader

        cmd = AzCliCommand(self.ctx, name, _command_handler, **kwargs)
        if confirmation:
            cmd.add_argument('yes', '--yes', '-y', dest='_confirm_yes', action='store_true',
                             help='Do not prompt for confirmation')
        return cmd

    def get_op_handler(self, operation):
        """ Import and load the operation handler """
        # Patch the unversioned sdk path to include the appropriate API version for the
        # resource type in question.
        from azure.cli.core.profiles import ResourceType
        from azure.cli.core.profiles._shared import get_versioned_sdk_path
        import types

        profile = self.ctx.cloud.profile
        for rt in ResourceType:
            if operation.startswith(rt.import_prefix):
                operation = operation.replace(rt.import_prefix,
                                              get_versioned_sdk_path(profile, rt))

        return CLICommandsLoader.get_op_handler(operation)


# TODO: Shouldn't have to monkey patch the implementation to make this work... Knack issue #15
def az_command_invoker_execute(self, argv):
    import azure.cli.core.telemetry as telemetry
    import knack.events as events
    from knack.util import CommandResultItem, todict, CLIError
    from msrest.paging import Paged


    # TODO: Can't simply be invoked as an event because args are transformed
    args = _pre_command_table_create(self.ctx, argv)

    self.ctx.raise_event(events.EVENT_INVOKER_PRE_CMD_TBL_CREATE, args=args)
    cmd_tbl = self.commands_loader.load_command_table(args)
    command = self._rudimentary_get_command(args)
    self.commands_loader.load_arguments(command)
    cmd_tbl = {command: self.commands_loader.command_table[command]} if command else cmd_tbl
    self.ctx.raise_event(events.EVENT_INVOKER_POST_CMD_TBL_CREATE, cmd_tbl=cmd_tbl)
    self.parser.load_command_table(cmd_tbl)
    self.ctx.raise_event(events.EVENT_INVOKER_CMD_TBL_LOADED, cmd_tbl=cmd_tbl, parser=self.parser)

    if not args:
        self.ctx.completion.enable_autocomplete(self.parser)
        subparser = self.parser.subparsers[tuple()]
        self.help.show_welcome(subparser)

        # TODO: No event in base with which to target
        telemetry.set_command_details('az')
        telemetry.set_success(summary='welcome')
        return None

    if args[0].lower() == 'help':
        args[0] = '--help'

    self.ctx.completion.enable_autocomplete(self.parser)

    self.ctx.raise_event(events.EVENT_INVOKER_PRE_PARSE_ARGS, args=args)
    parsed_args = self.parser.parse_args(args)
    self.ctx.raise_event(events.EVENT_INVOKER_POST_PARSE_ARGS, command=parsed_args.command, args=parsed_args)


    # TODO: This fundamentally alters the way Knack.invocation works here. Cannot be customized
    # with an event. Would need to be customized via inheritance.
    results = []
    for expanded_arg in _explode_list_args(parsed_args):
        self.data['command'] = expanded_arg.command

        try:
            _validate_arguments(expanded_arg)
        except CLIError:
            raise
        except:  # pylint: disable=bare-except
            err = sys.exc_info()[1]
            getattr(expanded_arg, '_parser', self.parser).validation_error(str(err))


        params = self._filter_params(expanded_arg)

        telemetry.set_command_details(self.data['command'],
                                      self.data['output'],
                                      [p for p in argv if p.startswith('-')])

        result = expanded_arg.func(params)
        result = todict(list(result)) if isinstance(result, Paged) else todict(result)
        results.append(result)

    if len(results) == 1:
        results = results[0]    

    event_data = {'result': results}
    self.ctx.raise_event(events.EVENT_INVOKER_TRANSFORM_RESULT, event_data=event_data)
    self.ctx.raise_event(events.EVENT_INVOKER_FILTER_RESULT, event_data=event_data)

    return CommandResultItem(event_data['result'],
                             table_transformer=cmd_tbl[parsed_args.command].table_transformer,
                             is_query_active=self.data['query_active'])


CommandInvoker.execute = az_command_invoker_execute
