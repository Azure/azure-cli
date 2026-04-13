# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.log import get_logger

from azure.cli.core import AzCommandsLoader
from azure.cli.core.commands import AzArgumentContext, CliCommandType
from azure.cli.command_modules.monitor._help import helps   # pylint: disable=unused-import

logger = get_logger(__name__)

_CONFIG_SECTION = 'monitor'
_USE_LEGACY_CONFIG_KEY = 'use_legacy'


# pylint: disable=line-too-long
class MonitorArgumentContext(AzArgumentContext):

    def resource_parameter(self, dest, arg_group=None, required=True, skip_validator=False, alias='resource',
                           preserve_resource_group_parameter=False):
        from azure.cli.command_modules.monitor.validators import get_target_resource_validator
        self.argument(dest, options_list='--{}'.format(alias), arg_group=arg_group, required=required,
                      validator=get_target_resource_validator(
                          dest, required, alias=alias,
                          preserve_resource_group_parameter=preserve_resource_group_parameter) if not skip_validator else None,
                      help="Name or ID of the target resource.")
        self.extra('namespace', options_list='--{}-namespace'.format(alias), arg_group=arg_group,
                   help="Target resource provider namespace.")
        self.extra('parent', options_list='--{}-parent'.format(alias), arg_group=arg_group,
                   help="Target resource parent path, if applicable.")
        self.extra('resource_type', options_list='--{}-type'.format(alias), arg_group=arg_group,
                   help="Target resource type. Can also accept namespace/type format (Ex: 'Microsoft.Compute/virtualMachines')")
        self.extra('resource_group_name', options_list=['--resource-group', '-g'], arg_group=arg_group)


class MonitorCommandsLoader(AzCommandsLoader):

    def __init__(self, cli_ctx=None):
        from azure.cli.core.profiles import ResourceType
        self._use_legacy = cli_ctx.config.getboolean(
            _CONFIG_SECTION, _USE_LEGACY_CONFIG_KEY, fallback=False) if cli_ctx else False
        if self._use_legacy:
            monitor_custom = CliCommandType(
                operations_tmpl='azure.cli.command_modules.monitor._legacy.custom#{}')
        else:
            monitor_custom = CliCommandType(
                operations_tmpl='azure.cli.command_modules.monitor.custom#{}')
        super().__init__(cli_ctx=cli_ctx,
                         resource_type=ResourceType.MGMT_MONITOR,
                         argument_context_cls=MonitorArgumentContext,
                         custom_command_type=monitor_custom)

    def load_command_table(self, args):
        if self._use_legacy:
            return self._load_legacy_command_table(args)
        return self._load_new_command_table(args)

    def _load_legacy_command_table(self, args):
        """Load commands from the vendored _legacy snapshot (pre-refactor code from dev branch)."""
        from azure.cli.core.aaz import load_aaz_command_table

        logger.warning(
            "The monitor module is using legacy mode. "
            "To switch to the new optimized implementation, run: "
            "az config set %s.%s=false",
            _CONFIG_SECTION, _USE_LEGACY_CONFIG_KEY)

        try:
            from ._legacy import aaz as legacy_aaz
        except ImportError:
            legacy_aaz = None
        if legacy_aaz:
            load_aaz_command_table(
                loader=self,
                aaz_pkg_name=legacy_aaz.__name__,
                args=args
            )

        from ._legacy.commands import load_command_table
        load_command_table(self, args)
        return self.command_table

    def _load_new_command_table(self, args):
        """Load commands from the current (refactored) implementation."""
        from azure.cli.command_modules.monitor.commands import load_command_table
        from azure.cli.core.aaz import load_aaz_command_table_args_guided

        try:
            from . import aaz
        except ImportError:
            aaz = None
        if aaz:
            load_aaz_command_table_args_guided(
                loader=self,
                aaz_pkg_name=aaz.__name__,
                args=args
            )

        try:
            from . import operations
        except ImportError:
            operations = None
        if operations:
            load_aaz_command_table_args_guided(
                loader=self,
                aaz_pkg_name=operations.__name__,
                args=args
            )

        load_command_table(self, args)
        return self.command_table

    def load_arguments(self, command):
        if self._use_legacy:
            from azure.cli.command_modules.monitor._legacy._params import load_arguments
        else:
            from azure.cli.command_modules.monitor._params import load_arguments
        load_arguments(self, command)


COMMAND_LOADER_CLS = MonitorCommandsLoader
