# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long

from __future__ import print_function

__version__ = "2.7.0"

import os
import sys
import timeit

import six

from knack.cli import CLI
from knack.commands import CLICommandsLoader
from knack.completion import ARGCOMPLETE_ENV_NAME
from knack.introspection import extract_args_from_signature, extract_full_summary_from_signature
from knack.log import get_logger
from knack.preview import PreviewItem
from knack.experimental import ExperimentalItem
from knack.util import CLIError
from knack.arguments import ArgumentsContext, CaseInsensitiveList  # pylint: disable=unused-import
from .local_context import AzCLILocalContext, LocalContextAction

logger = get_logger(__name__)

EXCLUDED_PARAMS = ['self', 'raw', 'polling', 'custom_headers', 'operation_config',
                   'content_version', 'kwargs', 'client', 'no_wait']
EVENT_FAILED_EXTENSION_LOAD = 'MainLoader.OnFailedExtensionLoad'


class AzCli(CLI):

    def __init__(self, **kwargs):
        super(AzCli, self).__init__(**kwargs)

        from azure.cli.core.commands import register_cache_arguments
        from azure.cli.core.commands.arm import (
            register_ids_argument, register_global_subscription_argument)
        from azure.cli.core.cloud import get_active_cloud
        from azure.cli.core.commands.transform import register_global_transforms
        from azure.cli.core._session import ACCOUNT, CONFIG, SESSION

        from knack.util import ensure_dir

        self.data['headers'] = {}
        self.data['command'] = 'unknown'
        self.data['command_extension_name'] = None
        self.data['completer_active'] = ARGCOMPLETE_ENV_NAME in os.environ
        self.data['query_active'] = False

        azure_folder = self.config.config_dir
        ensure_dir(azure_folder)
        ACCOUNT.load(os.path.join(azure_folder, 'azureProfile.json'))
        CONFIG.load(os.path.join(azure_folder, 'az.json'))
        SESSION.load(os.path.join(azure_folder, 'az.sess'), max_age=3600)
        self.cloud = get_active_cloud(self)
        logger.debug('Current cloud config:\n%s', str(self.cloud.name))
        self.local_context = AzCLILocalContext(self)
        register_global_transforms(self)
        register_global_subscription_argument(self)
        register_ids_argument(self)  # global subscription must be registered first!
        register_cache_arguments(self)

        self.progress_controller = None

    def refresh_request_id(self):
        """Assign a new random GUID as x-ms-client-request-id

        The method must be invoked before each command execution in order to ensure
        unique client-side request ID is generated.
        """
        import uuid
        self.data['headers']['x-ms-client-request-id'] = str(uuid.uuid1())

    def get_progress_controller(self, det=False):
        import azure.cli.core.commands.progress as progress
        if not self.progress_controller:
            self.progress_controller = progress.ProgressHook()

        self.progress_controller.init_progress(progress.get_progress_view(det))
        return self.progress_controller

    def get_cli_version(self):
        return __version__

    def show_version(self):
        from azure.cli.core.util import get_az_version_string, show_updates
        from azure.cli.core.commands.constants import (SURVEY_PROMPT, SURVEY_PROMPT_COLOR,
                                                       UX_SURVEY_PROMPT, UX_SURVEY_PROMPT_COLOR)

        ver_string, updates_available = get_az_version_string()
        print(ver_string)
        show_updates(updates_available)

        show_link = self.config.getboolean('output', 'show_survey_link', True)
        if show_link:
            print('\n' + (SURVEY_PROMPT_COLOR if self.enable_color else SURVEY_PROMPT))
            print(UX_SURVEY_PROMPT_COLOR if self.enable_color else UX_SURVEY_PROMPT)

    def exception_handler(self, ex):  # pylint: disable=no-self-use
        from azure.cli.core.util import handle_exception
        return handle_exception(ex)

    def save_local_context(self, parsed_args, argument_definitions, specified_arguments):
        """ Local Context Attribute arguments

        Save argument value to local context if it is defined as SET and user specify a value for it.

        :param parsed_args: Parsed args which return by AzCliCommandParser parse_args
        :type parsed_args: Namespace
        :param argument_definitions: All available argument definitions
        :type argument_definitions: dict
        :param specified_arguments: Arguments which user specify in this command
        :type specified_arguments: list
        """
        local_context_args = []
        for argument_name in specified_arguments:
            # make sure SET is defined
            if argument_name not in argument_definitions:
                continue
            argtype = argument_definitions[argument_name].type
            lca = argtype.settings.get('local_context_attribute', None)
            if not lca or not lca.actions or LocalContextAction.SET not in lca.actions:
                continue
            # get the specified value
            value = getattr(parsed_args, argument_name)
            # save when name and scopes have value
            if lca.name and lca.scopes:
                self.local_context.set(lca.scopes, lca.name, value)
            options = argtype.settings.get('options_list', None)
            if options:
                local_context_args.append((options[0], value))

        # print warning if there are values saved to local context
        if local_context_args:
            logger.warning('Local context is turned on. Its information is saved in working directory %s. You can '
                           'run `az local-context off` to turn it off.',
                           self.local_context.effective_working_directory())
            args_str = []
            for name, value in local_context_args:
                args_str.append('{}: {}'.format(name, value))
            logger.warning('Command argument values saved to local context: %s', ', '.join(args_str))


class MainCommandsLoader(CLICommandsLoader):

    def __init__(self, cli_ctx=None):
        super(MainCommandsLoader, self).__init__(cli_ctx)
        self.cmd_to_loader_map = {}
        self.loaders = []

    def _update_command_definitions(self):
        for cmd_name in self.command_table:
            loaders = self.cmd_to_loader_map[cmd_name]
            for loader in loaders:
                loader.command_table = self.command_table
                loader._update_command_definitions()  # pylint: disable=protected-access

    # pylint: disable=too-many-statements
    def load_command_table(self, args):
        from importlib import import_module
        import pkgutil
        import traceback
        from azure.cli.core.commands import (
            _load_module_command_loader, _load_extension_command_loader, BLACKLISTED_MODS, ExtensionCommandSource)
        from azure.cli.core.extension import (
            get_extensions, get_extension_path, get_extension_modname)

        def _update_command_table_from_modules(args):
            '''Loads command table(s)
            When `module_name` is specified, only commands from that module will be loaded.
            If the module is not found, all commands are loaded.
            '''
            installed_command_modules = []
            try:
                mods_ns_pkg = import_module('azure.cli.command_modules')
                installed_command_modules = [modname for _, modname, _ in
                                             pkgutil.iter_modules(mods_ns_pkg.__path__)
                                             if modname not in BLACKLISTED_MODS]
            except ImportError as e:
                logger.warning(e)

            logger.debug('Installed command modules %s', installed_command_modules)
            cumulative_elapsed_time = 0
            for mod in [m for m in installed_command_modules if m not in BLACKLISTED_MODS]:
                try:
                    start_time = timeit.default_timer()
                    module_command_table, module_group_table = _load_module_command_loader(self, args, mod)
                    for cmd in module_command_table.values():
                        cmd.command_source = mod
                    self.command_table.update(module_command_table)
                    self.command_group_table.update(module_group_table)
                    elapsed_time = timeit.default_timer() - start_time
                    logger.debug("Loaded module '%s' in %.3f seconds.", mod, elapsed_time)
                    cumulative_elapsed_time += elapsed_time
                except Exception as ex:  # pylint: disable=broad-except
                    # Changing this error message requires updating CI script that checks for failed
                    # module loading.
                    import azure.cli.core.telemetry as telemetry
                    logger.error("Error loading command module '%s': %s", mod, ex)
                    telemetry.set_exception(exception=ex, fault_type='module-load-error-' + mod,
                                            summary='Error loading module: {}'.format(mod))
                    logger.debug(traceback.format_exc())
            logger.debug("Loaded all modules in %.3f seconds. "
                         "(note: there's always an overhead with the first module loaded)",
                         cumulative_elapsed_time)

        def _update_command_table_from_extensions(ext_suppressions):

            from azure.cli.core.extension.operations import check_version_compatibility

            def _handle_extension_suppressions(extensions):
                filtered_extensions = []
                for ext in extensions:
                    should_include = True
                    for suppression in ext_suppressions:
                        if should_include and suppression.handle_suppress(ext):
                            should_include = False
                    if should_include:
                        filtered_extensions.append(ext)
                return filtered_extensions

            extensions = get_extensions()
            if extensions:
                logger.debug("Found %s extensions: %s", len(extensions), [e.name for e in extensions])
                allowed_extensions = _handle_extension_suppressions(extensions)
                module_commands = set(self.command_table.keys())
                for ext in allowed_extensions:
                    try:
                        check_version_compatibility(ext.get_metadata())
                    except CLIError as ex:
                        # issue warning and skip loading extensions that aren't compatible with the CLI core
                        logger.warning(ex)
                        continue
                    ext_name = ext.name
                    ext_dir = ext.path or get_extension_path(ext_name)
                    logger.debug("Extensions directory: '%s'", ext_dir)
                    sys.path.append(ext_dir)
                    try:
                        ext_mod = get_extension_modname(ext_name, ext_dir=ext_dir)
                        # Add to the map. This needs to happen before we load commands as registering a command
                        # from an extension requires this map to be up-to-date.
                        # self._mod_to_ext_map[ext_mod] = ext_name
                        start_time = timeit.default_timer()
                        extension_command_table, extension_group_table = \
                            _load_extension_command_loader(self, args, ext_mod)

                        for cmd_name, cmd in extension_command_table.items():
                            cmd.command_source = ExtensionCommandSource(
                                extension_name=ext_name,
                                overrides_command=cmd_name in module_commands,
                                preview=ext.preview,
                                experimental=ext.experimental)

                        self.command_table.update(extension_command_table)
                        self.command_group_table.update(extension_group_table)
                        elapsed_time = timeit.default_timer() - start_time
                        logger.debug("Loaded extension '%s' in %.3f seconds.", ext_name, elapsed_time)
                    except Exception as ex:  # pylint: disable=broad-except
                        self.cli_ctx.raise_event(EVENT_FAILED_EXTENSION_LOAD, extension_name=ext_name)
                        logger.warning("Unable to load extension '%s: %s'. Use --debug for more information.",
                                       ext_name, ex)
                        logger.debug(traceback.format_exc())

        def _wrap_suppress_extension_func(func, ext):
            """ Wrapper method to handle centralization of log messages for extension filters """
            res = func(ext)
            should_suppress = res
            reason = "Use --debug for more information."
            if isinstance(res, tuple):
                should_suppress, reason = res
            suppress_types = (bool, type(None))
            if not isinstance(should_suppress, suppress_types):
                raise ValueError("Command module authoring error: "
                                 "Valid extension suppression values are {} in {}".format(suppress_types, func))
            if should_suppress:
                logger.warning("Extension %s (%s) has been suppressed. %s",
                               ext.name, ext.version, reason)
                logger.debug("Extension %s (%s) suppressed from being loaded due "
                             "to %s", ext.name, ext.version, func)
            return should_suppress

        def _get_extension_suppressions(mod_loaders):
            res = []
            for m in mod_loaders:
                suppressions = getattr(m, 'suppress_extension', None)
                if suppressions:
                    suppressions = suppressions if isinstance(suppressions, list) else [suppressions]
                    for sup in suppressions:
                        if isinstance(sup, ModExtensionSuppress):
                            res.append(sup)
            return res

        _update_command_table_from_modules(args)
        try:
            ext_suppressions = _get_extension_suppressions(self.loaders)
            # We always load extensions even if the appropriate module has been loaded
            # as an extension could override the commands already loaded.
            _update_command_table_from_extensions(ext_suppressions)
        except Exception:  # pylint: disable=broad-except
            logger.warning("Unable to load extensions. Use --debug for more information.")
            logger.debug(traceback.format_exc())

        return self.command_table

    def load_arguments(self, command=None):
        from azure.cli.core.commands.parameters import (
            resource_group_name_type, get_location_type, deployment_name_type, vnet_name_type, subnet_name_type)
        from knack.arguments import ignore_type

        # omit specific command to load everything
        if command is None:
            command_loaders = set()
            for loaders in self.cmd_to_loader_map.values():
                command_loaders = command_loaders.union(set(loaders))
            logger.info('Applying %s command loaders...', len(command_loaders))
        else:
            command_loaders = self.cmd_to_loader_map.get(command, None)

        if command_loaders:
            for loader in command_loaders:

                # register global args
                with loader.argument_context('') as c:
                    c.argument('resource_group_name', resource_group_name_type)
                    c.argument('location', get_location_type(self.cli_ctx))
                    c.argument('vnet_name', vnet_name_type)
                    c.argument('subnet', subnet_name_type)
                    c.argument('deployment_name', deployment_name_type)
                    c.argument('cmd', ignore_type)

                if command is None:
                    # load all arguments via reflection
                    for cmd in loader.command_table.values():
                        cmd.load_arguments()  # this loads the arguments via reflection
                    loader.skip_applicability = True
                    loader.load_arguments('')  # this adds entries to the argument registries
                else:
                    loader.command_name = command
                    self.command_table[command].load_arguments()  # this loads the arguments via reflection
                    loader.load_arguments(command)  # this adds entries to the argument registries
                self.argument_registry.arguments.update(loader.argument_registry.arguments)
                self.extra_argument_registry.update(loader.extra_argument_registry)
                loader._update_command_definitions()  # pylint: disable=protected-access


class ModExtensionSuppress(object):  # pylint: disable=too-few-public-methods

    def __init__(self, mod_name, suppress_extension_name, suppress_up_to_version, reason=None, recommend_remove=False,
                 recommend_update=False):
        self.mod_name = mod_name
        self.suppress_extension_name = suppress_extension_name
        self.suppress_up_to_version = suppress_up_to_version
        self.reason = reason
        self.recommend_remove = recommend_remove
        self.recommend_update = recommend_update

    def handle_suppress(self, ext):
        from pkg_resources import parse_version
        should_suppress = ext.name == self.suppress_extension_name and ext.version and \
            parse_version(ext.version) <= parse_version(self.suppress_up_to_version)
        if should_suppress:
            reason = self.reason or "Use --debug for more information."
            logger.warning("Extension %s (%s) has been suppressed. %s",
                           ext.name, ext.version, reason)
            logger.debug("Extension %s (%s) suppressed from being loaded due "
                         "to %s", ext.name, ext.version, self.mod_name)
            if self.recommend_remove:
                logger.warning("Remove this extension with 'az extension remove --name %s'", ext.name)
            if self.recommend_update:
                logger.warning("Update this extension with 'az extension update --name %s'", ext.name)
        return should_suppress


class AzCommandsLoader(CLICommandsLoader):  # pylint: disable=too-many-instance-attributes

    def __init__(self, cli_ctx=None, command_group_cls=None, argument_context_cls=None,
                 suppress_extension=None, **kwargs):
        from azure.cli.core.commands import AzCliCommand, AzCommandGroup, AzArgumentContext

        super(AzCommandsLoader, self).__init__(cli_ctx=cli_ctx,
                                               command_cls=AzCliCommand,
                                               excluded_command_handler_args=EXCLUDED_PARAMS)
        self.suppress_extension = suppress_extension
        self.module_kwargs = kwargs
        self.command_name = None
        self.skip_applicability = False
        self._command_group_cls = command_group_cls or AzCommandGroup
        self._argument_context_cls = argument_context_cls or AzArgumentContext

    def _update_command_definitions(self):
        master_arg_registry = self.cli_ctx.invocation.commands_loader.argument_registry
        master_extra_arg_registry = self.cli_ctx.invocation.commands_loader.extra_argument_registry

        for command_name, command in self.command_table.items():
            # Add any arguments explicitly registered for this command
            for argument_name, argument_definition in master_extra_arg_registry[command_name].items():
                command.arguments[argument_name] = argument_definition

            for argument_name in command.arguments:
                overrides = master_arg_registry.get_cli_argument(command_name, argument_name)
                command.update_argument(argument_name, overrides)

    def _apply_doc_string(self, dest, command_kwargs):
        from azure.cli.core.profiles._shared import APIVersionException
        doc_string_source = command_kwargs.get('doc_string_source', None)
        if not doc_string_source:
            return
        if not isinstance(doc_string_source, str):
            raise CLIError("command authoring error: applying doc_string_source '{}' directly will cause slowdown. "
                           'Import by string name instead.'.format(doc_string_source.__name__))

        model = doc_string_source
        try:
            model = self.get_models(doc_string_source)
        except APIVersionException:
            model = None
        if not model:
            from importlib import import_module
            (path, model_name) = doc_string_source.split('#', 1)
            method_name = None
            if '.' in model_name:
                (model_name, method_name) = model_name.split('.', 1)
            module = import_module(path)
            model = getattr(module, model_name)
            if method_name:
                model = getattr(model, method_name, None)
        if not model:
            raise CLIError("command authoring error: source '{}' not found.".format(doc_string_source))
        dest.__doc__ = model.__doc__

    def _get_resource_type(self):
        resource_type = self.module_kwargs.get('resource_type', None)
        if not resource_type:
            command_type = self.module_kwargs.get('command_type', None)
            resource_type = command_type.settings.get('resource_type', None) if command_type else None
        return resource_type

    def get_api_version(self, resource_type=None, operation_group=None):
        from azure.cli.core.profiles import get_api_version
        resource_type = resource_type or self._get_resource_type()
        version = get_api_version(self.cli_ctx, resource_type)
        if isinstance(version, str):
            return version
        version = getattr(version, operation_group, None)
        if version:
            return version
        from azure.cli.core.profiles._shared import APIVersionException
        raise APIVersionException(operation_group, self.cli_ctx.cloud.profile)

    def supported_api_version(self, resource_type=None, min_api=None, max_api=None, operation_group=None):
        from azure.cli.core.profiles import supported_api_version
        if not min_api and not max_api:
            # optimistically assume that fully supported if no api restriction listed
            return True
        api_support = supported_api_version(
            cli_ctx=self.cli_ctx,
            resource_type=resource_type or self._get_resource_type(),
            min_api=min_api,
            max_api=max_api,
            operation_group=operation_group)
        if isinstance(api_support, bool):
            return api_support
        if operation_group:
            return getattr(api_support, operation_group)
        return api_support

    def supported_resource_type(self, resource_type=None):
        from azure.cli.core.profiles import supported_resource_type
        return supported_resource_type(
            cli_ctx=self.cli_ctx,
            resource_type=resource_type or self._get_resource_type())

    def get_sdk(self, *attr_args, **kwargs):
        from azure.cli.core.profiles import get_sdk
        return get_sdk(self.cli_ctx, kwargs.pop('resource_type', self._get_resource_type()),
                       *attr_args, **kwargs)

    def get_models(self, *attr_args, **kwargs):
        from azure.cli.core.profiles import get_sdk
        resource_type = kwargs.get('resource_type', self._get_resource_type())
        operation_group = kwargs.get('operation_group', self.module_kwargs.get('operation_group', None))
        return get_sdk(self.cli_ctx, resource_type, *attr_args, mod='models', operation_group=operation_group)

    def command_group(self, group_name, command_type=None, **kwargs):
        if command_type:
            kwargs['command_type'] = command_type
        if 'deprecate_info' in kwargs:
            kwargs['deprecate_info'].target = group_name
        if kwargs.get('is_preview', False):
            kwargs['preview_info'] = PreviewItem(
                cli_ctx=self.cli_ctx,
                target=group_name,
                object_type='command group'
            )
        if kwargs.get('is_experimental', False):
            kwargs['experimental_info'] = ExperimentalItem(
                cli_ctx=self.cli_ctx,
                target=group_name,
                object_type='command group'
            )
        return self._command_group_cls(self, group_name, **kwargs)

    def argument_context(self, scope, **kwargs):
        return self._argument_context_cls(self, scope, **kwargs)

    def _cli_command(self, name, operation=None, handler=None, argument_loader=None, description_loader=None, **kwargs):

        from knack.deprecation import Deprecated

        kwargs['deprecate_info'] = Deprecated.ensure_new_style_deprecation(self.cli_ctx, kwargs, 'command')

        if operation and not isinstance(operation, six.string_types):
            raise TypeError("Operation must be a string. Got '{}'".format(operation))
        if handler and not callable(handler):
            raise TypeError("Handler must be a callable. Got '{}'".format(operation))
        if bool(operation) == bool(handler):
            raise TypeError("Must specify exactly one of either 'operation' or 'handler'")

        name = ' '.join(name.split())

        client_factory = kwargs.get('client_factory', None)

        def default_command_handler(command_args):
            from azure.cli.core.util import get_arg_list, augment_no_wait_handler_args
            from azure.cli.core.commands.client_factory import resolve_client_arg_name

            op = handler or self.get_op_handler(operation, operation_group=kwargs.get('operation_group'))
            op_args = get_arg_list(op)
            cmd = command_args.get('cmd') if 'cmd' in op_args else command_args.pop('cmd')

            client = client_factory(cmd.cli_ctx, command_args) if client_factory else None
            supports_no_wait = kwargs.get('supports_no_wait', None)
            if supports_no_wait:
                no_wait_enabled = command_args.pop('no_wait', False)
                augment_no_wait_handler_args(no_wait_enabled, op, command_args)
            if client:
                client_arg_name = resolve_client_arg_name(operation, kwargs)
                if client_arg_name in op_args:
                    command_args[client_arg_name] = client
            return op(**command_args)

        def default_arguments_loader():
            op = handler or self.get_op_handler(operation, operation_group=kwargs.get('operation_group'))
            self._apply_doc_string(op, kwargs)
            cmd_args = list(extract_args_from_signature(op, excluded_params=self.excluded_command_handler_args))
            return cmd_args

        def default_description_loader():
            op = handler or self.get_op_handler(operation, operation_group=kwargs.get('operation_group'))
            self._apply_doc_string(op, kwargs)
            return extract_full_summary_from_signature(op)

        kwargs['arguments_loader'] = argument_loader or default_arguments_loader
        kwargs['description_loader'] = description_loader or default_description_loader

        if self.supported_api_version(resource_type=kwargs.get('resource_type'),
                                      min_api=kwargs.get('min_api'),
                                      max_api=kwargs.get('max_api'),
                                      operation_group=kwargs.get('operation_group')):
            self._populate_command_group_table_with_subgroups(' '.join(name.split()[:-1]))
            self.command_table[name] = self.command_cls(self, name,
                                                        handler or default_command_handler,
                                                        **kwargs)

    def get_op_handler(self, operation, operation_group=None):
        """ Import and load the operation handler """
        # Patch the unversioned sdk path to include the appropriate API version for the
        # resource type in question.
        from importlib import import_module
        import types

        from azure.cli.core.profiles import AZURE_API_PROFILES
        from azure.cli.core.profiles._shared import get_versioned_sdk_path

        for rt in AZURE_API_PROFILES[self.cli_ctx.cloud.profile]:
            if operation.startswith(rt.import_prefix + '.'):
                operation = operation.replace(rt.import_prefix,
                                              get_versioned_sdk_path(self.cli_ctx.cloud.profile, rt,
                                                                     operation_group=operation_group))

        try:
            mod_to_import, attr_path = operation.split('#')
            op = import_module(mod_to_import)
            for part in attr_path.split('.'):
                op = getattr(op, part)
            if isinstance(op, types.FunctionType):
                return op
            return six.get_method_function(op)
        except (ValueError, AttributeError):
            raise ValueError("The operation '{}' is invalid.".format(operation))


def get_default_cli():
    from azure.cli.core.azlogging import AzCliLogging
    from azure.cli.core.commands import AzCliCommandInvoker
    from azure.cli.core.parser import AzCliCommandParser
    from azure.cli.core._config import GLOBAL_CONFIG_DIR, ENV_VAR_PREFIX
    from azure.cli.core._help import AzCliHelp
    from azure.cli.core._output import AzOutputProducer

    return AzCli(cli_name='az',
                 config_dir=GLOBAL_CONFIG_DIR,
                 config_env_var_prefix=ENV_VAR_PREFIX,
                 commands_loader_cls=MainCommandsLoader,
                 invocation_cls=AzCliCommandInvoker,
                 parser_cls=AzCliCommandParser,
                 logging_cls=AzCliLogging,
                 output_cls=AzOutputProducer,
                 help_cls=AzCliHelp)
