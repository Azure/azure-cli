# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

from azure.cli.core.commands import CliCommandType
from ._client_factory import management_groups_client_factory, management_group_subscriptions_client_factory
from ._exception_handler import managementgroups_exception_handler

def load_command_table(self, _):
    def managementgroups_type(*args, **kwargs):
        return CliCommandType(*args, exception_handler=managementgroups_exception_handler, **kwargs)

    managementgroups_sdk = managementgroups_type(
        operations_tmpl='azure.mgmt.resource.managementgroups.operations.management_groups_operations#ManagementGroupsOperations.{}',
        client_factory=management_groups_client_factory
        )

    managementgroups_subscriptions_sdk = managementgroups_type(
        operations_tmpl='azure.mgmt.resource.managementgroups.operations.management_group_subscriptions_operations#ManagementGroupSubscriptionsOperations.{}',
        client_factory=management_group_subscriptions_client_factory
        )

    with self.command_group('managementgroups group', managementgroups_sdk) as g:
        g.custom_command('list', 'cli_managementgroups_group_list')
        g.custom_command('get', 'cli_managementgroups_group_get')
        g.custom_command('new', 'cli_managementgroups_group_new')
        g.custom_command('remove', 'cli_managementgroups_group_remove')
        g.custom_command('update', 'cli_managementgroups_group_update')

    with self.command_group('managementgroups subscription', managementgroups_subscriptions_sdk, client_factory=management_group_subscriptions_client_factory) as g:
        g.custom_command('new', 'cli_managementgroups_subscription_new')
        g.custom_command('remove', 'cli_managementgroups_subscription_remove')