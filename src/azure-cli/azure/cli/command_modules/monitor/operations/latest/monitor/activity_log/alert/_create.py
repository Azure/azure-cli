# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=protected-access, line-too-long

from azure.cli.core.aaz import has_value, AAZStrArg, AAZListArg, AAZBoolArg, \
    AAZResourceIdArg, AAZResourceIdArgFormat
from azure.cli.command_modules.monitor.actions import AAZCustomListArg
from azure.cli.command_modules.monitor.aaz.latest.monitor.activity_log.alert._create \
    import Create as _ActivityLogAlertCreate
from azure.cli.command_modules.monitor.operations.activity_log_alerts import (
    _get_alert_settings_for_alert,
    process_condition_parameter_for_alert,
    process_webhook_properties,
)
from azure.cli.core.azclierror import ValidationError


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
