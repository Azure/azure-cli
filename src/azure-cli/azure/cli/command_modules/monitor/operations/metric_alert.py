# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=too-many-locals, line-too-long, protected-access, too-many-nested-blocks
# Class MetricsAlertUpdate moved to operations/latest/monitor/metrics/alert/_update.py

from knack.log import get_logger

logger = get_logger(__name__)

_metric_alert_dimension_prefix = '_where_'


def create_metric_alert(cmd, resource_group_name, rule_name, scopes, condition, disabled=False, description=None,
                        tags=None, actions=None, severity=2, window_size='5m', evaluation_frequency='1m',
                        auto_mitigate=None, target_resource_type=None, target_resource_region=None):
    from azure.cli.command_modules.monitor.aaz.latest.monitor.metrics.alert._create import Create
    from azure.cli.core.azclierror import InvalidArgumentValueError
    from msrest.serialization import Serializer

    # generate metadata for the conditions
    is_dynamic_threshold_criterion = False
    all_of = []
    single_all_of = []
    for i, cond in enumerate(condition):
        if "dynamic" in cond:
            is_dynamic_threshold_criterion = True
            item = cond["dynamic"]
            item["name"] = f"cond{i}"
            props = {
                "alert_sensitivity": item.pop("alert_sensitivity", None),
                "failing_periods": item.pop("failing_periods", None),
                "operator": item.pop("operator", None),
                "ignore_data_before": Serializer.serialize_iso(dt) if (dt := item.pop("ignore_data_before", None)) else None
            }

            all_of.append({**item, **{"dynamic_threshold_criterion": props}})
            single_all_of.append({**item, **props})
        else:
            item = cond["static"]
            item["name"] = f"cond{i}"
            props = {
                "operator": item.pop("operator", None),
                "threshold": item.pop("threshold", None)
            }

            all_of.append({**item, **{"static_threshold_criterion": props}})
            single_all_of.append({**item, **props})

    criteria = None
    resource_type, scope_type = _parse_resource_and_scope_type(scopes)
    if scope_type in ['resource_group', 'subscription']:
        if target_resource_type is None or target_resource_region is None:
            raise InvalidArgumentValueError('--target-resource-type and --target-resource-region must be provided.')
        criteria = {"microsoft_azure_monitor_multiple_resource_multiple_metric_criteria": {"all_of": all_of}}
    else:
        if len(scopes) == 1:
            if not is_dynamic_threshold_criterion:
                criteria = {"microsoft_azure_monitor_single_resource_multiple_metric_criteria": {"all_of": single_all_of}}
            else:
                criteria = {"microsoft_azure_monitor_multiple_resource_multiple_metric_criteria": {"all_of": all_of}}
        else:
            criteria = {"microsoft_azure_monitor_multiple_resource_multiple_metric_criteria": {"all_of": all_of}}
            target_resource_type = resource_type
            target_resource_region = target_resource_region if target_resource_region else 'global'

    return Create(cli_ctx=cmd.cli_ctx)(command_args={
        'resource_group': resource_group_name,
        'name': rule_name,
        'description': description,
        'severity': severity,
        'enabled': not disabled,
        'scopes': scopes,
        'evaluation_frequency': evaluation_frequency,
        'window_size': window_size,
        'criteria': criteria,
        'target_resource_type': target_resource_type,
        'target_resource_region': target_resource_region,
        'actions': actions,
        'tags': tags,
        'location': 'global',
        'auto_mitigate': auto_mitigate
    })


def create_metric_alert_dimension(dimension_name, value_list, operator=None):
    values = ' or '.join(value_list)
    return '{} {} {} {}'.format(_metric_alert_dimension_prefix, dimension_name, operator, values)


def create_metric_alert_condition(condition_type, aggregation, metric_name, operator, metric_namespace='',
                                  dimension_list=None, threshold=None, alert_sensitivity=None,
                                  number_of_evaluation_periods=None, min_failing_periods_to_alert=None,
                                  ignore_data_before=None, skip_metric_validation=None):
    if metric_namespace:
        metric_namespace += '.'
    condition = "{} {}'{}' {} ".format(aggregation, metric_namespace, metric_name, operator)
    if condition_type == 'static':
        condition += '{} '.format(threshold)
    elif condition_type == 'dynamic':
        dynamics = 'dynamic {} {} of {} '.format(
            alert_sensitivity, min_failing_periods_to_alert, number_of_evaluation_periods)
        if ignore_data_before:
            dynamics += 'since {} '.format(ignore_data_before)
        condition += dynamics
    else:
        raise NotImplementedError()

    if dimension_list:
        dimensions = ' '.join([t for t in dimension_list if t.strip()])
        if dimensions.startswith(_metric_alert_dimension_prefix):
            dimensions = [t for t in dimensions.split(_metric_alert_dimension_prefix) if t]
            dimensions = 'where' + 'and'.join(dimensions)
        condition += dimensions

    if skip_metric_validation:
        condition += ' with skipmetricvalidation'

    return condition.strip()


def _parse_action_removals(actions):
    """ Separates the combined list of keys to remove into webhooks and emails. """
    flattened = list({x for sublist in actions for x in sublist})
    emails = []
    webhooks = []
    for item in flattened:
        if item.startswith('http://') or item.startswith('https://'):
            webhooks.append(item)
        else:
            emails.append(item)
    return emails, webhooks


def _parse_resource_and_scope_type(scopes):
    from azure.mgmt.core.tools import parse_resource_id
    from azure.cli.core.azclierror import InvalidArgumentValueError

    if not scopes:
        raise InvalidArgumentValueError('scopes cannot be null.')

    namespace = ''
    resource_type = ''
    scope_type = None

    def validate_scope(item_namespace, item_resource_type, item_scope_type):
        if namespace != item_namespace or resource_type != item_resource_type or scope_type != item_scope_type:
            raise InvalidArgumentValueError('Multiple scopes should be the same resource type.')

    def store_scope(item_namespace, item_resource_type, item_scope_type):
        nonlocal namespace
        nonlocal resource_type
        nonlocal scope_type
        namespace = item_namespace
        resource_type = item_resource_type
        scope_type = item_scope_type

    def parse_one_scope_with_action(scope, operation_on_scope):
        result = parse_resource_id(scope)
        if 'namespace' in result and 'resource_type' in result:
            resource_types = [result['type']]
            child_idx = 1
            while 'child_type_{}'.format(child_idx) in result:
                resource_types.append(result['child_type_{}'.format(child_idx)])
                child_idx += 1
            operation_on_scope(result['namespace'], '/'.join(resource_types), 'resource')
        elif 'resource_group' in result:  # It's a resource group.
            operation_on_scope('', '', 'resource_group')
        elif 'subscription' in result:  # It's a subscription.
            operation_on_scope('', '', 'subscription')
        else:
            raise InvalidArgumentValueError('Scope must be a valid resource id.')

    # Store the resource type and scope type from first scope
    parse_one_scope_with_action(scopes[0], operation_on_scope=store_scope)
    # Validate the following scopes
    for item in scopes:
        parse_one_scope_with_action(item, operation_on_scope=validate_scope)

    return namespace + '/' + resource_type, scope_type
