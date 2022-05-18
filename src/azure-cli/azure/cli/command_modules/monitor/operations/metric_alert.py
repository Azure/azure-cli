# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=too-many-locals

from azure.cli.command_modules.monitor.util import get_operator_map, get_aggregation_map
from knack.log import get_logger

logger = get_logger(__name__)

_metric_alert_dimension_prefix = '_where_'


def create_metric_alert(client, resource_group_name, rule_name, scopes, condition, disabled=False, description=None,
                        tags=None, actions=None, severity=2, window_size='5m', evaluation_frequency='1m',
                        auto_mitigate=None, target_resource_type=None, target_resource_region=None):
    from azure.mgmt.monitor.models import (MetricAlertResource,
                                           MetricAlertSingleResourceMultipleMetricCriteria,
                                           MetricAlertMultipleResourceMultipleMetricCriteria,
                                           DynamicMetricCriteria)
    from azure.cli.core import CLIError
    # generate names for the conditions
    for i, cond in enumerate(condition):
        cond.name = 'cond{}'.format(i)
    criteria = None
    resource_type, scope_type = _parse_resource_and_scope_type(scopes)
    if scope_type in ['resource_group', 'subscription']:
        if target_resource_type is None or target_resource_region is None:
            raise CLIError('--target-resource-type and --target-resource-region must be provided.')
        criteria = MetricAlertMultipleResourceMultipleMetricCriteria(all_of=condition)
    else:
        if len(scopes) == 1:
            is_dynamic_threshold_criterion = False
            for v in condition:
                if isinstance(v, DynamicMetricCriteria):
                    is_dynamic_threshold_criterion = True
            if not is_dynamic_threshold_criterion:
                criteria = MetricAlertSingleResourceMultipleMetricCriteria(all_of=condition)
            else:
                criteria = MetricAlertMultipleResourceMultipleMetricCriteria(all_of=condition)
        else:
            criteria = MetricAlertMultipleResourceMultipleMetricCriteria(all_of=condition)
            target_resource_type = resource_type
            target_resource_region = target_resource_region if target_resource_region else 'global'

    kwargs = {
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
    }
    return client.create_or_update(resource_group_name, rule_name, MetricAlertResource(**kwargs))


def update_metric_alert(instance, scopes=None, description=None, enabled=None, tags=None,
                        severity=None, window_size=None, evaluation_frequency=None, auto_mitigate=None,
                        add_actions=None, remove_actions=None, add_conditions=None, remove_conditions=None):
    if scopes is not None:
        instance.scopes = scopes
    if description is not None:
        instance.description = description
    if enabled is not None:
        instance.enabled = enabled
    if tags is not None:
        instance.tags = tags
    if severity is not None:
        instance.severity = severity
    if window_size is not None:
        instance.window_size = window_size
    if evaluation_frequency is not None:
        instance.evaluation_frequency = evaluation_frequency
    if auto_mitigate is not None:
        instance.auto_mitigate = auto_mitigate

    # process action removals
    if remove_actions is not None:
        instance.actions = [x for x in instance.actions if x.action_group_id.lower() not in remove_actions]

    # process action additions
    if add_actions is not None:
        add_action_ids = {x.action_group_id.lower() for x in add_actions}
        instance.actions = [x for x in instance.actions if x.action_group_id.lower() not in add_action_ids]
        instance.actions.extend(add_actions)

    # process condition removals
    if remove_conditions is not None:
        instance.criteria.all_of = [x for x in instance.criteria.all_of if x.name not in remove_conditions]

    def _get_next_name():
        i = 0
        while True:
            possible_name = 'cond{}'.format(i)
            match = next((x for x in instance.criteria.all_of if x.name == possible_name), None)
            if match:
                i = i + 1
                continue
            return possible_name

    # process condition additions
    if add_conditions is not None:
        for condition in add_conditions:
            condition.name = _get_next_name()
            instance.criteria.all_of.append(condition)

    return instance


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


def list_metric_alerts(client, resource_group_name=None):
    if resource_group_name:
        return client.list_by_resource_group(resource_group_name)
    return client.list_by_subscription()


def _parse_actions(actions):
    """ Actions come in as a combined list. This method separates the webhook actions into a
        separate collection and combines any number of email actions into a single email collection
        and a single value for `email_service_owners`. If any email action contains a True value
        for `send_to_service_owners` then it is assumed the entire value should be True. """
    from azure.mgmt.monitor.models import RuleEmailAction, RuleWebhookAction
    actions = actions or []
    email_service_owners = None
    webhooks = [x for x in actions if isinstance(x, RuleWebhookAction)]
    custom_emails = set()
    for action in actions:
        if isinstance(action, RuleEmailAction):
            if action.send_to_service_owners:
                email_service_owners = True
            custom_emails = custom_emails | set(action.custom_emails)
    return list(custom_emails), webhooks, email_service_owners


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
