# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from .._client_factory import cf_monitor
from ..util import _gen_guid
from azure.cli.core.commands.transform import _parse_id

def clone_existed_settings(cmd, client, source_resource=None, target_resource=None):
    monitor_client = cf_monitor(cmd.cli_ctx)
    alert_rules = list(monitor_client.metric_alerts.list_by_subscription())
    updated_alert_rules = []
    ErrorResponseException = cmd.get_models('ErrorResponseException', operation_group='metric_alerts')
    for alert_rule in alert_rules:
        if source_resource in alert_rule.scopes:
            try:
                alert_rule.scopes.append(target_resource)
                resource_group_name, name = _parse_id(alert_rule.id).values()
                alert_rule = monitor_client.metric_alerts.create_or_update(resource_group_name=resource_group_name, rule_name=name, parameters=alert_rule)
            except ErrorResponseException as ex:  # Create new alert rule
                if ex.response.status_code == 400:
                    alert_rule.scopes = [target_resource]
                    resource_group_name, name = _parse_id(target_resource).values()
                    name = "{}-{}".format(name, _gen_guid())
                    alert_rule = monitor_client.metric_alerts.create_or_update(resource_group_name=resource_group_name, rule_name=name, parameters=alert_rule)
            updated_alert_rules.append(alert_rule)
    return updated_alert_rules
