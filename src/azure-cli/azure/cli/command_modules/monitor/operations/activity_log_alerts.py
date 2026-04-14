# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=protected-access, line-too-long


def _get_alert_settings_for_alert(cmd, resource_group_name, activity_log_alert_name, throw_if_missing=True):
    from azure.core.exceptions import HttpResponseError
    from azure.cli.core.azclierror import ValidationError
    from ..aaz.latest.monitor.activity_log.alert._show import Show as ActivityLogAlertGet
    try:
        return ActivityLogAlertGet(cli_ctx=cmd.cli_ctx)(command_args={
            "resource_group": resource_group_name,
            "activity_log_alert_name": activity_log_alert_name
        })
    except HttpResponseError as ex:
        if ex.status_code == 404:
            if throw_if_missing:
                raise ValidationError('Can\'t find activity log alert {} in resource group {}.'.format(
                    activity_log_alert_name, resource_group_name))
            return None
        raise ValidationError(ex.message)


# pylint: disable=inconsistent-return-statements
def _normalize_condition_for_alert(condition_instance):
    if isinstance(condition_instance, str):
        try:
            field, value = condition_instance.split('=')
            condition = {
                "field": field,
                "equals": value,
            }
            return '{}={}'.format(field.lower(), value), condition
        except ValueError:
            # too many values to unpack or not enough values to unpack
            raise ValueError('Condition "{}" does not follow format FIELD=VALUE'.format(condition_instance))


def process_condition_parameter_for_alert(args):
    from azure.cli.core.aaz import has_value
    from azure.cli.core.azclierror import ValidationError

    if not has_value(args.condition):
        return
    expression = args.condition.to_serialized_data()
    error = 'incorrect usage: --condition requires an expression in the form of FIELD=VALUE[ and FIELD=VALUE...]'

    if len(expression) == 1:
        expression = [each.strip() for each in expression[0].split(' ')]
    elif isinstance(expression, list):
        expression = [each.strip() for each in expression]
    else:
        raise ValidationError(error)

    if len(expression) == 0 or not len(expression) % 2:
        raise ValidationError(error)

    # This is a temporary approach built on the assumption that there is only AND operators. Eventually, a proper
    # YACC will be created to parse complex condition expression.

    # Ensure all the string at even options are AND operator
    operators = [expression[i] for i in range(1, len(expression), 2)]
    if any(op != 'and' for op in operators):
        raise ValidationError(error)

    # Pick the strings at odd position and convert them into condition leaf.
    conditions = dict(_normalize_condition_for_alert(expression[i]) for i in range(0, len(expression), 2))
    for cond in list(conditions.values()):
        args.all_of.append(cond)


def process_webhook_properties(args):
    from azure.cli.core.aaz import has_value

    result = {}
    if not has_value(args.webhook_properties_list):
        return result
    for each in args.webhook_properties_list:

        if has_value(each):
            if '=' in each.to_serialized_data():
                key, value = each.to_serialized_data().split('=', 1)
            else:
                key, value = each, ''
            result[key] = value
    return result


def normalize_names(cli_ctx, resource_names, resource_group, namespace, resource_type):
    """Normalize a group of resource names. Returns a set of resource ids. Throws if any of the name can't be correctly
    converted to a resource id."""
    from azure.mgmt.core.tools import is_valid_resource_id, resource_id
    from azure.cli.core.commands.client_factory import get_subscription_id

    rids = set()
    # normalize the action group ids
    for name in resource_names:
        if is_valid_resource_id(name):
            rids.add(name)
        else:
            rid = resource_id(subscription=get_subscription_id(cli_ctx),
                              resource_group=resource_group,
                              namespace=namespace,
                              type=resource_type,
                              name=name)
            if not is_valid_resource_id(rid):
                raise ValueError('The resource name {} is not valid.'.format(name))
            rids.add(rid)

    return rids
