# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long

__version__ = "2.85.0"

import os
import sys
import json
import time

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
# Marker used by CommandIndex.get() to signal top-level tab completion optimization
TOP_LEVEL_COMPLETION_MARKER = '__top_level_completion__'
# Internal sentinel used to trigger latest-profile extension help overlay refresh path.
REFRESH_EXTENSION_HELP_OVERLAY_SENTINEL = '__refresh_extension_help_overlay__'

# [Reserved, in case of future usage]
# Modules that will always be loaded. They don't expose commands but hook into CLI core.
ALWAYS_LOADED_MODULES = []
# Extensions that will always be loaded if installed. They don't expose commands but hook into CLI core.
ALWAYS_LOADED_EXTENSIONS = ['azext_ai_examples', 'azext_next']
# Timeout (in seconds) for loading a single module. Acts as a safety valve to prevent indefinite hangs
MODULE_LOAD_TIMEOUT_SECONDS = 60
# Maximum number of worker threads for parallel module loading.
MAX_WORKER_THREAD_COUNT = 4


def _get_top_level_command(args):
    """Return normalized top-level command token or None when unavailable."""
    if not args:
        return None

    top_command = args[0]
    if not top_command or top_command.startswith('-'):
        return None

    return top_command.lower()


def _configure_knack():
    """Override consts defined in knack to make them Azure CLI-specific."""

    # Customize status tag messages.
    from knack.util import status_tag_messages
    ref_message = "Reference and support levels: https://aka.ms/CLI_refstatus"
    # Override the preview message.
    status_tag_messages['preview'] = "{} is in preview and under development. " + ref_message
    # Override the experimental message.
    status_tag_messages['experimental'] = "{} is experimental and under development. " + ref_message

    # Allow logs from 'azure' logger to be displayed.
    from knack.log import cli_logger_names
    cli_logger_names.append('azure')


_configure_knack()


class AzCli(CLI):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        from azure.cli.core.breaking_change import register_upcoming_breaking_change_info
        from azure.cli.core.commands import register_cache_arguments
        from azure.cli.core.commands.arm import (
            register_ids_argument, register_global_subscription_argument, register_global_policy_argument)
        from azure.cli.core.cloud import get_active_cloud
        from azure.cli.core.commands.transform import register_global_transforms
        from azure.cli.core._session import ACCOUNT, CONFIG, SESSION, INDEX, EXTENSION_INDEX, HELP_INDEX, EXTENSION_HELP_INDEX, VERSIONS
        from azure.cli.core.util import handle_version_update

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
        INDEX.load(os.path.join(azure_folder, 'commandIndex.json'))
        EXTENSION_INDEX.load(os.path.join(azure_folder, 'extensionIndex.json'))
        HELP_INDEX.load(os.path.join(azure_folder, 'helpIndex.json'))
        EXTENSION_HELP_INDEX.load(os.path.join(azure_folder, 'extensionHelpIndex.json'))
        VERSIONS.load(os.path.join(azure_folder, 'versionCheck.json'))
        handle_version_update()

        self.cloud = get_active_cloud(self)
        logger.debug('Current cloud config:\n%s', str(self.cloud.name))
        self.local_context = AzCLILocalContext(self)
        register_global_transforms(self)
        register_global_subscription_argument(self)
        register_ids_argument(self)  # global subscription must be registered first!
        register_global_policy_argument(self)
        register_cache_arguments(self)
        register_upcoming_breaking_change_info(self)

        self.progress_controller = None

        self._configure_style()

    def refresh_request_id(self):
        """Assign a new random GUID as x-ms-client-request-id

        The method must be invoked before each command execution in order to ensure
        unique client-side request ID is generated.
        """
        import uuid
        self.data['headers']['x-ms-client-request-id'] = str(uuid.uuid1())

    def get_progress_controller(self, det=False, spinner=None):
        from azure.cli.core.commands import progress
        if not self.progress_controller:
            self.progress_controller = progress.ProgressHook()

        self.progress_controller.init_progress(progress.get_progress_view(det, spinner=spinner))
        return self.progress_controller

    def get_cli_version(self):
        return __version__

    def show_version(self):
        from azure.cli.core.util import get_az_version_string, show_updates
        from azure.cli.core import telemetry

        telemetry.set_command_details(command="", parameters=["--version"])

        ver_string, updates_available_components = get_az_version_string()
        print(ver_string)
        show_updates(updates_available_components)

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
            logger.warning('Parameter persistence is turned on. Its information is saved in working directory %s. '
                           'You can run `az config param-persist off` to turn it off.',
                           self.local_context.effective_working_directory())
            args_str = []
            for name, value in local_context_args:
                args_str.append('{}: {}'.format(name, value))
            logger.warning('Your preference of %s now saved as persistent parameter. To learn more, type in `az '
                           'config param-persist --help`',
                           ', '.join(args_str) + (' is' if len(args_str) == 1 else ' are'))

    def _configure_style(self):
        from azure.cli.core.util import in_cloud_console
        from azure.cli.core.style import format_styled_text, get_theme_dict, Style

        # Configure Style
        if self.enable_color:
            theme = self.config.get('core', 'theme',
                                    fallback="cloud-shell" if in_cloud_console() else "dark")

            theme_dict = get_theme_dict(theme)

            if theme_dict:
                # If theme is used, also apply it to knack's logger
                from knack.util import color_map
                color_map['error'] = theme_dict[Style.ERROR]
                color_map['warning'] = theme_dict[Style.WARNING]
        else:
            theme = 'none'
        format_styled_text.theme = theme


class ModuleLoadResult:  # pylint: disable=too-few-public-methods
    def __init__(self, module_name, command_table, group_table, elapsed_time, error=None, traceback_str=None, command_loader=None):
        self.module_name = module_name
        self.command_table = command_table
        self.group_table = group_table
        self.elapsed_time = elapsed_time
        self.error = error
        self.traceback_str = traceback_str
        self.command_loader = command_loader


class MainCommandsLoader(CLICommandsLoader):

    # Format string for pretty-print the command module table
    header_mod = "%-20s %10s %9s %9s" % ("Name", "Load Time", "Groups", "Commands")
    item_format_string = "%-20s %10.3f %9d %9d"
    header_ext = header_mod + "  Directory"
    item_ext_format_string = item_format_string + "  %s"

    def __init__(self, cli_ctx=None):
        super().__init__(cli_ctx)
        self.cmd_to_loader_map = {}
        self.loaders = []

    def _create_stub_commands_for_completion(self, command_names):
        """Create stub commands for top-level tab completion optimization.

        Stub commands allow argcomplete to parse command names without loading modules.

        :param command_names: List of command names to create stubs for
        """
        from azure.cli.core.commands import AzCliCommand

        def _stub_handler(*_args, **_kwargs):
            """Stub command handler used only for argument completion."""
            return None

        for cmd_name in command_names:
            if cmd_name not in self.command_table:
                # Stub commands only need names for argcomplete parser construction.
                self.command_table[cmd_name] = AzCliCommand(self, cmd_name, _stub_handler)

    def _update_command_definitions(self):
        for cmd_name in self.command_table:
            loaders = self.cmd_to_loader_map[cmd_name]
            for loader in loaders:
                loader.command_table = self.command_table
                loader._update_command_definitions()  # pylint: disable=protected-access

    @staticmethod
    def _should_update_extension_index(index_extensions, command_index):
        """Return True when latest-profile extension overlays should be refreshed."""
        return (index_extensions is None and
                command_index is not None and
                command_index.cloud_profile == 'latest')

    def _is_latest_non_completion_invocation(self, command_index, args):
        """Return True for real latest-profile invocations (not shell completion)."""
        return (command_index is not None and
                command_index.cloud_profile == 'latest' and
                bool(args) and
                not self.cli_ctx.data['completer_active'])

    # pylint: disable=too-many-statements, too-many-locals, too-many-return-statements
    def load_command_table(self, args):
        from importlib import import_module
        import pkgutil
        import traceback
        from azure.cli.core.commands import (
            _load_extension_command_loader, ExtensionCommandSource)
        from azure.cli.core.extension import (
            get_extensions, get_extension_path, get_extension_modname)
        from azure.cli.core.breaking_change import (
            import_core_breaking_changes, import_extension_breaking_changes)

        def _update_command_table_from_modules(args, command_modules=None):
            """Loads command tables from modules and merge into the main command table.

            :param args: Arguments of the command.
            :param list command_modules: Command modules to load, in the format like ['resource', 'profile'].
             If None, will do module discovery and load all modules.
             If [], only ALWAYS_LOADED_MODULES will be loaded.
             Otherwise, the list will be extended using ALWAYS_LOADED_MODULES.
            """

            # As command modules are built-in, the existence of modules in ALWAYS_LOADED_MODULES is NOT checked
            if command_modules is not None:
                command_modules.extend(ALWAYS_LOADED_MODULES)
            else:
                # Perform module discovery
                from azure.cli.core import telemetry
                telemetry.set_command_index_rebuild_triggered(True)
                command_modules = []
                try:
                    mods_ns_pkg = import_module('azure.cli.command_modules')
                    command_modules = [modname for _, modname, _ in
                                       pkgutil.iter_modules(mods_ns_pkg.__path__)]
                    logger.debug('Discovered command modules: %s', command_modules)
                except ImportError as e:
                    logger.warning(e)

            start_time = time.perf_counter()
            logger.debug("Loading command modules...")
            results = self._load_modules(args, command_modules)

            count, cumulative_group_count, cumulative_command_count = \
                self._process_results_with_timing(results)

            total_elapsed_time = time.perf_counter() - start_time
            # Summary line
            logger.debug(self.item_format_string,
                         "Total ({})".format(count), total_elapsed_time,
                         cumulative_group_count, cumulative_command_count)

        def _update_command_table_from_extensions(ext_suppressions, extension_modname=None):
            """Loads command tables from extensions and merge into the main command table.

            :param ext_suppressions: Extension suppression information.
            :param extension_modname: Command modules to load, in the format like ['azext_timeseriesinsights'].
             If None, will do extension discovery and load all extensions.
             If [], only ALWAYS_LOADED_EXTENSIONS will be loaded.
             Otherwise, the list will be extended using ALWAYS_LOADED_EXTENSIONS.
             If the extensions in the list are not installed, it will be skipped.
            """
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

            def _filter_modname(extensions):
                # Extension's name may not be the same as its modname. eg. name: virtual-wan, modname: azext_vwan
                filtered_extensions = []
                for ext in extensions:
                    ext_mod = get_extension_modname(ext.name, ext.path)
                    # Filter the extensions according to the index
                    if ext_mod in extension_modname:
                        filtered_extensions.append(ext)
                        extension_modname.remove(ext_mod)
                if extension_modname:
                    logger.debug("These extensions are not installed and will be skipped: %s", extension_modname)
                return filtered_extensions

            extensions = get_extensions()
            if not extensions:
                return

            if extension_modname is not None:
                extension_modname.extend(ALWAYS_LOADED_EXTENSIONS)
                extensions = _filter_modname(extensions)
            allowed_extensions = _handle_extension_suppressions(extensions)
            module_commands = set(self.command_table.keys())

            count = 0
            cumulative_elapsed_time = 0
            cumulative_group_count = 0
            cumulative_command_count = 0
            logger.debug("Loading extensions:")
            logger.debug(self.header_ext)

            for ext in allowed_extensions:
                try:
                    # Import in the `for` loop because `allowed_extensions` can be []. In such case we
                    # don't need to import `check_version_compatibility` at all.
                    from azure.cli.core.extension.operations import check_version_compatibility
                    check_version_compatibility(ext.get_metadata())
                except CLIError as ex:
                    # issue warning and skip loading extensions that aren't compatible with the CLI core
                    logger.warning(ex)
                    continue
                ext_name = ext.name
                ext_dir = ext.path or get_extension_path(ext_name)
                sys.path.append(ext_dir)
                try:
                    ext_mod = get_extension_modname(ext_name, ext_dir=ext_dir)
                    # Add to the map. This needs to happen before we load commands as registering a command
                    # from an extension requires this map to be up-to-date.
                    # self._mod_to_ext_map[ext_mod] = ext_name
                    start_time = time.perf_counter()
                    extension_command_table, extension_group_table, extension_command_loader = \
                        _load_extension_command_loader(self, args, ext_mod)
                    import_extension_breaking_changes(ext_mod)

                    for cmd_name, cmd in extension_command_table.items():
                        cmd.command_source = ExtensionCommandSource(
                            extension_name=ext_name,
                            overrides_command=cmd_name in module_commands,
                            preview=ext.preview,
                            experimental=ext.experimental)

                    # Populate cmd_to_loader_map for extension commands
                    if extension_command_loader:
                        self.loaders.append(extension_command_loader)
                        for cmd_name in extension_command_table:
                            if cmd_name not in self.cmd_to_loader_map:
                                self.cmd_to_loader_map[cmd_name] = []
                            self.cmd_to_loader_map[cmd_name].append(extension_command_loader)

                    self.command_table.update(extension_command_table)
                    self.command_group_table.update(extension_group_table)

                    elapsed_time = time.perf_counter() - start_time
                    logger.debug(self.item_ext_format_string, ext_name, elapsed_time,
                                 len(extension_group_table), len(extension_command_table),
                                 ext_dir)
                    count += 1
                    cumulative_elapsed_time += elapsed_time
                    cumulative_group_count += len(extension_group_table)
                    cumulative_command_count += len(extension_command_table)
                except Exception as ex:  # pylint: disable=broad-except
                    self.cli_ctx.raise_event(EVENT_FAILED_EXTENSION_LOAD, extension_name=ext_name)
                    logger.warning("Unable to load extension '%s: %s'. Use --debug for more information.",
                                   ext_name, ex)
                    logger.debug(traceback.format_exc())
            # Summary line
            logger.debug(self.item_ext_format_string,
                         "Total ({})".format(count), cumulative_elapsed_time,
                         cumulative_group_count, cumulative_command_count, "")

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

        # Clear the tables to make this method idempotent
        self.command_group_table.clear()
        self.command_table.clear()

        # Import announced breaking changes in azure.cli.core._breaking_change.py
        import_core_breaking_changes()

        command_index = None
        # Set fallback=False to turn off command index in case of regression
        use_command_index = self.cli_ctx.config.getboolean('core', 'use_command_index', fallback=True)

        if use_command_index:
            command_index = CommandIndex(self.cli_ctx)
            index_result = command_index.get(args)
            if index_result:
                index_modules, index_extensions = index_result

                if index_modules == TOP_LEVEL_COMPLETION_MARKER:
                    self._create_stub_commands_for_completion(index_extensions)
                    _update_command_table_from_extensions([], ALWAYS_LOADED_EXTENSIONS)
                    return self.command_table

                # Always load modules and extensions, because some of them (like those in
                # ALWAYS_LOADED_EXTENSIONS) don't expose a command, but hooks into handlers in CLI core
                _update_command_table_from_modules(args, index_modules)

                # The index won't contain suppressed extensions
                _update_command_table_from_extensions([], index_extensions)

                if self._should_update_extension_index(index_extensions, command_index):
                    command_index.update_extension_index(self.command_table)
                    self._cache_help_index(command_index)

                logger.debug("Loaded %d groups, %d commands.", len(self.command_group_table), len(self.command_table))
                from azure.cli.core.util import roughly_parse_command
                # The index may be outdated. Make sure the command appears in the loaded command table
                raw_cmd = roughly_parse_command(args)
                for cmd in self.command_table:
                    if raw_cmd.startswith(cmd):
                        # For commands with positional arguments, the raw command won't match the one in the
                        # command table. For example, `az find vm create` won't exist in the command table, but the
                        # corresponding command should be `az find`.
                        # raw command  : az find vm create
                        # command table: az find
                        # remaining    :         vm create
                        logger.debug("Found a match in the command table.")
                        logger.debug("Raw command  : %s", raw_cmd)
                        logger.debug("Command table: %s", cmd)
                        remaining = raw_cmd[len(cmd) + 1:]
                        if remaining:
                            logger.debug("remaining    : %s %s", ' ' * len(cmd), remaining)
                        return self.command_table
                # For command group, it must be an exact match, as no positional argument is supported by
                # command group operations.
                if raw_cmd in self.command_group_table:
                    logger.debug("Found a match in the command group table for '%s'.", raw_cmd)
                    return self.command_table
                if self.cli_ctx.data['completer_active']:
                    # If the command is not complete in autocomplete mode, we should match shorter command.
                    # For example, `account sho` should match `account`.
                    logger.debug("Could not find a match in the command or command group table for '%s'", raw_cmd)
                    trimmed_raw_cmd = ' '.join(raw_cmd.split()[:-1])
                    logger.debug("In autocomplete mode, try to match trimmed raw cmd: '%s'", trimmed_raw_cmd)
                    if not trimmed_raw_cmd:
                        # If full command is 'az acc', raw_cmd is 'acc', trimmed_raw_cmd is ''.
                        logger.debug("Trimmed raw cmd is empty, return command table.")
                        return self.command_table
                    if trimmed_raw_cmd in self.command_group_table:
                        logger.debug("Found a match in the command group table for trimmed raw cmd: '%s'.",
                                     trimmed_raw_cmd)
                        return self.command_table

                logger.debug("Could not find a match in the command or command group table for '%s'. "
                             "The index may be outdated.", raw_cmd)

                if self._is_latest_non_completion_invocation(command_index, args):
                    top_command = _get_top_level_command(args)
                    packaged_core_index = command_index.get_packaged_core_index() or {}
                    if top_command and top_command != 'help' and top_command not in packaged_core_index:
                        logger.debug("Top-level command '%s' is not in packaged core index. "
                                     "Skipping full core module reload.", top_command)
                        return self.command_table
            else:
                logger.debug("No module found from index for '%s'", args)

        logger.debug("Loading all modules and extensions")
        _update_command_table_from_modules(args)

        ext_suppressions = _get_extension_suppressions(self.loaders)
        # We always load extensions even if the appropriate module has been loaded
        # as an extension could override the commands already loaded.
        _update_command_table_from_extensions(ext_suppressions)
        logger.debug("Loaded %d groups, %d commands.", len(self.command_group_table), len(self.command_table))

        if use_command_index:
            command_index.update(self.command_table)
            self._cache_help_index(command_index)

        return self.command_table

    def _display_cached_help(self, help_data, command_path='root'):
        """Display help from cached help index without loading modules."""
        # Delegate to the help system for consistent formatting
        self.cli_ctx.invocation.help.show_cached_help(help_data, command_path)

    def _cache_help_index(self, command_index):
        """Cache help summary for top-level (root) help only."""
        try:
            from azure.cli.core.parser import AzCliCommandParser
            from azure.cli.core._help import CliGroupHelpFile, extract_help_index_data

            parser = AzCliCommandParser(self.cli_ctx)
            parser.load_command_table(self)

            subparser = parser.subparsers.get(tuple())
            if subparser:
                help_file = CliGroupHelpFile(self.cli_ctx.invocation.help, '', subparser)
                help_file.load(subparser)

                groups, commands = extract_help_index_data(help_file)

                if groups or commands:
                    help_index_data = {'groups': groups, 'commands': commands}
                    command_index.set_help_index(help_index_data)
                    logger.debug("Cached top-level help with %d groups and %d commands", len(groups), len(commands))

        except Exception as ex:  # pylint: disable=broad-except
            logger.debug("Failed to cache help data: %s", ex)

    @staticmethod
    def _sort_command_loaders(command_loaders):
        module_command_loaders = []
        extension_command_loaders = []

        # Separate module and extension command loaders
        for loader in command_loaders:
            if loader.__module__.startswith('azext'):
                extension_command_loaders.append(loader)
            else:
                module_command_loaders.append(loader)

        # Sort name in each command loader list
        module_command_loaders.sort(key=lambda loader: loader.__class__.__name__)
        extension_command_loaders.sort(key=lambda loader: loader.__class__.__name__)

        # Module first, then extension
        sorted_command_loaders = module_command_loaders + extension_command_loaders
        return sorted_command_loaders

    def load_arguments(self, command=None):
        from azure.cli.core.commands.parameters import (
            resource_group_name_type, get_location_type, deployment_name_type, vnet_name_type, subnet_name_type)
        from knack.arguments import ignore_type

        # omit specific command to load everything
        if command is None:
            command_loaders = set()
            for loaders in self.cmd_to_loader_map.values():
                command_loaders = command_loaders.union(set(loaders))
            # sort command loaders for consistent order when loading all commands for docs generation to avoid random diff
            command_loaders = self._sort_command_loaders(command_loaders)
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

    def _load_modules(self, args, command_modules):
        """Load command modules using ThreadPoolExecutor with timeout protection."""
        import concurrent.futures
        from concurrent.futures import ThreadPoolExecutor
        from azure.cli.core.commands import BLOCKED_MODS

        results = []
        with ThreadPoolExecutor(max_workers=MAX_WORKER_THREAD_COUNT) as executor:
            future_to_module = {executor.submit(self._load_single_module, mod, args): mod
                                for mod in command_modules if mod not in BLOCKED_MODS}

            try:
                for future in concurrent.futures.as_completed(future_to_module, timeout=MODULE_LOAD_TIMEOUT_SECONDS):
                    try:
                        result = future.result()
                        results.append(result)
                    except (ImportError, AttributeError, TypeError, ValueError) as ex:
                        mod = future_to_module[future]
                        logger.warning("Module '%s' load failed: %s", mod, ex)
                        results.append(ModuleLoadResult(mod, {}, {}, 0, ex))
                    except Exception as ex:  # pylint: disable=broad-exception-caught
                        mod = future_to_module[future]
                        logger.warning("Module '%s' load failed with unexpected exception: %s", mod, ex)
                        results.append(ModuleLoadResult(mod, {}, {}, 0, ex))
            except concurrent.futures.TimeoutError:
                for future, mod in future_to_module.items():
                    if future.done():
                        try:
                            result = future.result()
                            results.append(result)
                        except Exception as ex:  # pylint: disable=broad-exception-caught
                            logger.warning("Module '%s' load failed: %s", mod, ex)
                            results.append(ModuleLoadResult(mod, {}, {}, 0, ex))
                    else:
                        logger.warning("Module '%s' load timeout after %s seconds", mod, MODULE_LOAD_TIMEOUT_SECONDS)
                        results.append(ModuleLoadResult(mod, {}, {}, 0,
                                                        Exception(f"Module '{mod}' load timeout")))

        return results

    def _load_single_module(self, mod, args):
        from azure.cli.core.breaking_change import import_module_breaking_changes
        from azure.cli.core.commands import _load_module_command_loader
        import traceback
        try:
            start_time = time.perf_counter()
            module_command_table, module_group_table, command_loader = _load_module_command_loader(self, args, mod)
            import_module_breaking_changes(mod)
            elapsed_time = time.perf_counter() - start_time
            return ModuleLoadResult(mod, module_command_table, module_group_table, elapsed_time, command_loader=command_loader)
        except Exception as ex:  # pylint: disable=broad-except
            tb_str = traceback.format_exc()
            return ModuleLoadResult(mod, {}, {}, 0, ex, tb_str)

    def _handle_module_load_error(self, result):
        """Handle errors that occurred during module loading."""
        from azure.cli.core import telemetry

        logger.error("Error loading command module '%s': %s", result.module_name, result.error)
        telemetry.set_exception(exception=result.error,
                                fault_type='module-load-error-' + result.module_name,
                                summary='Error loading module: {}'.format(result.module_name))
        if result.traceback_str:
            logger.debug(result.traceback_str)

    def _process_successful_load(self, result):
        """Process successfully loaded module results."""
        if result.command_loader:
            self.loaders.append(result.command_loader)

            for cmd in result.command_table:
                if cmd not in self.cmd_to_loader_map:
                    self.cmd_to_loader_map[cmd] = []
                self.cmd_to_loader_map[cmd].append(result.command_loader)

        for cmd in result.command_table.values():
            cmd.command_source = result.module_name

        self.command_table.update(result.command_table)
        self.command_group_table.update(result.group_table)

        logger.debug(self.item_format_string, result.module_name, result.elapsed_time,
                     len(result.group_table), len(result.command_table))

    def _process_results_with_timing(self, results):
        """Process pre-loaded module results with timing and progress reporting."""
        logger.debug("Loaded command modules in parallel:")
        logger.debug(self.header_mod)

        count = 0
        cumulative_group_count = 0
        cumulative_command_count = 0

        for result in results:
            if result.error:
                self._handle_module_load_error(result)
            else:
                self._process_successful_load(result)
                count += 1
                cumulative_group_count += len(result.group_table)
                cumulative_command_count += len(result.command_table)

        return count, cumulative_group_count, cumulative_command_count


class CommandIndex:

    _COMMAND_INDEX = 'commandIndex'
    _COMMAND_INDEX_VERSION = 'version'
    _COMMAND_INDEX_CLOUD_PROFILE = 'cloudProfile'
    _HELP_INDEX = 'helpIndex'
    _PACKAGED_COMMAND_INDEX_LATEST = 'commandIndex.latest.json'
    _PACKAGED_HELP_INDEX_LATEST = 'helpIndex.latest.json'

    def __init__(self, cli_ctx=None):
        """Class to manage command index.

        :param cli_ctx: Only needed when `get` or `update` is called.
        """
        from azure.cli.core._session import INDEX, EXTENSION_INDEX, HELP_INDEX, EXTENSION_HELP_INDEX
        self.INDEX = INDEX
        self.EXTENSION_INDEX = EXTENSION_INDEX
        self.HELP_INDEX = HELP_INDEX
        self.EXTENSION_HELP_INDEX = EXTENSION_HELP_INDEX
        if cli_ctx:
            self.version = __version__
            self.cloud_profile = cli_ctx.cloud.profile
        self.cli_ctx = cli_ctx

    def _is_index_valid(self):
        """Check if the command index version and cloud profile are valid.

        :return: True if index is valid, False otherwise
        """
        index_version = self.INDEX.get(self._COMMAND_INDEX_VERSION)
        cloud_profile = self.INDEX.get(self._COMMAND_INDEX_CLOUD_PROFILE)
        return (index_version and index_version == self.version and
                cloud_profile and cloud_profile == self.cloud_profile)

    def _is_extension_index_valid(self):
        """Check if the extension index version and cloud profile are valid."""
        index_version = self.EXTENSION_INDEX.get(self._COMMAND_INDEX_VERSION)
        cloud_profile = self.EXTENSION_INDEX.get(self._COMMAND_INDEX_CLOUD_PROFILE)
        return (index_version and index_version == self.version and
                cloud_profile and cloud_profile == self.cloud_profile)

    def _is_extension_help_index_valid(self):
        """Check if the extension help index version and cloud profile are valid."""
        index_version = self.EXTENSION_HELP_INDEX.get(self._COMMAND_INDEX_VERSION)
        cloud_profile = self.EXTENSION_HELP_INDEX.get(self._COMMAND_INDEX_CLOUD_PROFILE)
        return (index_version and index_version == self.version and
                cloud_profile and cloud_profile == self.cloud_profile)

    def _clear_extension_index_cache(self):
        """Clear extension command index cache metadata and payload."""
        self.EXTENSION_INDEX[self._COMMAND_INDEX_VERSION] = ""
        self.EXTENSION_INDEX[self._COMMAND_INDEX_CLOUD_PROFILE] = ""
        self.EXTENSION_INDEX[self._COMMAND_INDEX] = {}

    def _clear_extension_help_overlay_cache(self):
        """Clear extension help overlay cache metadata and payload."""
        self.EXTENSION_HELP_INDEX[self._COMMAND_INDEX_VERSION] = ""
        self.EXTENSION_HELP_INDEX[self._COMMAND_INDEX_CLOUD_PROFILE] = ""
        self.EXTENSION_HELP_INDEX[self._HELP_INDEX] = {}

    def _get_top_level_completion_commands(self, index=None):
        """Get top-level command names for tab completion optimization.

        Returns marker and list of top-level commands (e.g., 'network', 'vm') for creating
        stub commands without module loading. Returns None if index is empty, triggering
        fallback to full module loading.

        :return: tuple of (TOP_LEVEL_COMPLETION_MARKER, list of top-level command names) or None
        """
        index = index or self.INDEX.get(self._COMMAND_INDEX) or {}
        if not index:
            logger.debug("Command index is empty, will fall back to loading all modules")
            return None
        top_level_commands = list(index.keys())
        logger.debug("Top-level completion: %d commands available", len(top_level_commands))
        return TOP_LEVEL_COMPLETION_MARKER, top_level_commands

    def _can_use_packaged_command_index(self, ignore_extensions=False):
        """Whether packaged command index can be used safely for this invocation."""
        if self.cloud_profile != 'latest':
            return False

        if ignore_extensions:
            return True

        # If non-always-loaded extensions are installed, we need a full rebuild to include overrides/extensions.
        if self._has_non_always_loaded_extensions():
            return False

        return True

    def _load_packaged_command_index(self):
        """Load packaged command index for latest profile if present."""
        file_path = os.path.join(os.path.dirname(__file__), self._PACKAGED_COMMAND_INDEX_LATEST)
        if not os.path.isfile(file_path):
            return None

        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError) as ex:
            logger.debug("Failed to load packaged command index file '%s': %s", file_path, ex)
            return None

        if not isinstance(data, dict):
            logger.debug("Packaged command index file '%s' has invalid schema.", file_path)
            return None

        return data

    def _load_packaged_help_index(self):
        """Load packaged help index for latest profile if present."""
        file_path = os.path.join(os.path.dirname(__file__), self._PACKAGED_HELP_INDEX_LATEST)
        if not os.path.isfile(file_path):
            return None

        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError) as ex:
            logger.debug("Failed to load packaged help index file '%s': %s", file_path, ex)
            return None

        if not isinstance(data, dict):
            logger.debug("Packaged help index file '%s' has invalid schema.", file_path)
            return None

        version_matches = data.get(self._COMMAND_INDEX_VERSION) == self.version
        profile_matches = data.get(self._COMMAND_INDEX_CLOUD_PROFILE) == self.cloud_profile
        if not version_matches or not profile_matches:
            if not version_matches:
                logger.debug("Packaged help index version doesn't match current CLI version.")
            if not profile_matches:
                logger.debug("Packaged help index cloud profile doesn't match current cloud profile.")
            return None

        help_index = data.get(self._HELP_INDEX)
        if not isinstance(help_index, dict) or not help_index:
            logger.debug("Packaged help index mapping is missing or empty.")
            return None

        return help_index

    @staticmethod
    def _has_non_always_loaded_extensions():
        """Return True if a non-always-loaded extension is installed."""
        from azure.cli.core.extension import get_extensions, get_extension_modname

        try:
            for ext in get_extensions() or []:
                ext_mod = get_extension_modname(ext.name, ext.path)
                if ext_mod not in ALWAYS_LOADED_EXTENSIONS:
                    logger.debug("Found installed extension '%s' (%s).", ext.name, ext_mod)
                    return True
        except Exception as ex:  # pylint: disable=broad-except
            logger.debug("Failed to evaluate installed extensions: %s", ex)
            return True

        return False

    def _get_packaged_command_index(self, ignore_extensions=False):
        """Get packaged command index mapping if valid for current profile/version."""
        if not self._can_use_packaged_command_index(ignore_extensions=ignore_extensions):
            return None

        packaged_index = self._load_packaged_command_index()
        if not packaged_index:
            return None

        if packaged_index.get(self._COMMAND_INDEX_VERSION) != self.version:
            logger.debug("Packaged command index version doesn't match current CLI version.")
            return None

        if packaged_index.get(self._COMMAND_INDEX_CLOUD_PROFILE) != self.cloud_profile:
            logger.debug("Packaged command index cloud profile doesn't match current cloud profile.")
            return None

        index = packaged_index.get(self._COMMAND_INDEX)
        if not isinstance(index, dict) or not index:
            logger.debug("Packaged command index mapping is missing or empty.")
            return None

        logger.debug("Using packaged command index for profile '%s'.", self.cloud_profile)
        return index

    def get_packaged_core_index(self):
        """Get packaged core command index mapping, ignoring extension presence checks."""
        return self._get_packaged_command_index(ignore_extensions=True)

    @staticmethod
    def _blend_command_indices(core_index, extension_index):
        """Blend packaged core index with local extension overlay index."""
        blended = {cmd: list(mods) for cmd, mods in (core_index or {}).items()}
        for cmd, mods in (extension_index or {}).items():
            if cmd not in blended:
                blended[cmd] = []
            for mod in mods:
                if mod not in blended[cmd]:
                    blended[cmd].append(mod)
        return blended

    @staticmethod
    def _blend_help_indices(base_help_index, extension_help_index):
        """Blend packaged core help with extension-only help overlay."""
        blended = {
            'groups': dict((base_help_index or {}).get('groups') or {}),
            'commands': dict((base_help_index or {}).get('commands') or {})
        }
        ext_help_index = extension_help_index or {}
        for section in ('groups', 'commands'):
            blended_section = blended[section]
            for key, value in (ext_help_index.get(section) or {}).items():
                blended_section[key] = value
        return blended

    @staticmethod
    def _build_extension_help_overlay(base_help_index, full_help_index):
        """Build extension-only help overlay by diffing full help against packaged core help."""
        overlay = {'groups': {}, 'commands': {}}
        base_help_index = base_help_index or {}
        full_help_index = full_help_index or {}
        for section in ('groups', 'commands'):
            base_section = base_help_index.get(section) or {}
            full_section = full_help_index.get(section) or {}
            for key, value in full_section.items():
                if key not in base_section or base_section[key] != value:
                    overlay[section][key] = value
        return overlay

    def _get_blended_latest_index(self):
        """Get effective index for latest profile by blending core and extension indices."""
        if self.cloud_profile != 'latest':
            return None, False, False

        core_index = self._get_packaged_command_index(ignore_extensions=True)
        if not core_index:
            return None, False, False

        extension_index = {}
        extension_index_available = False
        has_non_always_loaded_extensions = self._has_non_always_loaded_extensions()
        if self._is_extension_index_valid():
            extension_index = self.EXTENSION_INDEX.get(self._COMMAND_INDEX) or {}
            extension_index_available = True
        else:
            if self.EXTENSION_INDEX.get(self._COMMAND_INDEX):
                logger.debug("Extension index version or cloud profile is invalid, clearing local extension index.")
                self._clear_extension_index_cache()

        if extension_index:
            logger.debug("Blending packaged core index with local extension index.")
        return self._blend_command_indices(core_index, extension_index), extension_index_available, has_non_always_loaded_extensions

    def _resolve_latest_index_lookup(self, args, top_command):
        """Resolve command lookup for latest profile using blended packaged and extension indices."""
        force_packaged_for_version = bool(top_command == 'version')
        index, extension_index_available, has_non_always_loaded_extensions = self._get_blended_latest_index()
        if index is None:
            return None

        force_load_all_extensions = (has_non_always_loaded_extensions and
                                     not extension_index_available and
                                     not force_packaged_for_version)
        result = self._lookup_command_in_index(index, args,
                                               force_load_all_extensions=force_load_all_extensions)
        if result:
            return result

        if (args and not args[0].startswith('-') and
                not self.cli_ctx.data['completer_active'] and
                not force_packaged_for_version and
                top_command != 'help'):
            # Unknown top-level command on latest should prefer extension-only retry and avoid
            # full core module rebuild to preserve packaged-index startup benefit.
            if has_non_always_loaded_extensions:
                logger.debug("No match found in blended latest index for '%s'. Loading all extensions.",
                             args[0])
                return [], None

            logger.debug("No match found in latest index for '%s' and no dynamic extensions are installed. "
                         "Skipping core module rebuild.", args[0])
            return [], []

        logger.debug("No match found in blended latest index. Falling back to local command index.")
        return None

    def get(self, args):
        """Get the corresponding module and extension list of a command.

        :param args: command arguments, like ['network', 'vnet', 'create', '-h']
        :return: a tuple containing a list of modules and a list of extensions.
        """

        top_command = _get_top_level_command(args)

        if self.cloud_profile == 'latest':
            latest_result = self._resolve_latest_index_lookup(args, top_command)
            if latest_result is not None:
                return latest_result

        # For non-latest, use local command index and fallback logic.
        index = None
        if self._is_index_valid():
            index = self.INDEX.get(self._COMMAND_INDEX) or {}
        else:
            # `az version` should stay fast even when extensions are installed.
            force_packaged_for_version = bool(top_command == 'version' and self.cloud_profile == 'latest')
            index = self._get_packaged_command_index(ignore_extensions=force_packaged_for_version)
            if index is None:
                logger.debug("Command index version or cloud profile is invalid or doesn't match the current command.")
                self.invalidate()
                return None

        return self._lookup_command_in_index(index, args)

    def _lookup_command_in_index(self, index, args, force_load_all_extensions=False):
        """Lookup command modules/extensions from a resolved index mapping."""

        # Make sure the top-level command is provided, like `az version`.
        # Skip command index for `az` or `az --help`.
        top_command = _get_top_level_command(args)
        if not top_command:
            # For top-level completion (az [tab])
            if not args and self.cli_ctx.data.get('completer_active'):
                return self._get_top_level_completion_commands(index=index)
            return None

        index = index or {}

        # Check the command index for (command: [module]) mapping, like
        # "network": ["azure.cli.command_modules.natgateway", "azure.cli.command_modules.network", "azext_firewall"]
        index_modules_extensions = index.get(top_command)
        if not index_modules_extensions and self.cli_ctx.data['completer_active']:
            # If user type `az acco`, command begin with `acco` will be matched.
            logger.debug("In autocomplete mode, load commands starting with: '%s'", top_command)
            index_modules_extensions = []
            for command in index:
                if command.startswith(top_command):
                    index_modules_extensions += index[command]

        if index_modules_extensions:
            # This list contains both built-in modules and extensions
            index_builtin_modules = []
            index_extensions = []
            # Found modules from index
            logger.debug("Modules found from index for '%s': %s", top_command, index_modules_extensions)
            command_module_prefix = 'azure.cli.command_modules.'
            for m in index_modules_extensions:
                if m.startswith(command_module_prefix):
                    # The top-level command is from a command module
                    index_builtin_modules.append(m[len(command_module_prefix):])
                elif m.startswith('azext_'):
                    # The top-level command is from an extension
                    index_extensions.append(m)
                else:
                    logger.warning("Unrecognized module: %s", m)

            if force_load_all_extensions:
                logger.debug("Extension index is unavailable. Loading all installed extensions for safety.")
                index_extensions = None
            return index_builtin_modules, index_extensions

        if force_load_all_extensions and not self.cli_ctx.data['completer_active']:
            logger.debug("Top-level command '%s' not found in blended index. Loading all extensions.", top_command)
            return [], None

        return None

    def _get_help_index_cached_local(self, latest_fallback=False):
        """Return cached local help index when available and index metadata is valid."""
        if not self._is_index_valid():
            return None

        help_index = self.HELP_INDEX.get(self._HELP_INDEX, {})
        if not help_index:
            return None

        if latest_fallback:
            logger.debug("Using cached local help index with %d entries", len(help_index))
        else:
            logger.debug("Using cached help index with %d entries", len(help_index))
        return help_index

    def _get_help_index_latest(self):
        """Return help index for latest profile using packaged help and extension overlay."""
        # Packaged help is the base for latest profile.
        packaged_help_index = self._load_packaged_help_index()
        if not packaged_help_index:
            # Defensive fallback to local cache if packaged asset is unavailable.
            return self._get_help_index_cached_local(latest_fallback=True)

        if self._is_extension_help_index_valid():
            extension_help_index = self.EXTENSION_HELP_INDEX.get(self._HELP_INDEX, {})
            if extension_help_index:
                logger.debug("Blending packaged help index with extension help overlay (%d groups, %d commands).",
                             len(extension_help_index.get('groups') or {}),
                             len(extension_help_index.get('commands') or {}))
            return self._blend_help_indices(packaged_help_index, extension_help_index)

        # Clear stale overlay cache if schema exists but metadata is invalid.
        if self.EXTENSION_HELP_INDEX.get(self._HELP_INDEX):
            self._clear_extension_help_overlay_cache()

        if self._has_non_always_loaded_extensions():
            logger.debug("Extension help overlay unavailable on latest profile. Help index will be refreshed when overlay becomes available.")
            return None

        logger.debug("Using packaged help index with %d entries", len(packaged_help_index))
        return packaged_help_index

    def get_help_index(self):
        """Get the help index for top-level help display.

        :return: Dictionary mapping top-level commands to their short summaries, or None if not available
        """
        if self.cloud_profile == 'latest':
            return self._get_help_index_latest()

        return self._get_help_index_cached_local()

    def needs_latest_extension_help_overlay_refresh(self):
        """Return True when latest-profile top-level help should refresh extension help overlay."""
        if self.cloud_profile != 'latest':
            return False

        if self._is_extension_help_index_valid():
            return False

        return self._has_non_always_loaded_extensions()

    def set_help_index(self, help_data):
        """Set the help index data.

        :param help_data: Help index data structure containing groups and commands
        """
        if self.cloud_profile == 'latest':
            packaged_help_index = self._load_packaged_help_index() or {'groups': {}, 'commands': {}}
            extension_help_overlay = self._build_extension_help_overlay(packaged_help_index, help_data)

            self.EXTENSION_HELP_INDEX[self._COMMAND_INDEX_VERSION] = __version__
            self.EXTENSION_HELP_INDEX[self._COMMAND_INDEX_CLOUD_PROFILE] = self.cloud_profile
            self.EXTENSION_HELP_INDEX[self._HELP_INDEX] = extension_help_overlay

            # Keep local full help cache empty for latest; packaged base + extension overlay are authoritative.
            self.HELP_INDEX[self._HELP_INDEX] = {}
            if self.INDEX.get(self._HELP_INDEX):
                self.INDEX[self._HELP_INDEX] = {}
            return

        self.HELP_INDEX[self._HELP_INDEX] = help_data
        # Clear legacy key if it exists in commandIndex.json.
        if self.INDEX.get(self._HELP_INDEX):
            self.INDEX[self._HELP_INDEX] = {}

    def update(self, command_table):
        """Update the command index according to the given command table.

        :param command_table: The command table built by azure.cli.core.MainCommandsLoader.load_command_table
        """
        start_time = time.perf_counter()
        self.INDEX[self._COMMAND_INDEX_VERSION] = __version__
        self.INDEX[self._COMMAND_INDEX_CLOUD_PROFILE] = self.cloud_profile
        from collections import defaultdict
        index = defaultdict(list)

        # self.cli_ctx.invocation.commands_loader.command_table doesn't exist in DummyCli due to the lack of invocation
        for command_name, command in command_table.items():
            # Get the top-level name: <vm> create
            top_command = command_name.split()[0]
            # Get module name, like azure.cli.command_modules.vm, azext_webapp
            module_name = command.loader.__module__
            if module_name not in index[top_command]:
                index[top_command].append(module_name)

        elapsed_time = time.perf_counter() - start_time
        self.INDEX[self._COMMAND_INDEX] = index

        self.update_extension_index(command_table)

        logger.debug("Updated command index in %.3f seconds.", elapsed_time)

    def update_extension_index(self, command_table):
        """Update extension-only overlay index from a command table (latest profile only)."""
        if self.cloud_profile != 'latest':
            return

        from collections import defaultdict
        extension_index = defaultdict(list)
        for command_name, command in command_table.items():
            top_command = command_name.split()[0]
            module_name = command.loader.__module__
            if module_name.startswith('azext_') and module_name not in extension_index[top_command]:
                extension_index[top_command].append(module_name)

        self.EXTENSION_INDEX[self._COMMAND_INDEX_VERSION] = __version__
        self.EXTENSION_INDEX[self._COMMAND_INDEX_CLOUD_PROFILE] = self.cloud_profile
        self.EXTENSION_INDEX[self._COMMAND_INDEX] = extension_index

    def invalidate(self):
        """Invalidate the command index.

        This function MUST be called when installing or updating extensions. Otherwise, when an extension
            1. overrides a built-in command, or
            2. extends an existing command group,
        the command or command group will only be loaded from the command modules as per the stale command index,
        making the newly installed extension be ignored.

        This function can be called when removing extensions.
        """
        self.INDEX[self._COMMAND_INDEX_VERSION] = ""
        self.INDEX[self._COMMAND_INDEX_CLOUD_PROFILE] = ""
        self.INDEX[self._COMMAND_INDEX] = {}
        self._clear_extension_index_cache()
        self._clear_extension_help_overlay_cache()
        self.HELP_INDEX[self._HELP_INDEX] = {}
        # Clear legacy key if it exists in commandIndex.json.
        if self.INDEX.get(self._HELP_INDEX):
            self.INDEX[self._HELP_INDEX] = {}
        logger.debug("Command index has been invalidated.")


class ModExtensionSuppress:  # pylint: disable=too-few-public-methods

    def __init__(self, mod_name, suppress_extension_name, suppress_up_to_version, reason=None, recommend_remove=False,
                 recommend_update=False):
        self.mod_name = mod_name
        self.suppress_extension_name = suppress_extension_name
        self.suppress_up_to_version = suppress_up_to_version
        self.reason = reason
        self.recommend_remove = recommend_remove
        self.recommend_update = recommend_update

    def handle_suppress(self, ext):
        from packaging.version import parse
        should_suppress = ext.name == self.suppress_extension_name and ext.version and \
            parse(ext.version) <= parse(self.suppress_up_to_version)
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

        super().__init__(cli_ctx=cli_ctx,
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

    # Please use add_cli_command instead of _cli_command.
    # Currently "keyvault" and "batch" modules are still rely on this function, so it cannot be removed now.
    def _cli_command(self, name, operation=None, handler=None, argument_loader=None, description_loader=None, **kwargs):

        from knack.deprecation import Deprecated

        kwargs['deprecate_info'] = Deprecated.ensure_new_style_deprecation(self.cli_ctx, kwargs, 'command')

        if operation and not isinstance(operation, str):
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

    def add_cli_command(self, name, command_operation, **kwargs):
        """Register a command in command_table with command operation provided"""
        from knack.deprecation import Deprecated
        from .commands.command_operation import BaseCommandOperation
        if not issubclass(type(command_operation), BaseCommandOperation):
            raise TypeError("CommandOperation must be an instance of subclass of BaseCommandOperation."
                            " Got instance of '{}'".format(type(command_operation)))

        kwargs['deprecate_info'] = Deprecated.ensure_new_style_deprecation(self.cli_ctx, kwargs, 'command')

        name = ' '.join(name.split())

        if self.supported_api_version(resource_type=kwargs.get('resource_type'),
                                      min_api=kwargs.get('min_api'),
                                      max_api=kwargs.get('max_api'),
                                      operation_group=kwargs.get('operation_group')):
            self._populate_command_group_table_with_subgroups(' '.join(name.split()[:-1]))
            self.command_table[name] = self.command_cls(loader=self,
                                                        name=name,
                                                        handler=command_operation.handler,
                                                        arguments_loader=command_operation.arguments_loader,
                                                        description_loader=command_operation.description_loader,
                                                        command_operation=command_operation,
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
                break

        try:
            mod_to_import, attr_path = operation.split('#')
            op = import_module(mod_to_import)
            for part in attr_path.split('.'):
                op = getattr(op, part)
            if isinstance(op, types.FunctionType):
                return op
            return op.__func__
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
