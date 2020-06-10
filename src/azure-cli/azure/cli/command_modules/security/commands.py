# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import CliCommandType
from ._client_factory import (cf_security_tasks,
                              cf_security_alerts,
                              cf_security_settings,
                              cf_security_contacts,
                              cf_security_auto_provisioning_settings,
                              cf_security_discovered_security_solutions,
                              cf_security_external_security_solutions,
                              cf_security_jit_network_access_policies,
                              cf_security_locations,
                              cf_security_pricings,
                              cf_security_topology,
                              cf_security_workspace_settings,
                              cf_security_advanced_threat_protection)


# pylint: disable=line-too-long
# pylint: disable=too-many-statements
def load_command_table(self, _):

    security_tasks_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.security.operations#TasksOperations.{}',
        client_factory=cf_security_tasks,
        operation_group='security_tasks'
    )

    security_alerts_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.security.operations#AlertsOperations.{}',
        client_factory=cf_security_alerts,
        operation_group='security_alerts'
    )

    security_settings_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.security.operations#SettingsOperations.{}',
        client_factory=cf_security_settings,
        operation_group='security_settings'
    )

    security_contacts_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.security.operations#SecurityContactsOperations.{}',
        client_factory=cf_security_contacts,
        operation_group='security_contacts'
    )

    security_auto_provisioning_settings_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.security.operations#AutoProvisioningSettingsOperations.{}',
        client_factory=cf_security_auto_provisioning_settings,
        operation_group='security_auto_provisioning_settings'
    )

    security_discovered_security_solutions_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.security.operations#DiscoveredSecuritySolutionsOperations.{}',
        client_factory=cf_security_discovered_security_solutions,
        operation_group='security_discovered_security_solutions'
    )

    security_external_security_solutions_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.security.operations#ExternalSecuritySolutionsOperations.{}',
        client_factory=cf_security_external_security_solutions,
        operation_group='security_external_security_solutions'
    )

    security_jit_network_access_policies_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.security.operations#JitNetworkAccessPoliciesOperations.{}',
        client_factory=cf_security_jit_network_access_policies,
        operation_group='security_jit_network_access_policies'
    )

    security_locations_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.security.operations#LocationsOperations.{}',
        client_factory=cf_security_locations,
        operation_group='security_locations'
    )

    security_pricings_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.security.operations#PricingsOperations.{}',
        client_factory=cf_security_pricings,
        operation_group='security_pricings'
    )

    security_topology_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.security.operations#TopologyOperations.{}',
        client_factory=cf_security_topology,
        operation_group='security_topology'
    )

    security_workspace_settings_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.security.operations#WorkspaceSettingsOperations.{}',
        client_factory=cf_security_workspace_settings,
        operation_group='security_workspace_settings'
    )

    security_advanced_threat_protection_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.security.operations#AdvancedThreatProtectionOperations.{}',
        client_factory=cf_security_advanced_threat_protection
    )

    with self.command_group('security task',
                            security_tasks_sdk,
                            client_factory=cf_security_tasks) as g:
        g.custom_command('list', 'list_security_tasks')
        g.custom_command('show', 'get_security_task')

    with self.command_group('security atp storage',
                            security_advanced_threat_protection_sdk,
                            client_factory=cf_security_advanced_threat_protection) as g:
        g.custom_command('show', 'get_atp_setting')
        g.custom_command('update', 'update_atp_setting')

    with self.command_group('security alert',
                            security_alerts_sdk,
                            client_factory=cf_security_alerts) as g:
        g.custom_command('list', 'list_security_alerts')
        g.custom_command('show', 'get_security_alert')
        g.custom_command('update', 'update_security_alert')

    with self.command_group('security setting',
                            security_settings_sdk,
                            client_factory=cf_security_settings) as g:
        g.custom_command('list', 'list_security_settings')
        g.custom_command('show', 'get_security_setting')

    with self.command_group('security contact',
                            security_contacts_sdk,
                            client_factory=cf_security_contacts) as g:
        g.custom_command('list', 'list_security_contacts')
        g.custom_command('show', 'get_security_contact')
        g.custom_command('create', 'create_security_contact')
        g.custom_command('delete', 'delete_security_contact')

    with self.command_group('security auto-provisioning-setting',
                            security_auto_provisioning_settings_sdk,
                            client_factory=cf_security_auto_provisioning_settings) as g:
        g.custom_command('list', 'list_security_auto_provisioning_settings')
        g.custom_command('show', 'get_security_auto_provisioning_setting')
        g.custom_command('update', 'update_security_auto_provisioning_setting')

    with self.command_group('security discovered-security-solution',
                            security_discovered_security_solutions_sdk,
                            client_factory=cf_security_discovered_security_solutions) as g:
        g.custom_command('list', 'list_security_discovered_security_solutions')
        g.custom_command('show', 'get_security_discovered_security_solution')

    with self.command_group('security external-security-solution',
                            security_external_security_solutions_sdk,
                            client_factory=cf_security_external_security_solutions) as g:
        g.custom_command('list', 'list_security_external_security_solutions')
        g.custom_command('show', 'get_security_external_security_solution')

    with self.command_group('security jit-policy',
                            security_jit_network_access_policies_sdk,
                            client_factory=cf_security_jit_network_access_policies) as g:
        g.custom_command('list', 'list_security_jit_network_access_policies')
        g.custom_command('show', 'get_security_jit_network_access_policy')

    with self.command_group('security location',
                            security_locations_sdk,
                            client_factory=cf_security_locations) as g:
        g.custom_command('list', 'list_security_locations')
        g.custom_command('show', 'get_security_location')

    with self.command_group('security pricing',
                            security_pricings_sdk,
                            client_factory=cf_security_pricings) as g:
        g.custom_command('list', 'list_security_pricings')
        g.custom_command('show', 'get_security_pricing')
        g.custom_command('create', 'create_security_pricing')

    with self.command_group('security topology',
                            security_topology_sdk,
                            client_factory=cf_security_topology) as g:
        g.custom_command('list', 'list_security_topology')
        g.custom_command('show', 'get_security_topology')

    with self.command_group('security workspace-setting',
                            security_workspace_settings_sdk,
                            client_factory=cf_security_workspace_settings) as g:
        g.custom_command('list', 'list_security_workspace_settings')
        g.custom_command('show', 'get_security_workspace_setting')
        g.custom_command('create', 'create_security_workspace_setting')
        g.custom_command('delete', 'delete_security_workspace_setting')

    with self.command_group('security', is_preview=True):
        pass
