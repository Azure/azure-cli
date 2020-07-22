# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import CliCommandType
from azure.cli.command_modules.synapse._client_factory import cf_synapse


def get_custom_sdk(custom_module, client_factory):
    return CliCommandType(
        operations_tmpl='azure.cli.command_modules.synapse.operations.{}#'.format(custom_module) + '{}',
        client_factory=client_factory,
    )


def load_command_table(self, _):
    from azure.cli.core.commands import CliCommandType
    from ._client_factory import cf_synapse_client_workspace_factory
    from ._client_factory import cf_synapse_client_operations_factory
    from ._client_factory import cf_synapse_client_bigdatapool_factory
    from ._client_factory import cf_synapse_client_sqlpool_factory
    from ._client_factory import cf_synapse_client_ipfirewallrules_factory

    synapse_workspace_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.synapse.operations#WorkspacesOperations.{}',
        client_factory=cf_synapse_client_workspace_factory)

    synapse_operations_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.synapse.operations#Operations.{}',
        client_factory=cf_synapse_client_operations_factory)

    synapse_bigdatapool_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.synapse.operations#BigDataPoolsOperations.{}',
        client_factory=cf_synapse_client_bigdatapool_factory)

    synapse_sqlpool_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.synapse.operations#SqlPoolsOperations.{}',
        client_factory=cf_synapse_client_sqlpool_factory)

    synapse_firewallrules_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.synapse.operations#IpFirewallRulesOperations.{}',
        client_factory=cf_synapse_client_ipfirewallrules_factory)

    # Management Plane Commands --Workspace
    with self.command_group('synapse workspace', command_type=synapse_workspace_sdk,
                            custom_command_type=get_custom_sdk('workspace', cf_synapse_client_ipfirewallrules_factory),
                            client_factory=cf_synapse_client_workspace_factory) as g:
        g.show_command('show', 'get')
        g.custom_command('list', 'list_workspaces')
        g.custom_command('create', 'create_workspace', supports_no_wait=True)
        g.custom_command('update', 'update_workspace', supports_no_wait=True)
        g.custom_command('check-name', 'custom_check_name_availability',
                         command_type=synapse_operations_sdk,
                         client_factory=cf_synapse_client_operations_factory)
        g.command('delete', 'delete', confirmation=True, supports_no_wait=True)
        g.wait_command('wait')

    # Management Plane Commands --SparkPool
    with self.command_group('synapse spark pool', command_type=synapse_bigdatapool_sdk,
                            custom_command_type=get_custom_sdk('sparkpool', cf_synapse_client_ipfirewallrules_factory),
                            client_factory=cf_synapse_client_bigdatapool_factory) as g:
        g.custom_show_command('show', 'get_spark_pool')
        g.command('list', 'list_by_workspace')
        g.custom_command('create', 'create_spark_pool', supports_no_wait=True)
        g.custom_command('update', 'update_spark_pool', supports_no_wait=True)
        g.custom_command('delete', 'delete_spark_pool', confirmation=True, supports_no_wait=True)
        g.wait_command('wait')

    # Management Plane Commands --SqlPool
    with self.command_group('synapse sql pool', command_type=synapse_sqlpool_sdk,
                            custom_command_type=get_custom_sdk('sqlpool', cf_synapse_client_ipfirewallrules_factory),
                            client_factory=cf_synapse_client_sqlpool_factory) as g:
        g.show_command('show', 'get')
        g.command('list', 'list_by_workspace')
        g.custom_command('create', 'create_sql_pool', supports_no_wait=True)
        g.command('delete', 'delete', confirmation=True, supports_no_wait=True)
        g.custom_command('update', 'update_sql_pool')
        g.command('pause', 'pause')
        g.command('resume', 'resume')
        g.wait_command('wait')

    # Management Plane Commands --FirewallRule
    with self.command_group('synapse workspace firewall-rule', command_type=synapse_firewallrules_sdk,
                            custom_command_type=get_custom_sdk('workspace', cf_synapse_client_ipfirewallrules_factory),
                            client_factory=cf_synapse_client_ipfirewallrules_factory) as g:
        g.command('list', 'list_by_workspace')
        g.show_command('show', 'get')
        g.custom_command('create', 'create_firewall_rule', supports_no_wait=True)
        g.command('delete', 'delete', confirmation=True, supports_no_wait=True)
        g.wait_command('wait')

    with self.command_group('synapse', is_preview=True):
        pass
