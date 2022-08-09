# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import time
import json
import tempfile
from azure.cli.testsdk import (ScenarioTest, LiveScenarioTest, ResourceGroupPreparer, LogAnalyticsWorkspacePreparer)
from azure.cli.testsdk.base import execute
from azure.cli.core.mock import DummyCli
from azure.cli.testsdk.exceptions import CliTestError
from .preparers import (SqlVirtualMachinePreparer)


class VulnerabilityAssessmentForSqlTests(LiveScenarioTest):
    @ResourceGroupPreparer()
    @SqlVirtualMachinePreparer()
    @LogAnalyticsWorkspacePreparer()
    def test_va_sql_scenario(self, resource_group, resource_group_location, sqlvm, laworkspace):

        # Use prepared sql virtual machine and log analytics workspace to setup OMS agent with VA management pack
        _enable_intelligence_pack(resource_group, laworkspace)
        la_workspace_id = _get_log_analytics_workspace_id(resource_group, laworkspace)
        la_workspace_key = _get_log_analytics_workspace_key(resource_group, laworkspace)
        _set_vm_registry(resource_group, sqlvm)
        _install_oms_agent_on_vm(self, sqlvm, resource_group, la_workspace_id, la_workspace_key)
        _restart_monitoring_service(resource_group, sqlvm)  # Force start scan
        time.sleep(60 * 3)  # Graceful sleep

        # API parameters
        resource_id = _get_resource_id(resource_group, sqlvm)
        workspace_id = la_workspace_id
        server_name = "MSSQLSERVER"
        database_name = "master"

        # Test logic
        # Verify scan results arrived
        scan_summaries = self.cmd('az security va sql scans list --vm-resource-id {} --workspace-id {} --server-name {} --database-name {}'
                                  .format(resource_id, workspace_id, server_name, database_name)).get_output_in_json()
        selected_scan_summary = scan_id = scan_summaries["value"][0]
        scan_id = selected_scan_summary["name"]

        scan_summary = self.cmd('az security va sql scans show --vm-resource-id {} --workspace-id {} --server-name {} --database-name {} --scan-id {}'
                                .format(resource_id, workspace_id, server_name, database_name, scan_id)).get_output_in_json()
        self.assertEqual(selected_scan_summary, scan_summary)

        scan_results = self.cmd('az security va sql results list --vm-resource-id {} --workspace-id {} --server-name {} --database-name {} --scan-id {}'
                                .format(resource_id, workspace_id, server_name, database_name, scan_id)).get_output_in_json()
        scan_results_count = len(scan_results["value"])
        selected_scan_results = _get_scans_with_multiple_columns_in_results(scan_results)
        selected_scan_result = selected_scan_results[0]
        rule_id = selected_scan_result["name"]

        scan_result = self.cmd('az security va sql results show --vm-resource-id {} --workspace-id {} --server-name {} --database-name {} --scan-id {} --rule-id {}'
                               .format(resource_id, workspace_id, server_name, database_name, scan_id, rule_id)).get_output_in_json()
        self.assertEqual(selected_scan_result, scan_result)

        # Verify no baseline exists
        _assert_error('az security va sql baseline list --vm-resource-id {} --workspace-id {} --server-name {} --database-name {}'
                      .format(resource_id, workspace_id, server_name, database_name), error_reason='no baseline set')
        _assert_error('az security va sql baseline show --vm-resource-id {} --workspace-id {} --server-name {} --database-name {} --rule-id {}'
                      .format(resource_id, workspace_id, server_name, database_name, rule_id), error_reason='no baseline set')

        # Set baseline with latest results
        baseline_set_result = self.cmd('az security va sql baseline set --vm-resource-id {} --workspace-id {} --server-name {} --database-name {} --latest'
                                       .format(resource_id, workspace_id, server_name, database_name)).get_output_in_json()
        baseline_list_result = self.cmd('az security va sql baseline list --vm-resource-id {} --workspace-id {} --server-name {} --database-name {}'
                                        .format(resource_id, workspace_id, server_name, database_name)).get_output_in_json()
        self.assertEqual(scan_results_count, len(baseline_list_result["value"]))
        self.assertEqual(baseline_set_result["value"], baseline_list_result["value"])

        selected_baseline = [baseline for baseline in baseline_list_result["value"] if baseline["name"] == rule_id][0]
        baseline_show_result = self.cmd('az security va sql baseline show --vm-resource-id {} --workspace-id {} --server-name {} --database-name {} --rule-id {}'
                                        .format(resource_id, workspace_id, server_name, database_name, rule_id)).get_output_in_json()
        self.assertEqual(selected_baseline, baseline_show_result)

        # Delete an arbitrary baseline and verify it is deleted
        self.cmd('az security va sql baseline delete --vm-resource-id {} --workspace-id {} --server-name {} --database-name {} --rule-id {}'
                 .format(resource_id, workspace_id, server_name, database_name, rule_id))
        _assert_error('az security va sql baseline show --vm-resource-id {} --workspace-id {} --server-name {} --database-name {} --rule-id {}'
                      .format(resource_id, workspace_id, server_name, database_name, rule_id), error_reason='no baseline set (baseline deleted)')

        # Update baseline for single rule with latest results
        baseline_update_result = self.cmd('az security va sql baseline update --vm-resource-id {} --workspace-id {} --server-name {} --database-name {} --rule-id {} --latest'
                                          .format(resource_id, workspace_id, server_name, database_name, rule_id)).get_output_in_json()
        baseline_show_result = self.cmd('az security va sql baseline show --vm-resource-id {} --workspace-id {} --server-name {} --database-name {} --rule-id {}'
                                        .format(resource_id, workspace_id, server_name, database_name, rule_id)).get_output_in_json()
        self.assertEqual(baseline_update_result["properties"], baseline_show_result["properties"])

        # Update baseline for single rule with custom results
        baseline_input = _get_single_baseline_input(selected_scan_result)
        baseline_update_result = self.cmd('az security va sql baseline update --vm-resource-id {} --workspace-id {} --server-name {} --database-name {} --rule-id {} {}'
                                          .format(resource_id, workspace_id, server_name, database_name, rule_id, baseline_input)).get_output_in_json()
        baseline_show_result = self.cmd('az security va sql baseline show --vm-resource-id {} --workspace-id {} --server-name {} --database-name {} --rule-id {}'
                                        .format(resource_id, workspace_id, server_name, database_name, rule_id)).get_output_in_json()
        self.assertEqual(baseline_update_result["properties"], baseline_show_result["properties"])

        # Update baseline for multiple rule with custom results
        selected_scan_result_2 = selected_scan_results[1]
        rule_id_2 = selected_scan_result_2["name"]
        baseline_input = _get_multiple_baseline_input(rule_id, selected_scan_result, rule_id_2, selected_scan_result_2)
        baseline_set_result = self.cmd('az security va sql baseline set --vm-resource-id {} --workspace-id {} --server-name {} --database-name {} {}'
                                       .format(resource_id, workspace_id, server_name, database_name, baseline_input)).get_output_in_json()
        baseline_list_result = self.cmd('az security va sql baseline list --vm-resource-id {} --workspace-id {} --server-name {} --database-name {}'
                                        .format(resource_id, workspace_id, server_name, database_name)).get_output_in_json()
        baseline_show_result = self.cmd('az security va sql baseline show --vm-resource-id {} --workspace-id {} --server-name {} --database-name {} --rule-id {}'
                                        .format(resource_id, workspace_id, server_name, database_name, rule_id)).get_output_in_json()
        baseline_show_result_2 = self.cmd('az security va sql baseline show --vm-resource-id {} --workspace-id {} --server-name {} --database-name {} --rule-id {}'
                                          .format(resource_id, workspace_id, server_name, database_name, rule_id_2)).get_output_in_json()
        baseline_rule_1 = [baseline for baseline in baseline_list_result["value"] if baseline["name"] == rule_id][0]
        baseline_rule_2 = [baseline for baseline in baseline_list_result["value"] if baseline["name"] == rule_id_2][0]
        self.assertEqual(baseline_rule_1, baseline_show_result)
        self.assertEqual(baseline_rule_2, baseline_show_result_2)


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
    return len(query_results) > 0 and len(query_results[0]) > 1


def _get_single_baseline_input(scan_result):
    columns_count = len(scan_result["properties"]["queryResults"][0])
    two_line_baseline_template = '--baseline {} --baseline {}'
    line_template = 'word ' * columns_count
    line_template = line_template.rstrip()
    return two_line_baseline_template.format(line_template, line_template)


def _get_multiple_baseline_input(rule_id, scan_result_1, rule_id_2, scan_result_2):
    columns_count_1 = len(scan_result_1["properties"]["queryResults"][0])
    columns_count_2 = len(scan_result_2["properties"]["queryResults"][0])
    line_for_rule_1_template = 'word ' * columns_count_1
    line_for_rule_2_template = 'word ' * columns_count_2
    two_rule_baseline_template = '--baseline rule={} {} --baseline rule={} {}'
    return two_rule_baseline_template.format(rule_id, line_for_rule_1_template, rule_id_2, line_for_rule_2_template)


def _assert_error(cmd, error_reason):
    error_indicated = False
    try:
        execute(DummyCli(), cmd)
    except:
        error_indicated = True
    finally:
        if (not error_indicated):
            raise CliTestError('No error raised when expected. ' + error_reason)
