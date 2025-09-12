# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.command_modules.acs.azuremonitormetrics.constants import RULES_API
from azure.cli.command_modules.acs.azuremonitormetrics.recordingrules.common import truncate_rule_group_name


def delete_rule(cmd, cluster_subscription, cluster_resource_group_name, default_rule_group_name):
    from azure.cli.command_modules.acs._client_factory import get_resources_client
    resources = get_resources_client(cmd.cli_ctx, cmd.cli_ctx.data.get('subscription_id'))
    default_rule_group_id = (
        "/subscriptions/{0}/resourceGroups/{1}/providers/"
        "Microsoft.AlertsManagement/prometheusRuleGroups/{2}"
    ).format(
        cluster_subscription,
        cluster_resource_group_name,
        default_rule_group_name
    )
    resources.begin_delete_by_id(default_rule_group_id, RULES_API)


def delete_rules(cmd, cluster_subscription, cluster_resource_group_name, cluster_name):
    # limit rule group name to 260 characters
    delete_rule(
        cmd,
        cluster_subscription,
        cluster_resource_group_name,
        truncate_rule_group_name("NodeRecordingRulesRuleGroup-{0}".format(cluster_name))
    )
    delete_rule(
        cmd,
        cluster_subscription,
        cluster_resource_group_name,
        truncate_rule_group_name("KubernetesRecordingRulesRuleGroup-{0}".format(cluster_name))
    )
    delete_rule(
        cmd,
        cluster_subscription,
        cluster_resource_group_name,
        truncate_rule_group_name("NodeRecordingRulesRuleGroup-Win-{0}".format(cluster_name))
    )
    delete_rule(
        cmd,
        cluster_subscription,
        cluster_resource_group_name,
        truncate_rule_group_name("NodeAndKubernetesRecordingRulesRuleGroup-Win-{0}".format(cluster_name))
    )
    delete_rule(
        cmd,
        cluster_subscription,
        cluster_resource_group_name,
        truncate_rule_group_name("UXRecordingRulesRuleGroup - {0}".format(cluster_name))
    )
    delete_rule(
        cmd,
        cluster_subscription,
        cluster_resource_group_name,
        truncate_rule_group_name("UXRecordingRulesRuleGroup-Win - {0}".format(cluster_name))
    )
