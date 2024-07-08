# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import json
from azure.cli.command_modules.acs.azuremonitormetrics.constants import ALERTS_API, RULES_API
from azure.cli.command_modules.acs.azuremonitormetrics.recordingrules.common import truncate_rule_group_name
from knack.util import CLIError


# pylint: disable=line-too-long
def get_recording_rules_template(cmd, azure_monitor_workspace_resource_id):
    from azure.cli.core.util import send_raw_request
    headers = ['User-Agent=azuremonitormetrics.get_recording_rules_template']
    armendpoint = cmd.cli_ctx.cloud.endpoints.resource_manager
    url = f"{armendpoint}{azure_monitor_workspace_resource_id}/providers/microsoft.alertsManagement/alertRuleRecommendations?api-version={ALERTS_API}"
    r = send_raw_request(cmd.cli_ctx, "GET", url, headers=headers)
    data = json.loads(r.text)
    return data['value']


# pylint: disable=line-too-long
def put_rules(cmd, default_rule_group_id, default_rule_group_name, mac_region, cluster_resource_id, azure_monitor_workspace_resource_id, cluster_name, default_rules_template, url, enable_rules, i):
    from azure.cli.core.util import send_raw_request
    body = json.dumps({
        "id": default_rule_group_id,
        "name": default_rule_group_name,
        "type": "Microsoft.AlertsManagement/prometheusRuleGroups",
        "location": mac_region,
        "properties": {
            "scopes": [
                azure_monitor_workspace_resource_id,
                cluster_resource_id
            ],
            "enabled": enable_rules,
            "clusterName": cluster_name,
            "interval": "PT1M",
            "rules": default_rules_template[i]["properties"]["rulesArmTemplate"]["resources"][0]["properties"]["rules"]
        }
    })
    for _ in range(3):
        try:
            headers = ['User-Agent=azuremonitormetrics.put_rules.' + default_rule_group_name]
            send_raw_request(cmd.cli_ctx, "PUT", url,
                             body=body, headers=headers)
            break
        except CLIError as e:
            error = e
    else:
        raise error


# pylint: disable=line-too-long
def create_rules(cmd, cluster_subscription, cluster_resource_group_name, cluster_name, azure_monitor_workspace_resource_id, mac_region, raw_parameters):
    # limit rule group name to 260 characters
    # with urllib.request.urlopen("https://defaultrulessc.blob.core.windows.net/defaultrules/ManagedPrometheusDefaultRecordingRules.json") as url:
    #     default_rules_template = json.loads(url.read().decode())
    default_rules_template = get_recording_rules_template(cmd, azure_monitor_workspace_resource_id)
    default_rule_group_name = truncate_rule_group_name("NodeRecordingRulesRuleGroup-{0}".format(cluster_name))
    default_rule_group_id = "/subscriptions/{0}/resourceGroups/{1}/providers/Microsoft.AlertsManagement/prometheusRuleGroups/{2}".format(
        cluster_subscription,
        cluster_resource_group_name,
        default_rule_group_name
    )
    cluster_resource_id = \
        "/subscriptions/{0}/resourceGroups/{1}/providers/Microsoft.ContainerService/managedClusters/{2}".format(
            cluster_subscription,
            cluster_resource_group_name,
            cluster_name
        )
    url = "{0}{1}?api-version={2}".format(
        cmd.cli_ctx.cloud.endpoints.resource_manager,
        default_rule_group_id,
        RULES_API
    )
    put_rules(cmd, default_rule_group_id, default_rule_group_name, mac_region, cluster_resource_id, azure_monitor_workspace_resource_id, cluster_name, default_rules_template, url, True, 0)

    default_rule_group_name = truncate_rule_group_name("KubernetesRecordingRulesRuleGroup-{0}".format(cluster_name))
    default_rule_group_id = "/subscriptions/{0}/resourceGroups/{1}/providers/Microsoft.AlertsManagement/prometheusRuleGroups/{2}".format(
        cluster_subscription,
        cluster_resource_group_name,
        default_rule_group_name
    )
    url = "{0}{1}?api-version={2}".format(
        cmd.cli_ctx.cloud.endpoints.resource_manager,
        default_rule_group_id,
        RULES_API
    )
    put_rules(cmd, default_rule_group_id, default_rule_group_name, mac_region, cluster_resource_id, azure_monitor_workspace_resource_id, cluster_name, default_rules_template, url, True, 1)

    enable_windows_recording_rules = raw_parameters.get("enable_windows_recording_rules")

    if enable_windows_recording_rules is not True:
        enable_windows_recording_rules = False

    default_rule_group_name = truncate_rule_group_name("NodeRecordingRulesRuleGroup-Win-{0}".format(cluster_name))
    default_rule_group_id = "/subscriptions/{0}/resourceGroups/{1}/providers/Microsoft.AlertsManagement/prometheusRuleGroups/{2}".format(
        cluster_subscription,
        cluster_resource_group_name,
        default_rule_group_name
    )
    url = "{0}{1}?api-version={2}".format(
        cmd.cli_ctx.cloud.endpoints.resource_manager,
        default_rule_group_id,
        RULES_API
    )
    put_rules(cmd, default_rule_group_id, default_rule_group_name, mac_region, cluster_resource_id, azure_monitor_workspace_resource_id, cluster_name, default_rules_template, url, enable_windows_recording_rules, 2)

    default_rule_group_name = truncate_rule_group_name("NodeAndKubernetesRecordingRulesRuleGroup-Win-{0}".format(cluster_name))
    default_rule_group_id = "/subscriptions/{0}/resourceGroups/{1}/providers/Microsoft.AlertsManagement/prometheusRuleGroups/{2}".format(
        cluster_subscription,
        cluster_resource_group_name,
        default_rule_group_name
    )
    url = "{0}{1}?api-version={2}".format(
        cmd.cli_ctx.cloud.endpoints.resource_manager,
        default_rule_group_id,
        RULES_API
    )
    put_rules(cmd, default_rule_group_id, default_rule_group_name, mac_region, cluster_resource_id, azure_monitor_workspace_resource_id, cluster_name, default_rules_template, url, enable_windows_recording_rules, 3)
