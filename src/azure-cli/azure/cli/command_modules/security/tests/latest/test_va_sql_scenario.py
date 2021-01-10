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
    def test_va_sql_scenario(self): # , resource_group, resource_group_location, sqlvm, laworkspace

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
        scan_results_count = scan_results["value"].count()
        selected_scan_results = _get_scans_with_multiple_columns_in_results(scan_results)
        selected_scan_result = selected_scan_results[0]
        rule_id = selected_scan_result["properties"]["ruleId"]

        scan_result = self.cmd('az security va sql results show --vm-resource-id {} --workspace-id {} --server-name {} --database-name {} --scan-id {} --rule-id {}'
                               .format(resource_id, workspace_id, server_name, database_name, scan_id, rule_id)).get_output_in_json()
        # assert scan_result = selected_scan_result
        # assert no baseline adjusted in scan result

        _assert_error('az security va sql baseline list --vm-resource-id {} --workspace-id {} --server-name {} --database-name {}'
                      .format(resource_id, workspace_id, server_name, database_name), error_reason='no baseline set')
        _assert_error('az security va sql baseline show --vm-resource-id {} --workspace-id {} --server-name {} --database-name {} --rule-id {}'
                      .format(resource_id, workspace_id, server_name, database_name, rule_id), error_reason='no baseline set')

        baseline_set_result = self.cmd('az security va sql baseline set --vm-resource-id {} --workspace-id {} --server-name {} --database-name {} --latest'
                                       .format(resource_id, workspace_id, server_name, database_name, scan_id, rule_id)).get_output_in_json()
        baseline_list_result = self.cmd('az security va sql baseline list --vm-resource-id {} --workspace-id {} --server-name {} --database-name {}'
                                        .format(resource_id, workspace_id, server_name, database_name)).get_output_in_json()
        # assert equal number of baselines to scan results count
        # assert equal number of baselines_set_result to baseline_list_result

        # selected_baseline = select baseline of rule_id
        baseline_show_result = self.cmd('az security va sql baseline show --vm-resource-id {} --workspace-id {} --server-name {} --database-name {} --rule-id {}'
                                        .format(resource_id, workspace_id, server_name, database_name, rule_id)).get_output_in_json()
        # assert baseline equals selected baseline

        self.cmd('az security va sql baseline delete --vm-resource-id {} --workspace-id {} --server-name {} --database-name {} --rule-id {}'
                 .format(resource_id, workspace_id, server_name, database_name, rule_id)).get_output_in_json()
        _assert_error('az security va sql baseline show --vm-resource-id {} --workspace-id {} --server-name {} --database-name {} --rule-id {}'
                      .format(resource_id, workspace_id, server_name, database_name, rule_id), error_reason='no baseline set (baseline deleted)')

        baseline_update_result = self.cmd('az security va sql baseline update --vm-resource-id {} --workspace-id {} --server-name {} --database-name {} --rule-id {} --latest'
                                         .format(resource_id, workspace_id, server_name, database_name, scan_id, rule_id)).get_output_in_json()
        baseline_show_result = self.cmd('az security va sql baseline show --vm-resource-id {} --workspace-id {} --server-name {} --database-name {} --rule-id {}'
                                        .format(resource_id, workspace_id, server_name, database_name, rule_id)).get_output_in_json()
        # assert baseline equals selected baseline

        baseline_input = _get_baseline_input(selected_scan_result)
        baseline_update_result = self.cmd('az security va sql baseline update --vm-resource-id {} --workspace-id {} --server-name {} --database-name {} --rule-id {} {}'
                                          .format(resource_id, workspace_id, server_name, database_name, scan_id, rule_id, baseline_input)).get_output_in_json()
        baseline_show_result = self.cmd('az security va sql baseline show --vm-resource-id {} --workspace-id {} --server-name {} --database-name {} --rule-id {}'
                                        .format(resource_id, workspace_id, server_name, database_name, rule_id)).get_output_in_json()
        # assert baseline equals updated baseline

        selected_scan_result_2 = selected_scan_results[1]
        rule_id_2 = selected_scan_result_2["name"]
        baseline_input = _get_baseline_input(selected_scan_result, selected_scan_result_2)
        baseline_set_result = self.cmd('az security va sql baseline set --vm-resource-id {} --workspace-id {} --server-name {} --database-name {} {}'
                                       .format(resource_id, workspace_id, server_name, database_name, scan_id, rule_id, baseline_input)).get_output_in_json()
        baseline_list_result = self.cmd('az security va sql baseline list --vm-resource-id {} --workspace-id {} --server-name {} --database-name {}'
                                .format(resource_id, workspace_id, server_name, database_name)).get_output_in_json()
        baseline_show_result = self.cmd('az security va sql baseline show --vm-resource-id {} --workspace-id {} --server-name {} --database-name {} --rule-id {}'
                                        .format(resource_id, workspace_id, server_name, database_name, rule_id)).get_output_in_json()
        baseline_show_result_2 = self.cmd('az security va sql baseline show --vm-resource-id {} --workspace-id {} --server-name {} --database-name {} --rule-id {}'
                                        .format(resource_id, workspace_id, server_name, database_name, rule_id_2)).get_output_in_json()
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
    return [scan for scan in scan_results["value"] if _has_multiple_columns(scan["properties"]["queryResults"])]


def _has_multiple_columns(query_results):
    return query_results.count() > 0 and query_results[0].count() > 1


def _get_baseline_input(scan_result):
    columns_count = scan_result["properties"]["queryResults"][0].count()
    return "--baseline"


def _get_baseline_input(scan_result_1, scan_result_2):
    columns_count_1 = scan_result_1["properties"]["queryResults"][0].count()
    columns_count_2 = scan_result_2["properties"]["queryResults"][0].count()
    return "--baseline"

def _assert_error(cmd, error_reason):
    error_indicated = False
    try:
        execute(DummyCli(), cmd)
    except:
        error_indicated = True
    finally:
        if (not error_indicated):
            raise CliTestError('No error raised when expected. ' + error_reason)