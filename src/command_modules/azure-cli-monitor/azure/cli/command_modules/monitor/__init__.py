# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core import AzCommandsLoader
from azure.cli.core.commands import AzArgumentContext, CliCommandType

from azure.cli.command_modules.monitor._help import helps  # pylint: disable=unused-import


class MonitorArgumentContext(AzArgumentContext):
    def resource_parameter(self, dest, arg_group=None, required=True):
        """ Helper method to add the extra parameters needed to support specifying name or ID for target resources. """
        from .validators import get_target_resource_validator

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

    def resource_parameter_context(self, dest, arg_group=None, required=True):
        from .validators import get_target_resource_validator

        self.argument(dest, options_list='--resource', arg_group=arg_group, required=required,
                      validator=get_target_resource_validator(dest, required),
                      help="Name or ID of the target resource.")
        self.extra('namespace', options_list='--resource-namespace', arg_group=arg_group,
                   help="Target resource provider namespace.")
        self.extra('parent', options_list='--resource-parent', arg_group=arg_group,
                   help="Target resource parent path, if applicable.")
        self.extra('resource_type', options_list='--resource-type', arg_group=arg_group,
                   help="Target resource type. Can also accept namespace/type format "
                        "(Ex: 'Microsoft.Compute/virtualMachines)')")
        self.extra('resource_group_name', options_list=('--resource-group', '-g'), arg_group='Target Resource')


class MonitorCommandsLoader(AzCommandsLoader):
    def __init__(self, cli_ctx=None):
        super(MonitorCommandsLoader, self).__init__(cli_ctx=cli_ctx,
                                                    argument_context_cls=MonitorArgumentContext)

    def monitor_command_group(self, name, client_factory, sdk_module=None, sdk_class=None, custom_module=None,
                              **kwargs):
        command_type = CliCommandType(
            operations_tmpl='azure.mgmt.monitor.operations.{}#{}.'.format(sdk_module, sdk_class) + '{}',
            client_factory=client_factory) if (sdk_module and sdk_class) else None
        custom_command_type = CliCommandType(
            operations_tmpl='azure.cli.command_modules.monitor.operations.{}#'.format(custom_module) + '{}',
            client_factory=client_factory) if custom_module else None

        return self.command_group(name, command_type=command_type, custom_command_type=custom_command_type, **kwargs)

    def load_command_table(self, args):
        from azure.cli.command_modules.monitor.commands import load_command_table
        load_command_table(self, args)

        return self.command_table

    def load_arguments(self, command):
        from azure.cli.command_modules.monitor.params import load_arguments
        load_arguments(self, command)

    @staticmethod
    def _get_sdk_path(sdk_module, sdk_class):
        return 'azure.mgmt.monitor.operations.{}#{}.'.format(sdk_module, sdk_class) + '{}'

    @staticmethod
    def _get_custom_module_path(name):
        return 'azure.cli.command_modules.monitor.operations.{}#'.format(name) + '{}' if name else None


COMMAND_LOADER_CLS = MonitorCommandsLoader
