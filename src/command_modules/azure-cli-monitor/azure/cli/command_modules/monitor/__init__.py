# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core import AzCommandsLoader
from azure.cli.core.commands import AzArgumentContext

from azure.cli.command_modules.monitor._help import helps  # pylint: disable=unused-import


# pylint: disable=line-too-long
class MonitorArgumentContext(AzArgumentContext):

    def resource_parameter_context(self, dest, arg_group=None, required=True, skip_validator=False):
        from azure.cli.command_modules.monitor.validators import get_target_resource_validator
        self.argument(dest, options_list='--resource', arg_group=arg_group, required=required,
                      validator=get_target_resource_validator(dest, required) if not skip_validator else None,
                      help="Name or ID of the target resource.")
        self.extra('namespace', options_list='--resource-namespace', arg_group=arg_group,
                   help="Target resource provider namespace.")
        self.extra('parent', options_list='--resource-parent', arg_group=arg_group,
                   help="Target resource parent path, if applicable.")
        self.extra('resource_type', options_list='--resource-type', arg_group=arg_group,
                   help="Target resource type. Can also accept namespace/type format "
                        "(Ex: 'Microsoft.Compute/virtualMachines)')")
        self.extra('resource_group_name', options_list=['--resource-group', '-g'], arg_group=arg_group)

    def resource_parameter(self, dest, arg_group=None, required=True):
        """ Helper method to add the extra parameters needed to support specifying name or ID for target resources. """
        from azure.cli.command_modules.monitor.validators import get_target_resource_validator
        self.argument(dest, options_list=['--{}'.format(dest)], arg_group=arg_group, required=required,
                      validator=get_target_resource_validator(dest, required, preserve_resource_group_parameter=True),
                      help="Name or ID of the target resource.")
        self.extra('namespace', options_list=['--{}-namespace'.format(dest)], arg_group=arg_group,
                   help="Target resource provider namespace.")
        self.extra('parent', options_list=['--{}-parent'.format(dest)], arg_group=arg_group,
                   help="Target resource parent path, if applicable.")
        self.extra('resource_type', options_list=['--{}-type'.format(dest)], arg_group=arg_group,
                   help="Target resource type. Can also accept namespace/type format "
                        "(Ex: 'Microsoft.Compute/virtualMachines)')")


class MonitorCommandsLoader(AzCommandsLoader):

    def __init__(self, cli_ctx=None):
        super(MonitorCommandsLoader, self).__init__(cli_ctx=cli_ctx,
                                                    min_profile='2017-03-10-profile',
                                                    argument_context_cls=MonitorArgumentContext)

    def load_command_table(self, args):
        from azure.cli.command_modules.monitor.commands import load_command_table
        load_command_table(self, args)
        return self.command_table

    def load_arguments(self, command):
        from azure.cli.command_modules.monitor._params import load_arguments
        load_arguments(self, command)


COMMAND_LOADER_CLS = MonitorCommandsLoader
