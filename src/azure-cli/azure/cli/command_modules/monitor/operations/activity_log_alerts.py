# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=protected-access, line-too-long
from azure.cli.core.aaz import has_value, AAZStrArg, AAZListArg, AAZBoolArg, register_command, \
    AAZResourceIdArg, AAZResourceIdArgFormat
from azure.cli.command_modules.monitor.actions import AAZCustomListArg
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


class ActivityLogAlertCreate(_ActivityLogAlertCreate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.enabled._registered = False
        args_schema.location._registered = False
        args_schema.action_groups._registered = False
        args_schema.scopes._registered = False
        args_schema.scope_ui = AAZListArg(
            options=["--scope", "-s"],
            help="A list of strings that will be used as prefixes." + '''
        The alert rule will only apply to activity logs with resourceIDs that fall under one of
        these prefixes. If not provided, the subscriptionId will be used.
        ''',
        )
        args_schema.scope_ui.Element = AAZStrArg()

        args_schema.disable = AAZBoolArg(
            options=["--disable"],
            help="Disable the activity log alert rule after it is created.",
            default=False,
        )
        args_schema.condition = AAZCustomListArg(
            options=["--condition", "-c"],
            help="The condition that will cause the alert rule to activate. "
                 "The format is FIELD=VALUE[ and FIELD=VALUE...]" + '''
        The possible values for the field are 'resourceId', 'category', 'caller',
        'level', 'operationName', 'resourceGroup', 'resourceProvider', 'status',
        'subStatus', 'resourceType', or anything beginning with 'properties'.
        '''
        )
        args_schema.condition.Element = AAZStrArg()

        args_schema.action_group_ids = AAZListArg(
            options=["--action-group", "-a"],
            help="Add an action group. Accepts space-separated action group identifiers. "
                 "The identifier can be the action group's name or its resource ID.",
        )
        args_schema.action_group_ids.Element = AAZResourceIdArg(
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/microsoft.insights/actionGroups/{}",
            )
        )

        args_schema.webhook_properties_list = AAZCustomListArg(
            options=['--webhook-properties', '-w'],
            help="Space-separated webhook properties in 'key[=value]' format. "
                 "These properties are associated with the action groups added in this command." + '''
        For any webhook receiver in these action group, this data is appended to the webhook
        payload. To attach different webhook properties to different action groups, add the
        action groups in separate update-action commands.
        '''
        )
        args_schema.webhook_properties_list.Element = AAZStrArg()

        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        args.location = "Global"
        process_condition_parameter_for_alert(args)
        webhook_properties = process_webhook_properties(args)
        if not has_value(args.scope_ui):
            from azure.mgmt.core.tools import resource_id
            from azure.cli.core.commands.client_factory import get_subscription_id
            # args.scopes = [resource_id(subscription=get_subscription_id(self.cli_ctx),
            #                            resource_group=args.resource_group)]
            # service check
            args.scopes = [resource_id(subscription=get_subscription_id(self.cli_ctx))]
        else:
            args.scopes = args.scope_ui.to_serialized_data()
        if _get_alert_settings_for_alert(self, args.resource_group, args.activity_log_alert_name,
                                         throw_if_missing=False):
            raise ValidationError(
                'The activity log alert {} already exists in resource group {}.'.format(args.activity_log_alert_name,
                                                                                        args.resource_group))
        if not has_value(args.all_of):
            args.all_of.append({
                "field": "category",
                "equals": "ServiceHealth",
            })
        else:
            current_all_of = args.all_of.to_serialized_data()
            category_found = False
            for item in current_all_of:
                if item.get("field", None) == "category":
                    category_found = True
                    break
            if not category_found:
                args.all_of.append({
                    "field": "category",
                    "equals": "ServiceHealth",
                })
        # Add action groups
        action_group_rids = set()
        if has_value(args.action_group_ids):
            action_group_rids = set(args.action_group_ids.to_serialized_data())
        args.action_groups = []
        for i in action_group_rids:
            args.action_groups.append({
                "action_group_id": i,
                "webhook_properties": webhook_properties
            })
        if has_value(args.disable):
            args.enabled = not args.disable


class ActivityLogAlertUpdate(_ActivityLogAlertUpdate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.action_groups._registered = False
        args_schema.scopes._registered = False
        args_schema.condition = AAZCustomListArg(
            options=["--condition", "-c"],
            help="The condition that will cause the alert rule to activate. "
                 "The format is FIELD=VALUE[ and FIELD=VALUE...]" + '''
        The possible values for the field are 'resourceId', 'category', 'caller',
        'level', 'operationName', 'resourceGroup', 'resourceProvider', 'status',
        'subStatus', 'resourceType', or anything beginning with 'properties'.
        '''
        )
        args_schema.condition.Element = AAZStrArg()
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        process_condition_parameter_for_alert(args)
        if not has_value(args.all_of):
            args.all_of.append({
                "field": "category",
                "equals": "ServiceHealth",
            })
        else:
            current_all_of = args.all_of.to_serialized_data()
            category_found = False
            for item in current_all_of:
                if item.get("field", None) == "category":
                    category_found = True
                    break
            if not category_found:
                args.all_of.append({
                    "field": "category",
                    "equals": "ServiceHealth",
                })


@register_command("monitor activity-log alert action-group add")
class ActivityLogAlertActionGroupAdd(_ActivityLogAlertUpdate):
    """Add action groups to this activity log alert rule. It can also be used to overwrite existing webhook properties of particular action groups.

    :example: Add an action group and specify webhook properties.
        az monitor activity-log alert action-group add -n AlertName -g ResourceGroup \\
          --action /subscriptions/{SubID}/resourceGroups/{ResourceGroup}/providers/microsoft.insight
        s/actionGroups/{ActionGroup} \\
          --webhook-properties usage=test owner=jane

    :example: Overwite an existing action group's webhook properties.
        az monitor activity-log alert action-group add -n AlertName -g ResourceGroup \\
          -a /subscriptions/{SubID}/resourceGroups/{ResourceGroup}/providers/microsoft.insights/acti
        onGroups/{ActionGroup} \\
          --webhook-properties usage=test owner=john

    :example: Remove webhook properties from an existing action group.
        az monitor activity-log alert action-group add -n AlertName -g ResourceGroup \\
          -a /subscriptions/{SubID}/resourceGroups/{ResourceGroup}/providers/microsoft.insights/acti
        onGroups/{ActionGroup}

    :example: Add new action groups but prevent the command from accidently overwrite existing webhook properties
        az monitor activity-log alert action-group add -n AlertName -g ResourceGroup --strict \\
          --action-group ResourceIDList
    """

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
            required=True
        )
        args_schema.action_group_ids.Element = AAZResourceIdArg(
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/microsoft.insights/actionGroups/{}",
            )
        )

        args_schema.webhook_properties_list = AAZCustomListArg(
            options=['--webhook-properties', '-w'],
            help="Space-separated webhook properties in 'key[=value]' format. "
                 "These properties are associated with the action groups added in this command." + '''
          For any webhook receiver in these action group, these data are appended to the webhook
          payload. To attach different webhook properties to different action groups, add the
          action groups in separate update-action commands.
          '''
        )
        args_schema.webhook_properties_list.Element = AAZStrArg()

        args_schema.reset = AAZBoolArg(
            options=["--reset"],
            help="Remove all the existing action groups before add new conditions.",
            default=False
        )
        args_schema.strict = AAZBoolArg(
            options=["--strict"],
            help="Fails the command if an action group to be added will change existing webhook properties.",
            default=False,
        )
        return args_schema

    def pre_instance_update(self, instance):
        args = self.ctx.args
        webhook_properties = process_webhook_properties(args)

        rids = args.action_group_ids.to_serialized_data()

        if has_value(args.reset) and args.reset:
            action_groups = []
            for rid in rids:
                action_groups.append({
                    "action_group_id": rid,
                    "webhook_properties": webhook_properties
                })
            instance.properties.actions.action_groups = action_groups
        else:
            action_groups_map = {}
            for item in instance.properties.actions.action_groups:
                ac_id = item.actionGroupId.to_serialized_data()
                # service returned action group id can be uppercase
                action_groups_map[ac_id.lower()] = {
                    "action_group_id": ac_id,
                    "webhook_properties": dict(item.webhookProperties)
                }

            for rid in rids:
                if args.strict:
                    for key, item in action_groups_map.items():
                        if key.lower() == rid.lower() and webhook_properties != item["webhook_properties"]:
                            raise ValueError(
                                'Fails to override webhook properties of action group {} in strict mode.'.format(rid))

                action_groups_map[rid.lower()] = {
                    "action_group_id": rid,
                    "webhook_properties": webhook_properties
                }

            action_groups = list(action_groups_map.values())
            instance.properties.actions.action_groups = action_groups


@register_command("monitor activity-log alert action-group remove")
class ActivityLogAlertActionGroupRemove(_ActivityLogAlertUpdate):
    """Remove action groups from this activity log alert rule.
    """

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
            required=True,
            help="The names or the resource ids of the action groups to be added.",
        )
        args_schema.action_group_ids.Element = AAZStrArg()
        return args_schema

    def pre_instance_update(self, instance):
        args = self.ctx.args
        action_group_ids = args.action_group_ids.to_serialized_data()
        if len(action_group_ids) == 1 and action_group_ids[0] == '*':
            instance.properties.actions.actionGroups = []
        else:
            # normalize the action group ids
            rids = _normalize_names(self.cli_ctx, args.action_group_ids.to_serialized_data(), args.resource_group,
                                    'microsoft.insights', 'actionGroups')
            action_groups = []
            for item in instance.properties.actions.actionGroups:
                ac_id = item.actionGroupId.to_serialized_data()
                found = False
                for rid in rids:
                    if ac_id.lower() == rid.lower():  # service returned action group id can be uppercase
                        found = True
                        break
                if not found:
                    action_groups.append(item)
            instance.properties.actions.actionGroups = action_groups


@register_command("monitor activity-log alert scope add")
class ActivityLogAlertScopeAdd(_ActivityLogAlertUpdate):
    """Add scopes to this activity log alert rule.

    :example: Add scopes to this activity log alert rule.
        az monitor activity-log alert scope add --name MyActivityLogAlerts --resource-group
        MyResourceGroup --scope /subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
        /subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myRG
        /subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-
        xxxxxxxxxxxx/resourceGroups/myRG/Microsoft.KeyVault/vaults/mykey
    """

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.enabled._registered = False
        args_schema.all_of._registered = False
        args_schema.action_groups._registered = False
        args_schema.tags._registered = False
        args_schema.description._registered = False
        args_schema.scopes._registered = False
        args_schema.scope_ui = AAZListArg(
            options=["--scope", "-s"],
            required=True,
            help="List of scopes to add. Each scope could be a resource ID or a subscription ID.",
        )
        args_schema.scope_ui.Element = AAZStrArg()

        args_schema.reset = AAZBoolArg(
            options=["--reset"],
            help="Remove all the existing action groups before add new conditions.",
            default=False
        )
        return args_schema

    def pre_instance_update(self, instance):
        args = self.ctx.args
        new_scopes = set() if args.reset else set(instance.properties.scopes.to_serialized_data())
        for scope in args.scope_ui.to_serialized_data():
            new_scopes.add(scope)

        args.scopes = list(new_scopes)


@register_command("monitor activity-log alert scope remove")
class ActivityLogAlertScopeRemove(_ActivityLogAlertUpdate):
    """Removes scopes from this activity log alert rule.
    """

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.enabled._registered = False
        args_schema.all_of._registered = False
        args_schema.action_groups._registered = False
        args_schema.tags._registered = False
        args_schema.description._registered = False
        args_schema.scopes._registered = False
        args_schema.scope_ui = AAZListArg(
            options=["--scope", "-s"],
            required=True,
            help="The scopes to remove.",
        )
        args_schema.scope_ui.Element = AAZStrArg()
        return args_schema

    def pre_instance_update(self, instance):
        args = self.ctx.args
        new_scopes = set(instance.properties.scopes.to_serialized_data())
        for scope in args.scope_ui.to_serialized_data():
            try:
                new_scopes.remove(scope)
            except KeyError:
                pass
        args.scopes = list(new_scopes)


def _normalize_names(cli_ctx, resource_names, resource_group, namespace, resource_type):
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
