# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from .._client_factory import cf_monitor
from ..util import _gen_guid
from azure.cli.core.commands.transform import _parse_id
from knack.log import get_logger
from knack.util import CLIError
from msrestazure.tools import parse_resource_id


logger = get_logger(__name__)


def clone_existed_settings(cmd, source_resource=None, target_resource=None):
    metrics_alert_rules = _clone_monitor_metrics_alerts(cmd, source_resource, target_resource)
    return metrics_alert_rules


def _clone_monitor_metrics_alerts(cmd, source_resource, target_resource):
    if not _is_resource_type_same_and_sub_same(source_resource, target_resource):
        raise CLIError('The target resource should be the same type with the source resource '
                       'and they are in the same subscription')
    monitor_client = cf_monitor(cmd.cli_ctx, subscription_id=parse_resource_id(source_resource)['subscription'])
    # we can only clone the alert rules belonging to the source subscription.
    alert_rules = list(monitor_client.metric_alerts.list_by_subscription())
    updated_alert_rules = []
    ErrorResponseException = cmd.get_models('ErrorResponseException', operation_group='metric_alerts')
    for alert_rule in alert_rules:
        if source_resource in alert_rule.scopes:
            if target_resource not in alert_rule.scopes:
                try:
                    alert_rule.scopes.append(target_resource)
                    resource_group_name, name = _parse_id(alert_rule.id).values()
                    alert_rule = monitor_client.metric_alerts.create_or_update(resource_group_name=resource_group_name,
                                                                               rule_name=name, parameters=alert_rule)
                except ErrorResponseException as ex:  # Create new alert rule
                    if ex.response.status_code == 400:
                        alert_rule.scopes = [target_resource]
                        resource_group_name, name = _parse_id(target_resource).values()
                        name = "{}-{}".format(name, _gen_guid())
                        alert_rule = monitor_client.metric_alerts.create_or_update(resource_group_name=resource_group_name,  # pylint: disable=line-too-long
                                                                                   rule_name=name,
                                                                                   parameters=alert_rule)
                    else:
                        raise ex
                updated_alert_rules.append(alert_rule)
            else:
                logger.warning('The target resource already has alert rule %s. '
                               'Skip cloning this one.', alert_rule.name)
    if not updated_alert_rules:
        return None
    return updated_alert_rules if len(updated_alert_rules) > 1 else updated_alert_rules[0]


def _is_resource_type_same_and_sub_same(source_resource, target_resource):
    source_dict = parse_resource_id(source_resource)
    target_dict = parse_resource_id(target_resource)
    same_rp = source_dict['namespace'] == target_dict['namespace'] and source_dict['type'] == target_dict['type']
    same_sub = source_dict['subscription'] == target_dict['subscription']
    return same_rp and same_sub
