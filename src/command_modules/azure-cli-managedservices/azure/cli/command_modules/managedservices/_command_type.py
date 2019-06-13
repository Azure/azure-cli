# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import AzCommandGroup


class ManagedServicesCommandGroup(AzCommandGroup):
    def managedservices_custom(self, name, method_name=None, **kwargs):
        self._register_common_arguments(name, method_name, **kwargs)

    def _register_common_arguments(self, name, method_name=None, **kwargs):
        command = self.command_loader.command_table[self.custom_command(name, method_name, **kwargs)]

        group_name = 'ManagedServices'
        command.add_argument('api_version', required=False, default=None,
                             arg_group=group_name, help='The API Version to target.')
        command.add_argument('subscription', '--subscription', '-s', required=False, default=None,
                             arg_group=group_name, help='Optional, but can be used to override the default subscription.')

        if "assignment" in method_name:
            command.add_argument('resource_group_name', '--resource-group', '-g', arg_group=group_name,
                                 help='Optional. When provided the assignment will be created under the resource '
                                      'group scope. Ex: /subscriptions/id/resourceGroups/rgName/.')

