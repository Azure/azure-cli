# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=protected-access, line-too-long

from azure.cli.core.aaz import has_value, AAZStrArg, AAZListArg, AAZBoolArg, register_command, \
    AAZResourceIdArg, AAZResourceIdArgFormat
from azure.cli.command_modules.monitor.actions import AAZCustomListArg
from azure.cli.command_modules.monitor.aaz.latest.monitor.activity_log.alert._update \
    import Update as _ActivityLogAlertUpdate
from azure.cli.command_modules.monitor.operations.activity_log_alerts import process_webhook_properties


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
            instance.properties.actions.action_groups = list(action_groups_map.values())
