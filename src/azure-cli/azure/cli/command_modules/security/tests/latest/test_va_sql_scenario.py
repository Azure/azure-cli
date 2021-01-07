# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import time
import json
import tempfile
from azure_devtools.scenario_tests import AllowLargeResponse
from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer)
from azure.cli.testsdk.base import execute
from azure.cli.core.mock import DummyCli
from azure.cli.testsdk.exceptions import CliTestError
from .preparers import (SqlVirtualMachinePreparer, LogAnalyticsWorkspacePreparer)


class VulnerabilityAssessmentForSqlTests(ScenarioTest):
    @AllowLargeResponse()
    #@ResourceGroupPreparer()
    #@SqlVirtualMachinePreparer()
    #@LogAnalyticsWorkspacePreparer()
    def test_va_sql_scenario(self):

        resource_group = 'clitest'
        self.kwargs.update({
            'rg': resource_group
        })

        sqlvm = 'clisqlvmluu7td6'
        laworkspace = 'laworkspacez65x'

        # Use prepared sql virtual machine and log analytics workspace to setup OMS agent with VA management pack
        #_enable_intelligence_pack(resource_group, laworkspace)
        la_workspace_id = _get_log_analytics_workspace_id(resource_group, laworkspace)
        la_workspace_key = _get_log_analytics_workspace_key(resource_group, laworkspace)
        #_set_vm_registry(resource_group, sqlvm)
        #_install_oms_agent_on_vm(self, sqlvm, resource_group, la_workspace_id, la_workspace_key)
        #_restart_monitoring_service(resource_group, sqlvm)
        #time.sleep(60 * 3) # Safety sleep

        # API parameters
        resource_id = _get_resource_id(resource_group, sqlvm)
        workspace_id = la_workspace_id
        server_name = "MSSQLSERVER"
        database_name = "master"

        # Test logic
        scan_summaries = self.cmd('az security va sql scans list --vm-resource-id {} --workspace-id {} --server-name {} --database-name {}'
                                  .format(resource_id, workspace_id, server_name, database_name)).get_output_in_json()
        selected_scan_summary = scan_id = scan_summaries["value"][0]
        scan_id = selected_scan_summary["name"]

        scan_summary = self.cmd('az security va sql scans show --vm-resource-id {} --workspace-id {} --server-name {} --database-name {} --scan-id {}'
                                .format(resource_id, workspace_id, server_name, database_name, scan_id)).get_output_in_json()
        # assert scan_summary == selected_scan_summary

        scan_results = self.cmd('az security va sql results list --vm-resource-id {} --workspace-id {} --server-name {} --database-name {} --scan-id {}'
                                .format(resource_id, workspace_id, server_name, database_name, scan_id)).get_output_in_json()
        #scan_results_count = 
        selected_scan_results = _get_scans_with_multiple_columns_in_results(scan_results)
        selected_scan_result = selected_scan_results[0]
        rule_id = selected_scan_result["name"]

        scan_result = self.cmd('az security va sql results show --vm-resource-id {} --workspace-id {} --server-name {} --database-name {} --scan-id {} --rule-id {}'
                               .format(resource_id, workspace_id, server_name, database_name, scan_id, rule_id)).get_output_in_json()
        # assert scan_result = selected_scan_result

        # assert no baseline adjusted in scan result

        # assert error: baseline list (baseline not set)
        # assert error: baseline show for rule id (baseline not set)

        # baseline set latest
        # baseline list
        # assert equal number of baselines to scan results count

        # select baseline of rule_id
        # baseline show rule_id
        # assert baseline equals selected baseline

        # baseline delete
        # assert error: baseline show rule rule id (baseline deleted)

        # baseline update latest for rule_id
        # baseline show rule_id
        # assert baseline equals selected baseline

        # baseline update custom for rule_id
        # baseline show rule_id
        # assert baseline equals updated baseline

        # select two rule ids with more than one columns
        # baseline set custom for rule_id_1 rule_id_2
        # baseline list
        # baseline show rule_id_1
        # baseline show rule_id_2
        # assert baseline equal for rule_id_1
        # assert baseline equal for rule_id_2


def _enable_intelligence_pack(resource_group, workspace_name):
    intelligence_pack_name = 'SQLVulnerabilityAssessment'
    template = 'az monitor log-analytics workspace pack enable -n {} -g {} --workspace-name {}'
    execute(DummyCli(), template.format(intelligence_pack_name, resource_group, workspace_name))


def _set_vm_registry(resource_group, sqlvm):
    template = 'az vm run-command invoke --command-id {} --name {} -g {} --scripts \'New-Item -ItemType Directory -Force -Path C:\\Users\\admin123\\Desktop\\Va_Logs\' \
                \'New-Item -ItemType Directory -Force -Path C:\\Users\\admin123\\Desktop\\Setup_Logs\' \
                \'New-Item -Path HKLM:\\Software\\Microsoft\\AzureOperationalInsights\' \
                \'Set-ItemProperty -Path HKLM:\\Software\\Microsoft\\AzureOperationalInsights -Name SqlVulnerabilityAssessment_LogDirectoryPath -Value C:\\Users\\admin123\\Desktop\\Va_Logs\' \
                \'Set-ItemProperty -Path HKLM:\\Software\\Microsoft\\AzureOperationalInsights -Name SqlVulnerabilityAssessment_BypassHashCheck -Value true\' \
                \'Set-ItemProperty -Path HKLM:\\Software\\Microsoft\\AzureOperationalInsights -Name SqlVulnerabilityAssessment_TestMachine -Value true\''
    execute(DummyCli(), template.format('RunPowerShellScript', sqlvm, resource_group))


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


def _restart_monitoring_service(resource_group, sqlvm):
    template = 'az vm run-command invoke --command-id {} --name {} -g {} --scripts \'Start-Sleep -Seconds 60\' \
                \'Restart-Service HealthService\''
    execute(DummyCli(), template.format('RunPowerShellScript', sqlvm, resource_group))


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


def _get_resource_id(resource_group, sqlvm):
    resource_group_details = execute(DummyCli(), 'az group show -n {}'.format(resource_group)).get_output_in_json()
    resource_group_id = resource_group_details["id"]
    return f'{resource_group_id}/providers/Microsoft.Compute/VirtualMachines/{sqlvm}'


def _get_scans_with_multiple_columns_in_results(scan_results):
    return scan_results # TODO


def _assert_error():
    try:
        execute(DummyCli(), template.format(intelligence_pack_name, resource_group, workspace_name))
    except:
        pass