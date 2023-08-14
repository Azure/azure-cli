# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.aaz import has_value, AAZStrArg, AAZListArg, AAZBoolArg
from azure.cli.core.azclierror import ValidationError
from ..aaz.latest.monitor.activity_log.alert import Create as _ActivityLogAlertCreate, \
    Update as _ActivityLogAlertUpdate

def _get_alert_settings_for_alert(cmd, resource_group_name, activity_log_alert_name, throw_if_missing=True):
    from azure.core.exceptions import HttpResponseError
    from ..aaz.latest.monitor.activity_log.alert import Show as ActivityLogAlertGet
    try:
        return ActivityLogAlertGet(cli_ctx=cmd.cli_ctx)(command_args={
            "resource_group": resource_group_name,
            "activity_log_alert_name": activity_log_alert_name
        })
    except HttpResponseError as ex:
        if ex.status_code == 404:
            if throw_if_missing:
                raise ValidationError('Can\'t find activity log alert {} in resource group {}.'.format(activity_log_alert_name,
                                                                                                resource_group_name))
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
    try:
        expression = args.condition.to_serialized_data()
        if expression is None:
            return
    except AttributeError:
        return

    error = 'incorrect usage: --condition requires an expression in the form of FIELD=VALUE[ and FIELD=VALUE...]'
    print(args.condition)
    if not expression:
        raise ValidationError(error)
    conditions = dict(_normalize_condition_for_alert(expression[i]) for i in range(0, len(expression), 1))
    setattr(args, 'all_of', list(conditions.values()))
    return
    if len(expression) == 1:
        expression = [each.strip() for each in expression[0].split(' ')]
    elif isinstance(expression, list):
        expression = [each.strip() for each in expression]
    else:
        raise ValidationError(error)

    if not expression or not len(expression) % 2:
        raise ValidationError(error)

    # This is a temporary approach built on the assumption that there is only AND operators. Eventually, a proper
    # YACC will be created to parse complex condition expression.

    # Ensure all the string at even options are AND operator
    operators = [expression[i] for i in range(1, len(expression), 2)]
    if any(op != 'and' for op in operators):
        raise ValidationError(error)

    # Pick the strings at odd position and convert them into condition leaf.
    conditions = dict(_normalize_condition_for_alert(expression[i]) for i in range(0, len(expression), 2))
    setattr(args, 'all_of', list(conditions.values()))


def process_webhook_properties(args):
    if not isinstance(args.webhook_properties_list, list):
        return

    result = {}
    for each in args.webhook_properties_list:
        if has_value(each):
            if '=' in each.to_serialized_data():
                key, value = each.to_serialized_data().split('=', 1)
            else:
                key, value = each, ''
            result[key] = value

    return result


class ActivityLogAlertCreate(_ActivityLogAlertCreate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.enabled._registered = False
        args_schema.location._registered = False
        args_schema.all_of._registered = False
        args_schema.action_groups._registered = False
        args_schema.disable = AAZBoolArg(
            options=["--disable"],
            help="Disable the activity log alert rule after it is created.",
        )
        args_schema.condition = AAZListArg(
            options=["--condition", "-c"],
            help="The condition that will cause the alert rule to activate. "
                 "The format is FIELD=VALUE[ and FIELD=VALUE...]",
        )
        args_schema.condition.Element = AAZStrArg()

        args_schema.action_group_id = AAZListArg(
            options=["--action-group", "-a"],
            help="Add an action group. Accepts space-separated action group identifiers. "
                 "The identifier can be the action group's name or its resource ID.",
        )
        args_schema.action_group_id.Element = AAZStrArg()

        args_schema.webhook_properties_list = AAZListArg(
            options=['--webhook-properties', '-w'],
            help="Space-separated webhook properties in 'key[=value]' format. "
                 "These properties are associated with the action groups added in this command.",
        )
        args_schema.webhook_properties_list.Element = AAZStrArg()

        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        process_condition_parameter_for_alert(args)
        webhook_properties = process_webhook_properties(args)
        if not has_value(args.scopes):
            from msrestazure.tools import resource_id
            from azure.cli.core.commands.client_factory import get_subscription_id
            args.scopes = [resource_id(subscription=get_subscription_id(self.cli_ctx),
                                       resource_group=self.resource_group)]
        if _get_alert_settings_for_alert(self, args.resource_group, args.activity_log_alert_name,
                                         throw_if_missing=False):
            raise ValidationError(
                'The activity log alert {} already exists in resource group {}.'.format(args.activity_log_alert_name,
                                                                                        args.resource_group))
        if not has_value(args.all_off):
            args.all_off = [{
                "field": "category",
                "equals": "ServiceHealth",
            }]
        # Add action groups
        action_group_rids = _normalize_names(self.cli_ctx, args.action_group_id.to_serialized_data(),
                                             args.resource_group, 'microsoft.insights', 'actionGroups')

        args.action_groups = []
        for i in action_group_rids:
            args.action_groups.append({
                "action_group_id": i,
                "webhook_properties_raw": webhook_properties
            })
        if has_value(args.disable):
            args.enabled = not args.disable


class ActivityLogAlertUpdate(_ActivityLogAlertUpdate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.enabled._registered = False
        args_schema.location._registered = False
        args_schema.all_of._registered = False
        args_schema.action_groups._registered = False
        args_schema.condition = AAZListArg(
            options=["--condition", "-c"],
            help="The condition that will cause the alert rule to activate. "
                 "The format is FIELD=VALUE[ and FIELD=VALUE...]",
        )
        args_schema.condition.Element = AAZStrArg()
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        process_condition_parameter_for_alert(args)


class ActivityLogAlertActionGroupAdd(_ActivityLogAlertUpdate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.action_groups._registered = False
        args_schema.all_of._registered = False
        args_schema.description._registered = False
        args_schema.enabled._registered = False
        args_schema.scopes._registered = False
        args_schema.tags._registered = False

        args_schema.action_group_ids = AAZListArg(
            options=["--action-group", "-a"],
            help="The names or the resource ids of the action groups to be added.",
        )
        args_schema.action_group_ids.Element = AAZStrArg()

        args_schema.webhook_properties_list = AAZListArg(
            options=['--webhook-properties', '-w'],
            help="Space-separated webhook properties in 'key[=value]' format. "
                 "These properties are associated with the action groups added in this command.",
        )
        args_schema.webhook_properties_list.Element = AAZStrArg()

        args_schema.reset = AAZBoolArg(
            options=["--reset"],
            help="Remove all the existing action groups before add new conditions.",
            default=True
        )
        args_schema.strict = AAZStrArg(
            options=["--strict"],
            help="Fails the command if an action group to be added will change existing webhook properties.",
        )
        return args_schema

    def pre_instance_create(self):
        args = self.ctx.args
        instance = self.ctx.vars.instance
        webhook_properties = process_webhook_properties(args)

        # normalize the action group ids
        rids = _normalize_names(self.cli_ctx, args.action_group_ids.to_serialized_data(), args.resource_group,
                                'microsoft.insights', 'actionGroups')
        action_groups = []
        if has_value(args.reset) and args.reset:
            for rid in rids:
                action_groups.append({
                    "action_group_id": rid,
                    "webhook_properties_raw": webhook_properties
                })
        else:
            action_groups = dict((each.action_group_id, each) for each in instance.properties.actions.action_groups)
            for rid in rids:
                if rid in action_groups and webhook_properties != action_groups[rid].webhook_properties \
                        and args.strict:
                    raise ValueError(
                        'Fails to override webhook properties of action group {} in strict mode.'.format(rid))

                action_groups[rid] = {
                    "action_group_id": rid,
                    "webhook_properties_raw": webhook_properties
                }
            action_groups = list(action_groups.values())
        instance.properties.actions.action_groups = action_groups


class ActivityLogAlertActionGroupRemove(_ActivityLogAlertUpdate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.action_group_index._registered = False
        args_schema.action_group_id._registered = False
        args_schema.webhook_properties_raw._registered = False

        args_schema.action_group_ids = AAZListArg(
            options=["--action-group", "-a"],
            help="The names or the resource ids of the action groups to be added.",
        )
        args_schema.action_group_ids.Element = AAZStrArg()
        return args_schema

    def pre_instance_create(self):
        args = self.ctx.args
        instance = self.ctx.vars.instance

        if len(args.action_group_ids) == 1 and args.action_group_ids[0] == '*':
            instance.properties.actions.action_groups = []
        else:
            # normalize the action group ids
            rids = _normalize_names(self.cli_ctx, args.action_group_ids.to_serialized_data(), args.resource_group,
                                    'microsoft.insights','actionGroups')
            action_groups = [each for each in instance.properties.actions.action_groups if each.action_group_id not in rids]
            instance.properties.actions.action_groups = action_groups


class ActivityLogAlertScopeAdd(_ActivityLogAlertUpdate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.enabled._registered = False
        args_schema.all_of._registered = False
        args_schema.action_groups._registered = False
        args_schema.tags._registered = False
        args_schema.description._registered = False
        args_schema.reset = AAZBoolArg(
            options=["--reset"],
            help="Remove all the existing action groups before add new conditions.",
            default=True
        )
        return args_schema

    def pre_instance_create(self):
        args = self.ctx.args
        instance = self.ctx.vars.instance
        new_scopes = set() if args.reset else set(instance.properties.scopes)
        for scope in args.scopes.to_serialized_data():
            new_scopes.add(scope)

        instance.properties.scopes = list(new_scopes)


class ActivityLogAlertScopeRemove(_ActivityLogAlertUpdate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.enabled._registered = False
        args_schema.all_of._registered = False
        args_schema.action_groups._registered = False
        args_schema.tags._registered = False
        args_schema.description._registered = False
        return args_schema

    def pre_instance_create(self):
        args = self.ctx.args
        instance = self.ctx.vars.instance
        new_scopes = set(instance.properties.scopes)
        for scope in args.scopes.to_serialized_data():
            try:
                new_scopes.remove(scope)
            except KeyError:
                pass

        instance.properties.scopes = list(new_scopes)


def process_condition_parameter(namespace):
    from azure.mgmt.monitor.models import AlertRuleAllOfCondition
    from knack.util import CLIError

    try:
        expression = namespace.condition
        if expression is None:
            return
    except AttributeError:
        return

    error = 'incorrect usage: --condition requires an expression in the form of FIELD=VALUE[ and FIELD=VALUE...]'

    if not expression:
        raise CLIError(error)

    if len(expression) == 1:
        expression = [each.strip() for each in expression[0].split(' ')]
    elif isinstance(expression, list):
        expression = [each.strip() for each in expression]
    else:
        raise CLIError(error)

    if not expression or not len(expression) % 2:
        raise CLIError(error)

    # This is a temporary approach built on the assumption that there is only AND operators. Eventually, a proper
    # YACC will be created to parse complex condition expression.

    # Ensure all the string at even options are AND operator
    operators = [expression[i] for i in range(1, len(expression), 2)]
    if any(op != 'and' for op in operators):
        raise CLIError(error)

    # Pick the strings at odd position and convert them into condition leaf.
    conditions = dict(_normalize_condition(expression[i]) for i in range(0, len(expression), 2))
    setattr(namespace, 'condition', AlertRuleAllOfCondition(all_of=list(conditions.values())))


def list_activity_logs_alert(client, resource_group_name=None):
    if resource_group_name:
        return client.list_by_resource_group(resource_group_name)

    return client.list_by_subscription_id()


def create(cmd, client, resource_group_name, activity_log_alert_name, scopes=None, condition=None,
           action_groups=frozenset(), tags=None, disable=False, description=None, webhook_properties=None):
    from msrestazure.tools import resource_id
    from azure.mgmt.monitor.models import (ActivityLogAlertResource, AlertRuleAllOfCondition,
                                           AlertRuleLeafCondition, ActionList)
    from azure.mgmt.monitor.models import ActionGroup
    from azure.cli.core.commands.client_factory import get_subscription_id
    from knack.util import CLIError

    if not scopes:
        scopes = [resource_id(subscription=get_subscription_id(cmd.cli_ctx), resource_group=resource_group_name)]

    if _get_alert_settings(client, resource_group_name, activity_log_alert_name, throw_if_missing=False):
        raise CLIError('The activity log alert {} already exists in resource group {}.'.format(activity_log_alert_name,
                                                                                               resource_group_name))

    # Add alert conditions
    condition = condition or AlertRuleAllOfCondition(
        all_of=[AlertRuleLeafCondition(field='category', equals='ServiceHealth')])

    # Add action groups
    action_group_rids = _normalize_names(cmd.cli_ctx, action_groups, resource_group_name, 'microsoft.insights',
                                         'actionGroups')
    action_groups = [ActionGroup(action_group_id=i, webhook_properties=webhook_properties) for i in action_group_rids]
    alert_actions = ActionList(action_groups=action_groups)

    settings = ActivityLogAlertResource(location='global', scopes=scopes, condition=condition,
                                        actions=alert_actions, enabled=not disable, description=description, tags=tags)

    return client.create_or_update(resource_group_name=resource_group_name,
                                   activity_log_alert_name=activity_log_alert_name, activity_log_alert=settings)


def add_scope(client, resource_group_name, activity_log_alert_name, scopes, reset=False):
    settings = _get_alert_settings(client, resource_group_name, activity_log_alert_name)

    new_scopes = set() if reset else set(settings.scopes)
    for scope in scopes:
        new_scopes.add(scope)

    settings.scopes = list(new_scopes)
    return client.create_or_update(resource_group_name=resource_group_name,
                                   activity_log_alert_name=activity_log_alert_name,
                                   activity_log_alert=settings)


def remove_scope(client, resource_group_name, activity_log_alert_name, scopes):
    settings = _get_alert_settings(client, resource_group_name, activity_log_alert_name)

    new_scopes = set(settings.scopes)
    for scope in scopes:
        try:
            new_scopes.remove(scope)
        except KeyError:
            pass

    settings.scopes = list(new_scopes)
    return client.create_or_update(resource_group_name=resource_group_name,
                                   activity_log_alert_name=activity_log_alert_name,
                                   activity_log_alert=settings)


def add_action_group(cmd, client, resource_group_name, activity_log_alert_name, action_group_ids, reset=False,
                     webhook_properties=None, strict=False):
    from azure.mgmt.monitor.models import ActionGroup

    settings = _get_alert_settings(client, resource_group_name, activity_log_alert_name)

    # normalize the action group ids
    rids = _normalize_names(cmd.cli_ctx, action_group_ids, resource_group_name, 'microsoft.insights', 'actionGroups')

    if reset:
        action_groups = [ActionGroup(action_group_id=rid, webhook_properties=webhook_properties) for rid in rids]
    else:
        action_groups = dict((each.action_group_id, each) for each in settings.actions.action_groups)

        for rid in rids:
            if rid in action_groups and webhook_properties != action_groups[rid].webhook_properties and strict:
                raise ValueError('Fails to override webhook properties of action group {} in strict mode.'.format(rid))

            action_groups[rid] = ActionGroup(action_group_id=rid, webhook_properties=webhook_properties)
        action_groups = list(action_groups.values())

    settings.actions.action_groups = action_groups
    return client.create_or_update(resource_group_name=resource_group_name,
                                   activity_log_alert_name=activity_log_alert_name,
                                   activity_log_alert=settings)


def remove_action_group(cmd, client, resource_group_name, activity_log_alert_name, action_group_ids):
    settings = _get_alert_settings(client, resource_group_name, activity_log_alert_name)

    if len(action_group_ids) == 1 and action_group_ids[0] == '*':
        settings.actions.action_groups = []
    else:
        # normalize the action group ids
        rids = _normalize_names(cmd.cli_ctx, action_group_ids, resource_group_name, 'microsoft.insights',
                                'actionGroups')
        action_groups = [each for each in settings.actions.action_groups if each.action_group_id not in rids]
        settings.actions.action_groups = action_groups

    return client.create_or_update(resource_group_name=resource_group_name,
                                   activity_log_alert_name=activity_log_alert_name,
                                   activity_log_alert=settings)


def update(instance, condition=None, enabled=None, tags=None, description=None):
    if tags:
        instance.tags = tags

    if description:
        instance.description = description

    if enabled is not None:
        instance.enabled = enabled

    if condition is not None:
        instance.condition = condition

    return instance


# pylint: disable=inconsistent-return-statements
def _normalize_condition(condition_instance):
    from azure.mgmt.monitor.models import AlertRuleLeafCondition

    if isinstance(condition_instance, str):
        try:
            field, value = condition_instance.split('=')
            return '{}={}'.format(field.lower(), value), AlertRuleLeafCondition(field=field, equals=value)
        except ValueError:
            # too many values to unpack or not enough values to unpack
            raise ValueError('Condition "{}" does not follow format FIELD=VALUE'.format(condition_instance))
    elif isinstance(condition_instance, AlertRuleLeafCondition):
        return '{}={}'.format(condition_instance.field.lower(), condition_instance.equals), condition_instance


def _normalize_names(cli_ctx, resource_names, resource_group, namespace, resource_type):
    """Normalize a group of resource names. Returns a set of resource ids. Throws if any of the name can't be correctly
    converted to a resource id."""
    from msrestazure.tools import is_valid_resource_id, resource_id
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


def _get_alert_settings(client, resource_group_name, activity_log_alert_name, throw_if_missing=True):
    from azure.core.exceptions import HttpResponseError

    try:
        return client.get(resource_group_name=resource_group_name, activity_log_alert_name=activity_log_alert_name)
    except HttpResponseError as ex:
        from knack.util import CLIError
        if ex.status_code == 404:
            if throw_if_missing:
                raise CLIError('Can\'t find activity log alert {} in resource group {}.'.format(activity_log_alert_name,
                                                                                                resource_group_name))
            return None
        raise CLIError(ex.message)
