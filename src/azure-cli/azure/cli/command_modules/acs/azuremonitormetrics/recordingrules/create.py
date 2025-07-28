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

    filtered_templates = [
        template for template in data.get('value', [])
        if template.get("properties", {}).get("alertRuleType", "").lower() == "microsoft.alertsmanagement/prometheusrulegroups" and isinstance(template.get("properties", {}).get("rulesArmTemplate", {}).get("resources"), list) and all(
            isinstance(rule, dict) and "record" in rule and "expression" in rule
            for resource in template["properties"]["rulesArmTemplate"]["resources"]
            if resource.get("type", "").lower() == "microsoft.alertsmanagement/prometheusrulegroups"
            for rule in resource.get("properties", {}).get("rules", [])
        )
    ]

    return filtered_templates


# pylint: disable=line-too-long
def put_rules(cmd, default_rule_group_id, default_rule_group_name, mac_region, cluster_resource_id, azure_monitor_workspace_resource_id, cluster_name, default_rules_template, url, enable_rules, i):
    from azure.cli.command_modules.acs._client_factory import get_resources_client
    resources = get_resources_client(cmd.cli_ctx, cmd.cli_ctx.data.get('subscription_id'))
    body = {
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
    }
    for _ in range(3):
        try:
            resources.begin_create_or_update_by_id(
                default_rule_group_id,
                url.split('api-version=')[1],
                body
            )
            break
        except Exception as e:
            raise CLIError(e)


# pylint: disable=line-too-long
def create_rules(cmd, cluster_subscription, cluster_resource_group_name, cluster_name, azure_monitor_workspace_resource_id, mac_region, raw_parameters):
    default_rules_template = get_recording_rules_template(cmd, azure_monitor_workspace_resource_id)

    cluster_resource_id = (
        f"/subscriptions/{cluster_subscription}/resourceGroups/{cluster_resource_group_name}/providers/Microsoft.ContainerService/managedClusters/{cluster_name}"
    )

    enable_windows_recording_rules = raw_parameters.get("enable_windows_recording_rules", False)

    for index, rule_template in enumerate(default_rules_template):
        rule_name = rule_template["name"]
        is_windows_rule = "win" in rule_name.lower()

        # Determine whether the rule group should be enabled:
        # - If the rule is a Windows rule AND windows recording rules are NOT enabled → disable the rule group (enable_rules = False)
        # - If the rule is a Windows rule AND windows recording rules are enabled → enable the rule group (enable_rules = True)
        # - If the rule is NOT a Windows rule (i.e., a Linux or general rule) → always enable the rule group (enable_rules = True)
        enable_rules = not (is_windows_rule and not enable_windows_recording_rules)

        rule_group_name = truncate_rule_group_name(f"{rule_template['name']}-{cluster_name}")
        rule_group_id = f"/subscriptions/{cluster_subscription}/resourceGroups/{cluster_resource_group_name}/providers/Microsoft.AlertsManagement/prometheusRuleGroups/{rule_group_name}"
        url = f"{cmd.cli_ctx.cloud.endpoints.resource_manager}{rule_group_id}?api-version={RULES_API}"

        put_rules(
            cmd,
            rule_group_id,
            rule_group_name,
            mac_region,
            cluster_resource_id,
            azure_monitor_workspace_resource_id,
            cluster_name,
            default_rules_template,
            url,
            enable_rules,
            index
        )
