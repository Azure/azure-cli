# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core import AzCommandsLoader
from azure.cli.core.commands import AzArgumentContext, CliCommandType

from azure.cli.command_modules.monitor._help import helps  # pylint: disable=unused-import


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
        from azure.cli.command_modules.monitor._exception_handler import monitor_exception_handler
        from azure.cli.core.profiles import ResourceType
        monitor_custom = CliCommandType(
            operations_tmpl='azure.cli.command_modules.monitor.custom#{}',
            exception_handler=monitor_exception_handler)
        super(MonitorCommandsLoader, self).__init__(cli_ctx=cli_ctx,
                                                    resource_type=ResourceType.MGMT_MONITOR,
                                                    argument_context_cls=MonitorArgumentContext,
                                                    custom_command_type=monitor_custom)

    def load_command_table(self, args):
        from azure.cli.command_modules.monitor.commands import load_command_table
        load_command_table(self, args)
        return self.command_table

    def load_arguments(self, command):
        from azure.cli.command_modules.monitor._params import load_arguments
        load_arguments(self, command)


COMMAND_LOADER_CLS = MonitorCommandsLoader
