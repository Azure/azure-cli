# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.command_modules.acs.azuremonitormetrics.constants import RULES_API


def delete_rule(cmd, cluster_subscription, cluster_resource_group_name, default_rule_group_name):
    from azure.cli.core.util import send_raw_request
    default_rule_group_id = \
        "/subscriptions/{0}/resourceGroups/{1}/providers/Microsoft.AlertsManagement/prometheusRuleGroups/{2}".format(
            cluster_subscription,
            cluster_resource_group_name,
            default_rule_group_name
        )
    headers = ['User-Agent=azuremonitormetrics.delete_rule.' + default_rule_group_name]
    url = "{0}{1}?api-version={2}".format(
        cmd.cli_ctx.cloud.endpoints.resource_manager,
        default_rule_group_id,
        RULES_API
    )
    send_raw_request(cmd.cli_ctx, "DELETE", url, headers=headers)


def delete_rules(cmd, cluster_subscription, cluster_resource_group_name, cluster_name):
    delete_rule(
        cmd,
        cluster_subscription,
        cluster_resource_group_name,
        "NodeRecordingRulesRuleGroup-{0}".format(cluster_name)
    )
    delete_rule(
        cmd,
        cluster_subscription,
        cluster_resource_group_name,
        "KubernetesRecordingRulesRuleGroup-{0}".format(cluster_name)
    )
    delete_rule(
        cmd,
        cluster_subscription,
        cluster_resource_group_name,
        "NodeRecordingRulesRuleGroup-Win-{0}".format(cluster_name)
    )
    delete_rule(
        cmd,
        cluster_subscription,
        cluster_resource_group_name,
        "NodeAndKubernetesRecordingRulesRuleGroup-Win-{0}".format(cluster_name)
    )
