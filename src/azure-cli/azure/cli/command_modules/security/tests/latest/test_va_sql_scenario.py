# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import tempfile
from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer)
from azure.cli.testsdk.base import execute
from azure.cli.core.mock import DummyCli
from azure.cli.testsdk.exceptions import CliTestError
from .preparers import (SqlVirtualMachinePreparer, LogAnalyticsWorkspacePreparer)


class VulnerabilityAssessmentForSqlTests(ScenarioTest):
    @ResourceGroupPreparer()
    @SqlVirtualMachinePreparer()
    @LogAnalyticsWorkspacePreparer()
    def test_va_sql_scenario(self, resource_group, resource_group_location, sqlvm, laworkspace):
        # Use prepared sql virtual machine and log analytics workspace to setup OMS agent with VA management pack
        _enable_intelligence_pack(resource_group, laworkspace)
        workspace_id = _get_log_analytics_workspace_id(resource_group, laworkspace)
        workspace_key = _get_log_analytics_workspace_key(resource_group, laworkspace)
        _install_oms_agent_on_vm(self, sqlvm, resource_group, workspace_id, workspace_key)
        subscription_id = 'subscription'
        server_name = "server"
        database_name = "database"
        resource_id = _get_resource_id(subscription_id, resource_group, sqlvm)

        # Finished setup, start test logic
        pass


def _enable_intelligence_pack(resource_group, workspace_name):
    intelligence_pack_name = 'SQLVulnerabilityAssessment'
    template = 'az monitor log-analytics workspace pack enable -n {} -g {} --workspace-name {}'
    execute(DummyCli(), template.format(intelligence_pack_name, resource_group, workspace_name))


def _install_oms_agent_on_vm(self, vm_name, resource_group, workspace_id, workspace_key):
    public_config_file = _get_config_file('workspaceId', workspace_id)
    protected_config_file = _get_config_file('workspaceKey', workspace_key)
    self.kwargs.update({
        'vm': vm_name,
        'oms_publisher': 'Microsoft.EnterpriseCloud.Monitoring',
        'oms_extension': 'MicrosoftMonitoringAgent',
        'oms_version': '1.0',
        'public_config': public_config_file,
        'protected_config': protected_config_file
    })

    self.cmd('vm extension set --vm-name {vm} --resource-group {rg} \
                               -n {oms_extension} --publisher {oms_publisher} --version {oms_version}  \
                               --settings "{public_config}" --protected-settings "{protected_config}" --force-update')


def _get_log_analytics_workspace_id(resource_group, workspace_name):
    template = 'az monitor log-analytics workspace show --resource-group {} --workspace-name {}'
    workspace_details = execute(DummyCli(), template.format(resource_group, workspace_name)).get_output_in_json()
    return workspace_details["customerId"]


def _get_log_analytics_workspace_key(resource_group, workspace_name):
    template = 'az monitor log-analytics workspace get-shared-keys --resource-group {} --workspace-name {}'
    shared_keys = execute(DummyCli(), template.format(resource_group, workspace_name)).get_output_in_json()
    return shared_keys["primarySharedKey"]


def _get_config_file(key, value):
    config = {}
    config[key] = value
    _, config_file = tempfile.mkstemp()
    with open(config_file, 'w') as outfile:
        json.dump(config, outfile)
    return config_file


def _get_resource_id(subscription_id, resource_group, sqlvm):
    return f'subscriptions/{subscription_id}/ResourceGroups/{resource_group}/providers/Microsoft.Compute/VirtualMachines/{sqlvm}'
