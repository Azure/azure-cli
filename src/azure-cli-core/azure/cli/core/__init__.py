# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from __future__ import print_function

__version__ = "2.0.43"

import os
import sys
import timeit

import six

from knack.arguments import ArgumentsContext
from knack.cli import CLI
from knack.commands import CLICommandsLoader
from knack.completion import ARGCOMPLETE_ENV_NAME
from knack.introspection import extract_args_from_signature, extract_full_summary_from_signature
from knack.log import get_logger
from knack.util import CLIError


logger = get_logger(__name__)

EXCLUDED_PARAMS = ['self', 'raw', 'polling', 'custom_headers', 'operation_config',
                   'content_version', 'kwargs', 'client', 'no_wait']
EVENT_FAILED_EXTENSION_LOAD = 'MainLoader.OnFailedExtensionLoad'


class AzCli(CLI):

    def __init__(self, **kwargs):
        super(AzCli, self).__init__(**kwargs)

        from azure.cli.core.commands.arm import add_id_parameters, register_global_subscription_parameter
        from azure.cli.core.cloud import get_active_cloud
        from azure.cli.core.extensions import register_extensions
        from azure.cli.core._session import ACCOUNT, CONFIG, SESSION

        import knack.events as events
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

        register_extensions(self)
        self.register_event(events.EVENT_INVOKER_POST_CMD_TBL_CREATE, add_id_parameters)
        register_global_subscription_parameter(self)

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
        from azure.cli.core.util import get_az_version_string
        print(get_az_version_string())

    def exception_handler(self, ex):  # pylint: disable=no-self-use
        from azure.cli.core.util import handle_exception
        return handle_exception(ex)


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
            except ImportError:
                pass
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
                    logger.error("Error loading command module '%s'", mod)
                    telemetry.set_exception(exception=ex, fault_type='module-load-error-' + mod,
                                            summary='Error loading module: {}'.format(mod))
                    logger.debug(traceback.format_exc())
            logger.debug("Loaded all modules in %.3f seconds. "
                         "(note: there's always an overhead with the first module loaded)",
                         cumulative_elapsed_time)

        def _update_command_table_from_extensions(ext_suppressions):

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
                    ext_name = ext.name
                    ext_dir = get_extension_path(ext_name)
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
                                preview=ext.preview)

                        self.command_table.update(extension_command_table)
                        self.command_group_table.update(extension_group_table)
                        elapsed_time = timeit.default_timer() - start_time
                        logger.debug("Loaded extension '%s' in %.3f seconds.", ext_name, elapsed_time)
                    except Exception:  # pylint: disable=broad-except
                        self.cli_ctx.raise_event(EVENT_FAILED_EXTENSION_LOAD, extension_name=ext_name)
                        logger.warning("Unable to load extension '%s'. Use --debug for more information.", ext_name)
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
                sup = getattr(m, 'suppress_extension', None)
                if sup and isinstance(sup, ModExtensionSuppress):
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

    def load_arguments(self, command):
        from azure.cli.core.commands.parameters import resource_group_name_type, get_location_type, deployment_name_type
        from knack.arguments import ignore_type

        command_loaders = self.cmd_to_loader_map.get(command, None)

        if command_loaders:
            with ArgumentsContext(self, '') as c:
                c.argument('resource_group_name', resource_group_name_type)
                c.argument('location', get_location_type(self.cli_ctx))
                c.argument('deployment_name', deployment_name_type)
                c.argument('cmd', ignore_type)

            for loader in command_loaders:
                loader.command_name = command
                self.command_table[command].load_arguments()  # this loads the arguments via reflection
                loader.load_arguments(command)  # this adds entries to the argument registries
                self.argument_registry.arguments.update(loader.argument_registry.arguments)
                self.extra_argument_registry.update(loader.extra_argument_registry)
                loader._update_command_definitions()  # pylint: disable=protected-access


class ModExtensionSuppress(object):  # pylint: disable=too-few-public-methods

    def __init__(self, mod_name, suppress_extension_name, suppress_up_to_version, reason=None, recommend_remove=False):
        self.mod_name = mod_name
        self.suppress_extension_name = suppress_extension_name
        self.suppress_up_to_version = suppress_up_to_version
        self.reason = reason
        self.recommend_remove = recommend_remove

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
        return should_suppress


class AzCommandsLoader(CLICommandsLoader):  # pylint: disable=too-many-instance-attributes

    def __init__(self, cli_ctx=None, min_profile=None, max_profile='latest',
                 command_group_cls=None, argument_context_cls=None, suppress_extension=None,
                 **kwargs):
        from azure.cli.core.commands import AzCliCommand, AzCommandGroup, AzArgumentContext

        super(AzCommandsLoader, self).__init__(cli_ctx=cli_ctx,
                                               command_cls=AzCliCommand,
                                               excluded_command_handler_args=EXCLUDED_PARAMS)
        self.min_profile = min_profile
        self.max_profile = max_profile
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
        elif not isinstance(doc_string_source, str):
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
        else:
            version = getattr(version, operation_group, None)
            if version:
                return version
            else:
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
            min_api=min_api or self.min_profile,
            max_api=max_api or self.max_profile,
            operation_group=operation_group)
        if isinstance(api_support, bool):
            return api_support
        elif operation_group:
            return getattr(api_support, operation_group)
        return api_support

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

            op = handler or self.get_op_handler(operation)
            op_args = get_arg_list(op)

            client = client_factory(self.cli_ctx, command_args) if client_factory else None
            supports_no_wait = kwargs.get('supports_no_wait', None)
            if supports_no_wait:
                no_wait_enabled = command_args.pop('no_wait', False)
                augment_no_wait_handler_args(no_wait_enabled, op, command_args)
            if client:
                client_arg_name = resolve_client_arg_name(operation, kwargs)
                if client_arg_name in op_args:
                    command_args[client_arg_name] = client
            result = op(**command_args)
            return result

        def default_arguments_loader():
            op = handler or self.get_op_handler(operation)
            self._apply_doc_string(op, kwargs)
            cmd_args = list(extract_args_from_signature(op, excluded_params=self.excluded_command_handler_args))
            return cmd_args

        def default_description_loader():
            op = handler or self.get_op_handler(operation)
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

    def get_op_handler(self, operation):
        """ Import and load the operation handler """
        # Patch the unversioned sdk path to include the appropriate API version for the
        # resource type in question.
        from importlib import import_module
        import types

        from azure.cli.core.profiles import AZURE_API_PROFILES
        from azure.cli.core.profiles._shared import get_versioned_sdk_path

        for rt in AZURE_API_PROFILES[self.cli_ctx.cloud.profile]:
            if operation.startswith(rt.import_prefix + ".operations."):
                subs = operation[len(rt.import_prefix + ".operations."):]
                operation_group = subs[:subs.index('_operations')]
                operation = operation.replace(
                    rt.import_prefix,
                    get_versioned_sdk_path(self.cli_ctx.cloud.profile, rt, operation_group=operation_group))
            elif operation.startswith(rt.import_prefix):
                operation = operation.replace(rt.import_prefix,
                                              get_versioned_sdk_path(self.cli_ctx.cloud.profile, rt))

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

    return AzCli(cli_name='az',
                 config_dir=GLOBAL_CONFIG_DIR,
                 config_env_var_prefix=ENV_VAR_PREFIX,
                 commands_loader_cls=MainCommandsLoader,
                 invocation_cls=AzCliCommandInvoker,
                 parser_cls=AzCliCommandParser,
                 logging_cls=AzCliLogging,
                 help_cls=AzCliHelp)
